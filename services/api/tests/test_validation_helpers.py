import csv
import io
from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from test_validation import FIXTURE, run_validation, upload

from app.core.config import Settings
from app.core.http import APIError
from app.modules.validation.models import ValidationFinding
from app.modules.validation.services import affected_record_ids, record_statuses
from app.modules.verification.services import matching_key


@pytest.mark.parametrize("secret", [None, "", "x" * 31])
def test_matching_key_rejects_missing_or_short_bytes(
    settings: Settings, secret: str | None
) -> None:
    settings.apaar_matching_key = SecretStr(secret) if secret is not None else None
    with pytest.raises(APIError) as failure:
        matching_key(settings)
    assert failure.value.status_code == 422
    assert failure.value.code == "MATCHING_CONFIGURATION_UNAVAILABLE"


@pytest.mark.parametrize("secret", ["x" * 32, "é" * 16])
def test_matching_key_boundary_counts_utf8_bytes(
    settings: Settings, secret: str
) -> None:
    settings.apaar_matching_key = SecretStr(secret)
    assert matching_key(settings) == secret.encode()


def test_finding_record_selection_preserves_precedence_and_evidence_order() -> None:
    direct, first, second = uuid4(), uuid4(), uuid4()
    finding = ValidationFinding(
        record_version_id=direct,
        evidence_json_redacted={
            "affected_record_ids": [str(second), str(first), str(second)]
        },
    )
    assert affected_record_ids(finding) == [direct]
    finding.record_version_id = None
    assert affected_record_ids(finding) == [second, first, second]
    finding.evidence_json_redacted = {}
    assert affected_record_ids(finding) == []


@pytest.mark.parametrize("reverse", [False, True])
def test_group_and_direct_statuses_keep_incomplete_precedence(reverse: bool) -> None:
    first, second, untouched = uuid4(), uuid4(), uuid4()
    findings = [
        ValidationFinding(
            rule_code="DUPLICATE_IN_BATCH",
            record_version_id=None,
            evidence_json_redacted={"affected_record_ids": [str(first), str(second)]},
        ),
        ValidationFinding(
            rule_code="REQUIRED_FIELD_MISSING",
            record_version_id=first,
            evidence_json_redacted={"affected_record_ids": [str(untouched)]},
        ),
        ValidationFinding(
            rule_code="MISSING_INTAKE_RULE",
            record_version_id=None,
            evidence_json_redacted={},
        ),
    ]
    if reverse:
        findings.reverse()
    assert record_statuses(findings) == {first: "INCOMPLETE", second: "FLAGGED"}


def test_feedback_group_findings_match_row_statuses(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    demo_settings: Settings,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers, FIXTURE.read_bytes())
    demo_settings.validation_intake_rule_version = "DEMO-NOT-CONFIGURED"
    run_validation(client, identifier, headers)
    base = f"/api/v1/submissions/{identifier}"
    rows = client.get(base + "/rows", headers=headers).json()["data"]
    findings = client.get(base + "/findings?page_size=100", headers=headers).json()[
        "data"
    ]
    feedback = client.get(base + "/feedback.csv", headers=headers)
    assert feedback.status_code == 200
    exported = list(csv.DictReader(io.StringIO(feedback.text)))
    for row in rows:
        entries = [item for item in exported if item["record_version_id"] == row["id"]]
        assert entries
        assert {item["validation_status"] for item in entries} == {
            row["validation_status"]
        }
    grouped = next(
        item for item in findings if item["rule_code"] == "DUPLICATE_IN_BATCH"
    )
    assert [
        item["record_version_id"]
        for item in exported
        if item["rule_code"] == "DUPLICATE_IN_BATCH"
    ] == grouped["evidence"]["affected_record_ids"]
    assert any(
        not item["record_version_id"] and item["rule_code"] == "MISSING_INTAKE_RULE"
        for item in exported
    )
