"""Immutable review information and explicit, scope-locked activation."""

from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.http import APIError, not_found
from app.core.pagination import paginate_list
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.cases.services import record_correction_received
from app.modules.institutions.models import Institution, Programme
from app.modules.submissions.models import (
    ProcessingStatus,
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionReview,
    SubmissionScope,
)
from app.modules.submissions.schemas import (
    ActivationRequest,
    ActivationResponse,
    OmittedRecord,
    ReviewResponse,
)
from app.modules.submissions.services import batch_rows, scoped_batch, snapshot_counts
from app.modules.validation.models import ValidationRun
from app.modules.validation.rules import CATEGORIES, STATUSES, structural_findings
from app.modules.validation.services import (
    findings_for,
    require_run,
    run_response,
    structurally_compatible,
)

REVIEW_POLICY_VERSION = "SNAPSHOT-REVIEW-DEMO-v1"


def get_activation_session(request: Request) -> Iterator[Session]:
    # A distinct dependency gives activation a fresh READ COMMITTED transaction,
    # rather than reusing authentication's identity map or repeatable-read view.
    for session in get_session(request):
        session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        yield session


def administrator(session: Session, actor_id: UUID) -> User:
    user = session.get(User, actor_id, populate_existing=True)
    if user is None or not user.active:
        raise APIError(401, "NOT_AUTHENTICATED", "Not authenticated")
    if user.role != Role.INSTITUTION_ADMIN:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")
    institution = session.get(Institution, user.institution_id, populate_existing=True)
    if institution is None or not institution.active:
        raise APIError(401, "NOT_AUTHENTICATED", "Not authenticated")
    return user


def eligibility(
    session: Session, batch: SubmissionBatch, run: ValidationRun | None
) -> dict[str, Any]:
    reasons: list[str] = []
    institution = session.get(Institution, batch.institution_id, populate_existing=True)
    programme = session.get(Programme, batch.programme_id, populate_existing=True)
    if (
        institution is None
        or not institution.active
        or programme is None
        or not programme.active
    ):
        reasons.append("INACTIVE_SCOPE")
    if batch.status != ProcessingStatus.COMPLETED or batch.completed_at is None:
        reasons.append("SUBMISSION_NOT_PROCESSED")
    if batch.activated_at is not None or batch.activation_review_id is not None:
        reasons.append("ALREADY_ACTIVATED")
    rows = batch_rows(session, batch.id)
    if len(rows) != batch.row_count or not rows:
        reasons.append("SUBMISSION_NOT_PROCESSED")
    blockers: list[str] = []
    if run is None:
        reasons.append("VALIDATION_NOT_RUN")
    elif programme is None or not structurally_compatible(run, batch, programme):
        reasons.append("REVALIDATION_REQUIRED")
    else:
        if run.batch_id != batch.id or run.summary_json.get("reported_records") != len(
            rows
        ):
            reasons.append("REVALIDATION_REQUIRED")
        blockers = sorted(
            {
                finding.rule_code
                for finding in findings_for(session, run)
                if finding.classification == "ACTIVATION_BLOCKING"
            }
        )
        # Reuse the engine's current structural rules, even if a developer forgot
        # to bump a version. No peer matching or regulatory re-evaluation here.
        current = structural_findings(rows, batch, programme.code)
        blockers = sorted(set(blockers) | {finding.code for finding in current})
        if blockers:
            reasons.append("STRUCTURAL_BLOCKERS")
    return {
        "eligible": not reasons,
        "validation_run_id": str(run.id) if run else None,
        "blocking_reasons": sorted(set(reasons)),
        "structural_blocking_rules": blockers,
    }


