from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from time import monotonic
from typing import Any
from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError as DriverOperationalError
from sqlalchemy import Engine, delete, event, func, select, text, update
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session
from test_validation import csv_data, fields, run_validation, upload

from app.core.config import Settings
from app.core.http import APIError
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.institutions.models import Programme
from app.modules.submissions.activation import activate, create_review
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionReview,
    SubmissionScope,
)
from app.modules.submissions.parsing import parse_csv
from app.modules.submissions.schemas import ActivationRequest, UploadContext
from app.modules.submissions.services import persist_candidate
from app.modules.validation.rules import Finding
from app.modules.validation.services import validate_candidate
from app.seed import seed_demo, seed_id

SAMPLES = Path(__file__).resolve().parents[3] / "samples"


def review(
    client: TestClient,
    identifier: str,
    headers: dict[str, str],
    run_id: str | None = None,
) -> dict[str, Any]:
    if run_id is None:
        run_id = run_validation(client, identifier, headers)["id"]
    response = client.post(
        f"/api/v1/submissions/{identifier}/reviews",
        headers=headers,
        json={"validation_run_id": run_id},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def confirmation(receipt: dict[str, Any], *, omissions: bool = True) -> dict[str, Any]:
    return {
        "review_id": receipt["id"],
        "expected_scope_revision": receipt["expected_scope_revision"],
        "confirm_complete_replacement": True,
        "acknowledge_review_warnings": True,
        "acknowledge_omissions": omissions,
    }


def activate_http(
    client: TestClient,
    identifier: str,
    receipt: dict[str, Any],
    headers: dict[str, str],
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/submissions/{identifier}/activate",
        headers=headers,
        json=confirmation(receipt),
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def summary_url(institution: str = "cedar") -> str:
    identifier = seed_id("institutions", institution)
    return f"/api/v1/institutions/{identifier}/summary?academic_year=2026-27"


def test_replacement_omissions_counts_and_history(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    initial = upload(
        client, headers, (SAMPLES / "synthetic_snapshot_initial.csv").read_bytes()
    )
    first = review(client, initial, headers)
    assert (
        first["review_state"] == "READY" and first["snapshot"]["current_counts"] is None
    )
    assert (
        client.get(summary_url(), headers=headers).json()["coverage"]["status"]
        == "NONE"
    )
    activate_http(client, initial, first, headers)
    replacement = upload(
        client, headers, (SAMPLES / "synthetic_snapshot_replacement.csv").read_bytes()
    )
    receipt = review(client, replacement, headers)
    snap = receipt["snapshot"]
    assert snap["current_counts"]["declared_records"] == 3
    assert snap["candidate_counts"]["declared_records"] == 2
    assert snap["candidate_counts"]["demo_active_records"] == 1
    assert (
        snap["omitted_record_count"]
        == snap["previously_active_omitted_record_count"]
        == 1
    )
    assert snap["delta_counts"]["declared_records"] == -1
    assert snap["delta_counts"]["demo_active_records"] == -2
    assert snap["status_transitions"] == [
        {"from": "ACTIVE", "to": "WITHDRAWN", "records": 1}
    ]
    assert snap["category_transitions"] == [
        {"from": "REGULAR", "to": "NRI", "records": 1}
    ]
    assert receipt["omitted_records"][0]["college_student_id"] == "DEMO-003"
    assert receipt["assessment_now"]["current_overlap_records"] is None
    assert "not proof" in receipt["receipt_label"]
    response = client.post(
        f"/api/v1/submissions/{replacement}/activate",
        headers=headers,
        json=confirmation(receipt, omissions=False),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "OMISSIONS_ACKNOWLEDGMENT_REQUIRED"
    result = activate_http(client, replacement, receipt, headers)
    assert result["scope_revision"] == 2 and result["previous_batch_id"] == initial
    current = client.get(summary_url(), headers=headers).json()
    assert current["totals"]["declared_records"] == 2
    assert current["totals"]["demo_active_records"] == 1
    assert current["totals"]["categories"]["NRI"]["demo_active_records"] == 1
    assert current["coverage"]["status"] == "PARTIAL"
    assert current["data"][1]["counts"] is None
    assert (
        client.get(f"/api/v1/submissions/{initial}", headers=headers).json()[
            "snapshot_state"
        ]
        == "PREVIOUS"
    )
    active = client.get(f"/api/v1/submissions/{replacement}", headers=headers).json()
    assert active["snapshot_state"] == "CURRENT"
    assert (
        active["activation_provenance"]["validation_run_id"]
        == receipt["validation_run_id"]
    )
    assert (
        client.get(
            f"/api/v1/submissions/{replacement}/reviews/{receipt['id']}",
            headers=headers,
        ).json()["review_state"]
        == "CONSUMED"
    )
    assert (
        seeded_session.scalar(select(func.count()).select_from(StudentRecordVersion))
        == 5
    )
    event_row = seeded_session.scalar(
        select(AuditEvent).where(
            AuditEvent.action == "SUBMISSION_ACTIVATED",
            AuditEvent.entity_id == UUID(receipt["id"]),
        )
    )
    assert event_row is not None and event_row.actor_id == seed_id(
        "users", "cedar_admin"
    )
    assert "DEMO-003" not in str(event_row.metadata_redacted)
    for _model, statement in (
        (
            SubmissionReview,
            update(SubmissionReview).values(review_policy_version="changed"),
        ),
        (SubmissionReview, delete(SubmissionReview)),
        (
            SubmissionBatch,
            update(SubmissionBatch)
            .where(SubmissionBatch.id == UUID(replacement))
            .values(activated_at=None, activation_review_id=None),
        ),
    ):
        with pytest.raises(DBAPIError), seeded_session.begin_nested():
            seeded_session.execute(statement)


def test_old_upload_baseline_replay_and_stale_review(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    first = upload(client, headers)
    second = upload(client, headers)
    first_receipt = review(client, first, headers)
    second_receipt = review(client, second, headers)
    activate_http(client, first, first_receipt, headers)
    for identifier, receipt in ((first, first_receipt), (second, second_receipt)):
        response = client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        )
        assert response.status_code == 409
    stale = client.get(
        f"/api/v1/submissions/{second}/reviews/{second_receipt['id']}", headers=headers
    ).json()
    assert stale["review_state"] == "STALE"
    fresh = review(client, second, headers, second_receipt["validation_run_id"])
    assert fresh["expected_scope_revision"] == 1
    assert (
        client.get(f"/api/v1/submissions/{second}", headers=headers).json()[
            "base_scope_revision"
        ]
        == 0
    )
    activate_http(client, second, fresh, headers)
    assert (
        client.get(summary_url(), headers=headers).json()["totals"]["declared_records"]
        == 1
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"college_student_id": ""},
        {"academic_year": "2025-26"},
        {"programme_code": "WRONG"},
        {"admission_category": "UNKNOWN"},
        {"enrollment_status": "UNKNOWN"},
    ],
)
def test_structural_blockers(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    changes: dict[str, str],
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers, csv_data(**changes))
    receipt = review(client, identifier, headers)
    assert receipt["review_state"] == "BLOCKED"
    assert not receipt["eligibility"]["eligible"]
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == 409
    )


def test_duplicate_local_ids_make_omissions_unknown(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    data = csv_data()
    identifier = upload(client, headers, data + data.splitlines(keepends=True)[1])
    receipt = review(client, identifier, headers)
    assert receipt["snapshot"]["omitted_record_count"] is None
    assert receipt["omitted_records"] is None
    assert (
        receipt["snapshot"]["identifier_comparison"]
        == "UNAVAILABLE_AMBIGUOUS_IDENTIFIERS"
    )
    assert not receipt["eligibility"]["eligible"]


@pytest.mark.parametrize(
    "changes",
    [
        {"student_name": ""},
        {"apaar_id": ""},
        {"apaar_id": "bad-demo"},
        {"enrollment_date": "2026-02-30"},
        {"enrollment_date": ""},
    ],
)
def test_reviewable_incomplete_records_remain_eligible(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    changes: dict[str, str],
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers, csv_data(**changes))
    receipt = review(client, identifier, headers)
    assert receipt["eligibility"]["eligible"]
    activate_http(client, identifier, receipt, headers)
    assert (
        client.get(summary_url(), headers=headers).json()["totals"][
            "demo_active_records"
        ]
        == 1
    )


def test_selected_run_requires_new_validation_and_review_when_rules_change(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    with patch(
        "app.modules.validation.services.STRUCTURAL_RULESET_VERSION", "STRUCTURE-v2"
    ):
        response = client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        )
        assert (
            response.status_code == 409
            and response.json()["error"]["code"] == "REVALIDATION_REQUIRED"
        )
        newer = run_validation(
            client, identifier, auth_headers("demo_officer"), repeat=True
        )
        # A new run alone never substitutes the receipt's explicitly selected run.
        assert (
            client.post(
                f"/api/v1/submissions/{identifier}/activate",
                headers=headers,
                json=confirmation(receipt),
            ).status_code
            == 409
        )
        replacement = review(client, identifier, headers, newer["id"])
        activate_http(client, identifier, replacement, headers)


def test_current_structural_check_cannot_be_bypassed_by_version_label(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    with patch(
        "app.modules.submissions.activation.structural_findings",
        return_value=[
            Finding(
                "NEW_BLOCKER",
                "Test structural policy",
                severity="ERROR",
                classification="ACTIVATION_BLOCKING",
            )
        ],
    ):
        assert (
            client.post(
                f"/api/v1/submissions/{identifier}/activate",
                headers=headers,
                json=confirmation(receipt),
            ).status_code
            == 409
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_scope_revision", True),
        ("expected_scope_revision", -1),
        ("confirm_complete_replacement", False),
        ("confirm_complete_replacement", 1),
        ("acknowledge_review_warnings", False),
        ("acknowledge_omissions", "true"),
        ("extra", True),
    ],
)
def test_invalid_confirmation(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    field: str,
    value: Any,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    body = {**confirmation(receipt), field: value}
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate", headers=headers, json=body
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "alias,expected",
    [("maple_admin", 404), ("demo_officer", 403), ("demo_manager", 403)],
)
def test_activation_roles_and_isolation(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    alias: str,
    expected: int,
) -> None:
    owner = auth_headers("cedar_admin")
    identifier = upload(client, owner)
    receipt = review(client, identifier, owner)
    headers = auth_headers(alias)
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/reviews",
            headers=headers,
            json={"validation_run_id": receipt["validation_run_id"]},
        ).status_code
        == expected
    )
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == expected
    )
    assert client.get(
        f"/api/v1/submissions/{identifier}/reviews/{receipt['id']}", headers=headers
    ).status_code == (200 if alias == "demo_officer" else expected)
    if alias == "demo_manager":
        aggregate = client.get(summary_url(), headers=headers)
        assert aggregate.status_code == 200
        assert (
            identifier not in aggregate.text
            and "college_student_id" not in aggregate.text
        )


