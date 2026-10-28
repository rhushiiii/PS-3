"""Local DEMO rules. No identity verification, mutation, or external calls."""

import hmac
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.modules.institutions.models import AdmissionCategory, IntakeRule
from app.modules.submissions.models import StudentRecordVersion, SubmissionBatch
from app.modules.submissions.parsing import HEADERS

RULESET_VERSION = "LOCAL-DEMO-v1"
# Bump whenever activation-blocking rules change. Legacy M3 runs map explicitly
# to v1 only; never infer compatibility from a missing version in future runs.
STRUCTURAL_RULESET_VERSION = "LOCAL-STRUCTURE-DEMO-v1"
STATUSES = ("ACTIVE", "WITHDRAWN", "TRANSFERRED", "COMPLETED")
CATEGORIES = tuple(category.value for category in AdmissionCategory)
STRUCTURAL_FIELDS = {
    "college_student_id",
    "academic_year",
    "programme_code",
    "admission_category",
    "enrollment_status",
}


@dataclass
class Finding:
    code: str
    explanation: str
    record_id: UUID | None = None
    field_name: str | None = None
    severity: str = "WARNING"
    classification: str = "REVIEWABLE"
    evidence: dict[str, Any] = field(default_factory=dict)


def valid_token(token: str, length: int) -> bool:
    return len(token) == length and all("0" <= char <= "9" for char in token)


def token_hash(token: str, key: bytes) -> bytes:
    return hmac.digest(key, token.encode("utf-8"), "sha256")


def valid_year(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9]{4}-[0-9]{2}", value)) and (
        (int(value[:4]) + 1) % 100 == int(value[-2:])
    )


def structural_findings(
    rows: list[StudentRecordVersion],
    batch: SubmissionBatch,
    programme_code: str,
) -> list[Finding]:
    findings: list[Finding] = []
    local_ids: dict[str, list[StudentRecordVersion]] = defaultdict(list)
    for row in rows:
        values = row.normalized_json
        for column in HEADERS:
            if column in STRUCTURAL_FIELDS and not values[column]:
                findings.append(
                    Finding(
                        "REQUIRED_FIELD_MISSING",
                        "Required value is missing",
                        row.id,
                        column,
                        "ERROR",
                        "ACTIVATION_BLOCKING",
                        {"source_row_number": row.source_row_number},
                    )
                )
        checks = (
            (
                "academic_year",
                "INVALID_ACADEMIC_YEAR",
                not valid_year(values["academic_year"])
                or values["academic_year"] != batch.academic_year,
                "Year is malformed or differs from the candidate scope",
            ),
            (
                "programme_code",
                "PROGRAMME_MISMATCH",
                values["programme_code"] != programme_code,
                "Programme differs from the candidate scope",
            ),
            (
                "admission_category",
                "INVALID_ADMISSION_CATEGORY",
                values["admission_category"] not in CATEGORIES,
                "Category is not supported by this DEMO ruleset",
            ),
            (
                "enrollment_status",
                "INVALID_ENROLLMENT_STATUS",
                values["enrollment_status"] not in STATUSES,
                "Enrolment status is not supported by this DEMO ruleset",
            ),
        )
        for column, code, failed, message in checks:
            if values[column] and failed:
                findings.append(
                    Finding(
                        code,
                        message,
                        row.id,
                        column,
                        "ERROR",
                        "ACTIVATION_BLOCKING",
                        {"source_row_number": row.source_row_number},
                    )
                )
        if row.college_student_id:
            local_ids[row.college_student_id].append(row)
    for group in local_ids.values():
        if len(group) > 1:
            findings.append(
                Finding(
                    "DUPLICATE_COLLEGE_STUDENT_ID",
                    "Repeated local student identifier makes counting ambiguous",
                    severity="ERROR",
                    classification="ACTIVATION_BLOCKING",
                    evidence={
                        "affected_record_ids": [str(row.id) for row in group],
                        "source_row_numbers": [row.source_row_number for row in group],
                        "record_count": len(group),
                    },
                )
            )
    return findings