def comparison(
    current: list[StudentRecordVersion], candidate: list[StudentRecordVersion]
) -> dict[str, Any]:
    before = snapshot_counts(current)
    after = snapshot_counts(candidate)
    result: dict[str, Any] = {
        "current_counts": before if current else None,
        "candidate_counts": after,
        "count_basis": "DEMO_DECLARED_ROWS",
        "has_current_snapshot": bool(current),
        "delta_counts": {
            "declared_records": after["declared_records"] - before["declared_records"],
            "demo_active_records": after["demo_active_records"]
            - before["demo_active_records"],
            "categories": {
                category: {
                    key: after["categories"][category][key]
                    - before["categories"][category][key]
                    for key in ("declared_records", "demo_active_records")
                }
                for category in CATEGORIES
            },
            "statuses": {
                status: after["statuses"][status] - before["statuses"][status]
                for status in (*STATUSES, "UNSUPPORTED")
            },
        },
        "omission_meaning": (
            "Absent from replacement declaration; not inferred withdrawal or transfer"
        ),
    }
    before_ids = {row.college_student_id: row for row in current}
    after_ids = {row.college_student_id: row for row in candidate}
    ambiguous = (
        len(before_ids) != len(current)
        or len(after_ids) != len(candidate)
        or "" in before_ids
        or "" in after_ids
    )
    if ambiguous:
        result.update(
            {
                "identifier_comparison": "UNAVAILABLE_AMBIGUOUS_IDENTIFIERS",
                "added_record_count": None,
                "retained_record_count": None,
                "omitted_record_count": None,
                "previously_active_omitted_record_count": None,
                "status_transitions": None,
                "category_transitions": None,
                "_omitted_record_ids": None,
            }
        )
        return result
    omitted = [row for row in current if row.college_student_id not in after_ids]
    retained = [key for key in after_ids if key in before_ids]
    status_transitions: Counter[tuple[str, str]] = Counter()
    category_transitions: Counter[tuple[str, str]] = Counter()
    for key in retained:
        old, new = before_ids[key], after_ids[key]
        if old.enrollment_status != new.enrollment_status:
            status_transitions[
                (
                    old.enrollment_status
                    if old.enrollment_status in STATUSES
                    else "UNSUPPORTED",
                    new.enrollment_status
                    if new.enrollment_status in STATUSES
                    else "UNSUPPORTED",
                )
            ] += 1
        if old.admission_category != new.admission_category:
            category_transitions[
                (
                    old.admission_category
                    if old.admission_category in CATEGORIES
                    else "UNSUPPORTED",
                    new.admission_category
                    if new.admission_category in CATEGORIES
                    else "UNSUPPORTED",
                )
            ] += 1
    result.update(
        {
            "identifier_comparison": "COMPLETE",
            "added_record_count": len(after_ids.keys() - before_ids.keys()),
            "retained_record_count": len(retained),
            "omitted_record_count": len(omitted),
            "previously_active_omitted_record_count": sum(
                row.enrollment_status == "ACTIVE" for row in omitted
            ),
            "status_transitions": [
                {"from": old, "to": new, "records": count}
                for (old, new), count in sorted(status_transitions.items())
            ],
            "category_transitions": [
                {"from": old, "to": new, "records": count}
                for (old, new), count in sorted(category_transitions.items())
            ],
            "_omitted_record_ids": [str(row.id) for row in omitted],
        }
    )
    return result


def scoped_review(
    session: Session, user: User, batch_id: UUID, review_id: UUID
) -> SubmissionReview:
    scoped_batch(session, user, batch_id)
    review = session.scalar(
        select(SubmissionReview).where(
            SubmissionReview.id == review_id, SubmissionReview.batch_id == batch_id
        )
    )
    if review is None:
        raise not_found()
    return review