def test_foreign_run_and_review_and_inactive_programme(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    first = upload(client, headers)
    second = upload(client, headers)
    receipt = review(client, first, headers)
    assert (
        client.post(
            f"/api/v1/submissions/{second}/reviews",
            headers=headers,
            json={"validation_run_id": receipt["validation_run_id"]},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/submissions/{second}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == 404
    )
    assert client.get(f"/api/v1/submissions/{second}", headers=headers).json()[
        "activation_eligibility"
    ]["blocking_reasons"] == ["VALIDATION_NOT_RUN"]
    programme = seeded_session.get(Programme, seed_id("programmes", "cedar/DEMO-COMP"))
    assert programme is not None
    programme.active = False
    seeded_session.commit()
    assert (
        client.post(
            f"/api/v1/submissions/{first}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == 409
    )


@pytest.mark.parametrize("stage", ["batch", "scope", "audit", "commit"])
def test_atomic_rollback_at_each_write(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    stage: str,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    connection = seeded_session.connection()

    def fail_after_write(*args: Any) -> None:
        statement = str(args[2]).lower()
        target = (
            "update submission_batches"
            if stage == "batch"
            else "update submission_scopes"
        )
        if statement.startswith(target):
            raise ProgrammingError("redacted", {}, Exception("secret demo payload"))

    if stage in {"batch", "scope"}:
        event.listen(connection, "after_cursor_execute", fail_after_write)
        try:
            response = client.post(
                f"/api/v1/submissions/{identifier}/activate",
                headers=headers,
                json=confirmation(receipt),
            )
        finally:
            event.remove(connection, "after_cursor_execute", fail_after_write)
    else:
        target = (
            "app.modules.submissions.activation.record_action"
            if stage == "audit"
            else "commit"
        )
        with (
            patch(
                target,
                side_effect=ProgrammingError(
                    "redacted", {}, Exception("secret demo payload")
                ),
            )
            if stage == "audit"
            else patch.object(
                seeded_session,
                target,
                side_effect=ProgrammingError(
                    "redacted", {}, Exception("secret demo payload")
                ),
            )
        ):
            response = client.post(
                f"/api/v1/submissions/{identifier}/activate",
                headers=headers,
                json=confirmation(receipt),
            )
    assert response.status_code == 500 and "secret demo payload" not in response.text
    batch = seeded_session.get(SubmissionBatch, UUID(identifier))
    scope = seeded_session.get(SubmissionScope, UUID(receipt["scope_id"]))
    assert (
        batch is not None
        and batch.activated_at is None
        and batch.activation_review_id is None
    )
    assert scope is not None and scope.current_batch_id is None and scope.revision == 0
    assert (
        seeded_session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "SUBMISSION_ACTIVATED")
        )
        == 0
    )


def prepared_reviews(
    engine: Engine, settings: Settings, *, different_scopes: bool
) -> list[tuple[UUID, ActivationRequest]]:
    with Session(engine) as session, session.begin():
        seed_demo(session, settings)
    result = []
    for index in range(2):
        with (
            engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as connection,
            Session(connection, expire_on_commit=False) as session,
        ):
            user = session.get(User, seed_id("users", "cedar_admin"))
            assert user is not None
            values = fields()
            code = "DEMO-ELEC" if different_scopes and index else "DEMO-COMP"
            values["programme_id"] = str(seed_id("programmes", f"cedar/{code}"))
            data = csv_data(programme_code=code)
            identifier = persist_candidate(
                session,
                user,
                UploadContext.model_validate(values),
                data,
                "synthetic.csv",
                parse_csv(data, settings, monotonic() + 30),
                monotonic() + 30,
            ).id
            run = validate_candidate(session, user.id, identifier, settings)
            receipt = create_review(session, user.id, identifier, run.id)
            result.append(
                (
                    identifier,
                    ActivationRequest(
                        review_id=receipt.id,
                        expected_scope_revision=receipt.expected_scope_revision,
                        confirm_complete_replacement=True,
                        acknowledge_review_warnings=True,
                        acknowledge_omissions=True,
                    ),
                )
            )
    return result


def cleanup(engine: Engine) -> None:
    assert (engine.url.database or "").startswith("sih26263_m1_test_")
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE submission_reviews, apaar_verifications, "
                "case_events, case_records, review_cases, "
                "validation_findings, validation_runs, "
                "student_record_versions, submission_batches, submission_scopes, "
                "audit_events, users, "
                "intake_rules, programmes, institutions"
            )
        )