def evaluate(
    rows: list[StudentRecordVersion],
    batch: SubmissionBatch,
    programme_code: str,
    intake: list[IntakeRule],
    peers: Iterable[tuple[StudentRecordVersion, SubmissionBatch]],
    current_batches: set[str],
    *,
    key: bytes,
    format_length: int,
    check_budget: Callable[[], None],
) -> tuple[list[Finding], dict[str, Any]]:
    findings = structural_findings(rows, batch, programme_code)
    local_ids: dict[str, list[StudentRecordVersion]] = defaultdict(list)
    tokens: dict[bytes, list[StudentRecordVersion]] = defaultdict(list)
    declared: Counter[str] = Counter()
    active: Counter[str] = Counter()
    unclassifiable = 0
    active_records = 0

    def add(
        row: StudentRecordVersion,
        code: str,
        column: str,
        message: str,
        *,
        blocking: bool = False,
    ) -> None:
        findings.append(
            Finding(
                code,
                message,
                row.id,
                column,
                "ERROR" if blocking else "WARNING",
                "ACTIVATION_BLOCKING" if blocking else "REVIEWABLE",
                {"source_row_number": row.source_row_number},
            )
        )

    for row in rows:
        check_budget()
        values = row.normalized_json
        for column in HEADERS:
            if column not in STRUCTURAL_FIELDS and not values[column]:
                add(
                    row,
                    "REQUIRED_FIELD_MISSING",
                    column,
                    "Required value is missing",
                    blocking=column in STRUCTURAL_FIELDS,
                )
        year = values["academic_year"]
        programme = values["programme_code"]
        category = values["admission_category"]
        status = values["enrollment_status"]
        scope_valid = (
            valid_year(year)
            and year == batch.academic_year
            and programme == programme_code
        )
        if values["enrollment_date"] and row.enrollment_date is None:
            add(
                row,
                "INVALID_ENROLLMENT_DATE",
                "enrollment_date",
                "Date must be a valid YYYY-MM-DD date; original value is preserved",
            )
        token = values["apaar_id"]
        if token:
            if valid_token(token, format_length):
                tokens[token_hash(token, key)].append(row)
            else:
                add(
                    row,
                    "INVALID_APAAR_FORMAT",
                    "apaar_id",
                    "Fails local ASCII-digit structure; not an identity check",
                )
        if values["college_student_id"]:
            local_ids[values["college_student_id"]].append(row)
        if category in CATEGORIES:
            declared[category] += 1
        if status == "ACTIVE":
            active_records += 1
            if scope_valid and category in CATEGORIES:
                active[category] += 1
        if not scope_valid or category not in CATEGORIES or status not in STATUSES:
            unclassifiable += 1

    def group_finding(
        group: list[StudentRecordVersion], code: str, blocking: bool
    ) -> None:
        findings.append(
            Finding(
                code,
                "Repeated local student identifier makes counting ambiguous"
                if blocking
                else "Potential repeated APAAR within candidate; no records merged",
                severity="ERROR" if blocking else "WARNING",
                classification="ACTIVATION_BLOCKING" if blocking else "REVIEWABLE",
                evidence={
                    "affected_record_ids": [str(row.id) for row in group],
                    "source_row_numbers": [row.source_row_number for row in group],
                    "record_count": len(group),
                },
            )
        )

    for group in tokens.values():
        if len(group) > 1:
            group_finding(group, "DUPLICATE_IN_BATCH", False)

    # Each peer is retained once per token/context, avoiding a local×peer expansion.
    matches: dict[tuple[bytes, str], list[dict[str, str]]] = defaultdict(list)
    current_overlap: set[str] = set()
    excluded_current_peers = 0
    for peer, peer_batch in peers:
        check_budget()
        token = peer.apaar_identifier_encrypted_or_demo_token
        if not valid_token(token, format_length):
            if (
                str(peer.batch_id) in current_batches
                and peer.academic_year == batch.academic_year
                and peer.enrollment_status == "ACTIVE"
            ):
                excluded_current_peers += 1
            continue
        digest = token_hash(token, key)
        matching_group = tokens.get(digest)
        if not matching_group:
            continue
        if peer.academic_year != batch.academic_year:
            context = "DIFFERENT_YEAR"
        elif str(peer.batch_id) in current_batches:
            context = (
                "CURRENT_ACTIVE"
                if peer.enrollment_status == "ACTIVE"
                else "CURRENT_INACTIVE"
            )
        elif peer_batch.activated_at is not None:
            context = "HISTORICAL"
        else:
            context = "UNACTIVATED_CANDIDATE"
        matches[digest, context].append(
            {
                "institution_id": str(peer.institution_id),
                "batch_id": str(peer.batch_id),
                "record_version_id": str(peer.id),
            }
        )

    informational_versions = 0
    for (digest, context), references in matches.items():
        check_budget()
        group = tokens[digest]
        affected = (
            [row for row in group if row.enrollment_status == "ACTIVE"]
            if context == "CURRENT_ACTIVE"
            else group
        )
        # Inactive local records cannot contribute to current active overlap counts.
        inactive = (
            [row for row in group if row.enrollment_status != "ACTIVE"]
            if context == "CURRENT_ACTIVE"
            else []
        )
        for local_group, match_context in (
            (affected, context),
            (inactive, "LOCAL_INACTIVE"),
        ):
            if not local_group:
                continue
            is_current = match_context == "CURRENT_ACTIVE"
            if is_current:
                current_overlap.update(str(row.id) for row in local_group)
            else:
                informational_versions += len(references)
            findings.append(
                Finding(
                    "POTENTIAL_CROSS_INSTITUTION_DUPLICATE",
                    "Potential current ACTIVE overlap; transfers require review"
                    if is_current
                    else "Informational match as of evaluation; not current overlap",
                    severity="WARNING" if is_current else "INFO",
                    evidence={
                        "affected_record_ids": [str(row.id) for row in local_group],
                        "source_row_numbers": [
                            row.source_row_number for row in local_group
                        ],
                        "match_context": match_context,
                        "peer_references": references,
                    },
                )
            )

    capacities = {rule.category.value: rule for rule in intake}
    ambiguous_ids = any(len(group) > 1 for group in local_ids.values()) or any(
        not row.college_student_id for row in rows
    )
    for category in CATEGORIES:
        rule = capacities.get(category)
        if rule is None:
            findings.append(
                Finding(
                    "MISSING_INTAKE_RULE",
                    "No configured DEMO capacity; no regulatory violation inferred",
                    evidence={"category": category, "source_label": "DEMO"},
                )
            )
        elif active[category] > rule.approved_seats:
            findings.append(
                Finding(
                    "INTAKE_EXCEEDED",
                    "Candidate ACTIVE rows exceed DEMO capacity; not official policy",
                    evidence={
                        "category": category,
                        "candidate_active_rows": active[category],
                        "configured_capacity": rule.approved_seats,
                        "intake_rule_id": str(rule.id),
                        "rule_version": rule.rule_version,
                        "source_label": "DEMO",
                        "counts_uncertain": ambiguous_ids or bool(unclassifiable),
                    },
                )
            )

    return findings, {
        "reported_records": len(rows),
        "candidate_demo_active_records": active_records,
        "category_declared_records": {
            category: declared[category] for category in CATEGORIES
        },
        "category_allocated_active_records": {
            category: active[category] for category in CATEGORIES
        },
        "unclassifiable_records": unclassifiable,
        "ambiguous_student_ids": ambiguous_ids,
        "intake_assessment": "INCOMPLETE"
        if unclassifiable or ambiguous_ids or len(capacities) != len(CATEGORIES)
        else "COMPLETE",
        "current_overlap_records_at_evaluation": len(current_overlap),
        "matching_excluded_current_peer_records": excluded_current_peers,
        "informational_match_version_references": informational_versions,
        "source_label": "DEMO",
        "count_basis": "CANDIDATE_ROWS_NOT_CURRENT_ENROLMENT",
    }