def review_response(
    session: Session, review: SubmissionReview, *, page: int = 1, page_size: int = 20
) -> ReviewResponse:
    batch = session.get(SubmissionBatch, review.batch_id, populate_existing=True)
    scope = session.get(SubmissionScope, review.scope_id, populate_existing=True)
    assert batch is not None and scope is not None
    run = require_run(session, batch.id, review.validation_run_id)
    allowed = eligibility(session, batch, run)
    if review.review_snapshot_json["identifier_comparison"] != "COMPLETE":
        allowed = {
            **allowed,
            "eligible": False,
            "blocking_reasons": [
                *allowed["blocking_reasons"],
                "COMPARISON_UNAVAILABLE",
            ],
        }
    if review.review_policy_version != REVIEW_POLICY_VERSION:
        allowed = {
            **allowed,
            "eligible": False,
            "blocking_reasons": [*allowed["blocking_reasons"], "REVIEW_POLICY_CHANGED"],
        }
    state = "READY" if allowed["eligible"] else "BLOCKED"
    if (
        scope.revision != review.expected_scope_revision
        or scope.current_batch_id != review.expected_current_batch_id
    ):
        state = "STALE"
    if batch.activation_review_id == review.id:
        state = "CONSUMED"
    assessment = run_response(session, run)
    omitted_ids = review.review_snapshot_json.get("_omitted_record_ids")
    omitted_records = None
    pagination = None
    if omitted_ids is not None:
        window = paginate_list(omitted_ids, page, page_size)
        selected = window.data
        records = (
            {
                str(row.id): row
                for row in session.scalars(
                    select(StudentRecordVersion).where(
                        StudentRecordVersion.id.in_([UUID(value) for value in selected])
                    )
                )
            }
            if selected
            else {}
        )
        omitted_records = [
            OmittedRecord(
                record_version_id=records[value].id,
                source_row_number=records[value].source_row_number,
                college_student_id=records[value].college_student_id,
                previous_enrollment_status=records[value].enrollment_status,
                previous_admission_category=records[value].admission_category,
            )
            for value in selected
        ]
        pagination = window.pagination.model_dump()
    return ReviewResponse(
        id=review.id,
        batch_id=batch.id,
        scope_id=scope.id,
        institution_id=batch.institution_id,
        programme_id=batch.programme_id,
        academic_year=batch.academic_year,
        validation_run_id=run.id,
        reviewed_by=review.reviewed_by,
        created_at=review.created_at,
        expected_scope_revision=review.expected_scope_revision,
        expected_current_batch_id=review.expected_current_batch_id,
        review_policy_version=review.review_policy_version,
        review_state=state,
        snapshot={
            key: value
            for key, value in review.review_snapshot_json.items()
            if not key.startswith("_")
        },
        eligibility=allowed,
        assessment_now={
            "cross_current_freshness": assessment.cross_current_freshness,
            "matching_assessment": run.summary_json["matching_assessment"],
            "current_overlap_records": assessment.current_overlap_records,
            "historical_assessment": "AS_OF_RUN",
        },
        omitted_records=omitted_records,
        omission_pagination=pagination,
    )


def create_review(
    session: Session, actor_id: UUID, batch_id: UUID, run_id: UUID
) -> ReviewResponse:
    try:
        user = administrator(session, actor_id)
        batch = scoped_batch(session, user, batch_id)
        scope = session.get(SubmissionScope, batch.scope_id)
        assert scope is not None
        run = require_run(session, batch.id, run_id)
        snapshot = comparison(
            batch_rows(session, scope.current_batch_id)
            if scope.current_batch_id
            else [],
            batch_rows(session, batch.id),
        )
        findings = findings_for(session, run)
        assessment = run_response(session, run)
        initial_eligibility = eligibility(session, batch, run)
        if snapshot["identifier_comparison"] != "COMPLETE":
            initial_eligibility = {
                **initial_eligibility,
                "eligible": False,
                "blocking_reasons": [
                    *initial_eligibility["blocking_reasons"],
                    "COMPARISON_UNAVAILABLE",
                ],
            }
        snapshot.update(
            {
                "eligibility_at_review": initial_eligibility,
                "ruleset_version": run.ruleset_version,
                "ruleset_snapshot": run.ruleset_snapshot_json,
                "blocking_finding_ids": [
                    str(item.id)
                    for item in findings
                    if item.classification == "ACTIVATION_BLOCKING"
                ],
                "reviewable_finding_count": sum(
                    item.classification == "REVIEWABLE" for item in findings
                ),
                "findings_url": (
                    f"/api/v1/submissions/{batch.id}/findings?run_id={run.id}"
                ),
                "assessment_at_review": {
                    "cross_current_freshness": assessment.cross_current_freshness,
                    "matching_assessment": run.summary_json["matching_assessment"],
                    "current_overlap_records": assessment.current_overlap_records,
                },
            }
        )
        review = SubmissionReview(
            batch_id=batch.id,
            scope_id=scope.id,
            validation_run_id=run.id,
            reviewed_by=user.id,
            expected_scope_revision=scope.revision,
            expected_current_batch_id=scope.current_batch_id,
            review_policy_version=REVIEW_POLICY_VERSION,
            review_snapshot_json=snapshot,
        )
        session.add(review)
        session.flush()
        record_action(
            session,
            actor_id=user.id,
            institution_id=batch.institution_id,
            action="SUBMISSION_REVIEW_CREATED",
            entity_type="submission_reviews",
            entity_id=review.id,
        )
        result = review_response(session, review)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise


def activate(
    session: Session, actor_id: UUID, batch_id: UUID, request: ActivationRequest
) -> ActivationResponse:
    try:
        user = administrator(session, actor_id)
        batch = scoped_batch(session, user, batch_id)
        scope = session.scalar(
            select(SubmissionScope)
            .where(SubmissionScope.id == batch.scope_id)
            .with_for_update(nowait=True)
            .execution_options(populate_existing=True)
        )
        assert scope is not None
        # Refresh after acquiring the lock; another activation may have completed.
        session.refresh(batch)
        user = administrator(session, actor_id)
        review = scoped_review(session, user, batch.id, request.review_id)
        if review.reviewed_by != user.id:
            raise APIError(
                403, "REVIEW_ACTOR_MISMATCH", "Create your own review before activating"
            )
        if batch.activated_at is not None:
            raise APIError(409, "ALREADY_ACTIVATED", "Candidate was already activated")
        if (
            scope.revision != request.expected_scope_revision
            or scope.revision != review.expected_scope_revision
            or scope.current_batch_id != review.expected_current_batch_id
        ):
            raise APIError(
                409,
                "SCOPE_REVISION_CONFLICT",
                "Current snapshot changed; create a new review",
            )
        if review.review_policy_version != REVIEW_POLICY_VERSION:
            raise APIError(
                409,
                "REVIEW_POLICY_CHANGED",
                "Review policy changed; create a new review",
            )
        run = require_run(session, batch.id, review.validation_run_id)
        allowed = eligibility(session, batch, run)
        if review.review_snapshot_json["identifier_comparison"] != "COMPLETE":
            allowed = {**allowed, "eligible": False}
        if not allowed["eligible"]:
            code = (
                "REVALIDATION_REQUIRED"
                if "REVALIDATION_REQUIRED" in allowed["blocking_reasons"]
                else "CANDIDATE_INELIGIBLE"
            )
            raise APIError(
                409,
                code,
                "Candidate is ineligible; inspect validation and create a new review",
            )
        if (
            review.review_snapshot_json["omitted_record_count"]
            and not request.acknowledge_omissions
        ):
            raise APIError(
                422,
                "OMISSIONS_ACKNOWLEDGMENT_REQUIRED",
                "Explicit omission acknowledgment is required",
            )
        batch.activation_review_id = review.id
        batch.activated_at = datetime.now(UTC)
        scope.current_batch_id = batch.id
        scope.revision += 1
        record_correction_received(session, batch)
        session.flush()
        record_action(
            session,
            actor_id=user.id,
            institution_id=batch.institution_id,
            action="SUBMISSION_ACTIVATED",
            entity_type="submission_reviews",
            entity_id=review.id,
        )
        result = ActivationResponse(
            batch_id=batch.id,
            scope_id=scope.id,
            review_id=review.id,
            validation_run_id=run.id,
            previous_batch_id=review.expected_current_batch_id,
            scope_revision=scope.revision,
            activated_by=user.id,
            activated_at=batch.activated_at,
            counts=snapshot_counts(batch_rows(session, batch.id)),
        )
        session.commit()
        return result
    except DBAPIError as error:
        session.rollback()
        if getattr(error.orig, "sqlstate", None) == "55P03":
            raise APIError(
                409,
                "ACTIVATION_CONFLICT",
                "Scope is busy; retry after reviewing its revision",
            ) from None
        raise
    except Exception:
        session.rollback()
        raise