@pytest.mark.parametrize("different_scopes", [False, True])
def test_real_concurrent_activations(
    db_engine: Engine, demo_settings: Settings, different_scopes: bool
) -> None:
    try:
        candidates = prepared_reviews(
            db_engine, demo_settings, different_scopes=different_scopes
        )
        barrier = Barrier(2)

        def attempt(item: tuple[UUID, ActivationRequest]) -> int:
            with Session(db_engine, expire_on_commit=False) as session:
                barrier.wait(timeout=10)
                try:
                    activate(session, seed_id("users", "cedar_admin"), item[0], item[1])
                    return 200
                except APIError as error:
                    return error.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = sorted(executor.map(attempt, candidates))
        assert results == ([200, 200] if different_scopes else [200, 409])
        with Session(db_engine) as session:
            assert session.scalar(select(func.sum(SubmissionScope.revision))) == (
                2 if different_scopes else 1
            )
            assert session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.action == "SUBMISSION_ACTIVATED")
            ) == (2 if different_scopes else 1)
    finally:
        cleanup(db_engine)


def test_nowait_conflict_does_not_lock_other_scope(
    db_engine: Engine, demo_settings: Settings
) -> None:
    try:
        candidates = prepared_reviews(db_engine, demo_settings, different_scopes=True)
        with (
            Session(db_engine) as holder,
            Session(db_engine, expire_on_commit=False) as contender,
        ):
            batch = holder.get(SubmissionBatch, candidates[0][0])
            assert batch is not None
            holder.scalar(
                select(SubmissionScope)
                .where(SubmissionScope.id == batch.scope_id)
                .with_for_update()
            )
            with pytest.raises(APIError) as caught:
                activate(contender, seed_id("users", "cedar_admin"), *candidates[0])
            assert (
                caught.value.status_code == 409
                and caught.value.code == "ACTIVATION_CONFLICT"
            )
            # Scope 1 remains locked while scope 2 successfully commits.
            assert (
                activate(
                    contender, seed_id("users", "cedar_admin"), *candidates[1]
                ).scope_revision
                == 1
            )
    finally:
        cleanup(db_engine)


def test_peer_activation_stales_assessment_without_blocking_candidate(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    cedar = auth_headers("cedar_admin")
    maple = auth_headers("maple_admin")
    peer = upload(client, maple, institution="maple")
    peer_review = review(client, peer, maple)
    candidate = upload(client, cedar)
    receipt = review(client, candidate, cedar)
    assert receipt["assessment_now"]["current_overlap_records"] == 0
    activate_http(client, peer, peer_review, maple)
    changed = client.get(
        f"/api/v1/submissions/{candidate}/reviews/{receipt['id']}", headers=cedar
    ).json()
    assert changed["review_state"] == "READY"
    assert changed["assessment_now"]["cross_current_freshness"] == "STALE"
    assert changed["assessment_now"]["current_overlap_records"] is None
    assert changed["snapshot"] == receipt["snapshot"]
    activate_http(client, candidate, receipt, cedar)


def test_review_owner_and_account_rechecked(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    other_headers = auth_headers("maple_admin")
    other = seeded_session.get(User, seed_id("users", "maple_admin"))
    assert other is not None
    other.institution_id = seed_id("institutions", "cedar")
    seeded_session.commit()
    response = client.post(
        f"/api/v1/submissions/{identifier}/activate",
        headers=other_headers,
        json=confirmation(receipt),
    )
    assert (
        response.status_code == 403
        and response.json()["error"]["code"] == "REVIEW_ACTOR_MISMATCH"
    )
    owner = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert owner is not None
    owner.active = False
    seeded_session.commit()
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == 401
    )


def test_many_omissions_duplicate_apaar_and_demo_excess_are_reviewable(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    data = csv_data().splitlines(keepends=True)[0] + b"".join(
        csv_data(college_student_id=f"DEMO-{index}").splitlines(keepends=True)[1]
        for index in range(25)
    )
    initial = upload(client, headers, data)
    first = review(client, initial, headers)
    assert (
        first["eligibility"]["eligible"]
        and first["snapshot"]["reviewable_finding_count"] >= 2
    )
    activate_http(client, initial, first, headers)
    replacement = upload(client, headers, csv_data(college_student_id="DEMO-0"))
    receipt = review(client, replacement, headers)
    assert (
        receipt["snapshot"]["omitted_record_count"]
        == receipt["snapshot"]["previously_active_omitted_record_count"]
        == 24
    )
    assert (
        receipt["omission_pagination"]["total"] == 24
        and len(receipt["omitted_records"]) == 20
    )
    second_page = client.get(
        f"/api/v1/submissions/{replacement}/reviews/{receipt['id']}?page=2&page_size=20",
        headers=headers,
    ).json()
    assert len(second_page["omitted_records"]) == 4
    assert "900000000001" not in str(second_page)
    activate_http(client, replacement, receipt, headers)


def test_missing_intake_configuration_is_reviewable(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(
        client, headers, csv_data(academic_year="2025-26"), year="2025-26"
    )
    receipt = review(client, identifier, headers)
    assert receipt["snapshot"]["reviewable_finding_count"] == 5
    activate_http(client, identifier, receipt, headers)


def test_summary_filters_pagination_and_isolation(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    activate_http(client, identifier, review(client, identifier, headers), headers)
    page = client.get(summary_url() + "&page_size=1&page=2", headers=headers).json()
    assert page["pagination"]["total"] == 2 and len(page["data"]) == 1
    assert page["totals"]["declared_records"] == 1
    assert client.get(summary_url("maple"), headers=headers).status_code == 404
    assert (
        client.get(
            summary_url() + f"&programme_id={seed_id('programmes', 'maple/DEMO-COMP')}",
            headers=headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            summary_url().replace("2026-27", "2026-99"), headers=headers
        ).status_code
        == 422
    )
    assert client.get(summary_url()).status_code == 401


def test_legacy_validation_version_mapping_is_explicit(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    from app.modules.validation.models import ValidationRun
    from app.modules.validation.services import structurally_compatible

    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    run_response = run_validation(client, identifier, headers)
    run = seeded_session.get(ValidationRun, UUID(run_response["id"]))
    batch = seeded_session.get(SubmissionBatch, UUID(identifier))
    programme = seeded_session.get(Programme, seed_id("programmes", "cedar/DEMO-COMP"))
    assert run is not None and batch is not None and programme is not None
    legacy = ValidationRun(
        ruleset_version="LOCAL-DEMO-v1",
        completed_at=run.completed_at,
        ruleset_snapshot_json={
            key: value
            for key, value in run.ruleset_snapshot_json.items()
            if key != "structural_ruleset_version"
        },
    )
    assert structurally_compatible(legacy, batch, programme)
    legacy.ruleset_version = "UNKNOWN-OLD-RULESET"
    assert not structurally_compatible(legacy, batch, programme)


def test_activation_database_outage_is_redacted_and_atomic(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    error = OperationalError(
        "redacted", {}, DriverOperationalError("sensitive connection details")
    )
    with patch("app.modules.submissions.activation.record_action", side_effect=error):
        response = client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        )
    assert (
        response.status_code == 503
        and "sensitive connection details" not in response.text
    )
    scope = seeded_session.get(SubmissionScope, UUID(receipt["scope_id"]))
    assert scope is not None and scope.current_batch_id is None and scope.revision == 0


def test_anonymous_verifier_and_incomplete_candidate_denied(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    from app.modules.auth.models import Role

    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    receipt = review(client, identifier, headers)
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/reviews",
            json={"validation_run_id": receipt["validation_run_id"]},
        ).status_code
        == 401
    )
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate", json=confirmation(receipt)
        ).status_code
        == 401
    )
    batch = seeded_session.get(SubmissionBatch, UUID(identifier))
    assert batch is not None
    batch.status = "PROCESSING"  # type: ignore[assignment]
    seeded_session.commit()
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == 409
    )
    user = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert user is not None
    user.role = Role.AUTHORIZED_VERIFIER
    seeded_session.commit()
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/activate",
            headers=headers,
            json=confirmation(receipt),
        ).status_code
        == 403
    )
    assert client.get(summary_url(), headers=headers).status_code == 403
