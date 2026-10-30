import csv
import io
import os
import socket
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from time import monotonic, sleep
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx2
import pytest
from conftest import truncate_all
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, delete, func, select, update
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.modules.auth.models import Role, User
from app.modules.institutions.models import IntakeRule
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.parsing import HEADERS, parse_csv
from app.modules.submissions.schemas import UploadContext
from app.modules.submissions.services import persist_candidate
from app.modules.validation.models import ValidationFinding, ValidationRun
from app.modules.validation.services import safe_csv_cell, validate_candidate
from app.seed import seed_demo, seed_id

FIXTURE = Path(__file__).resolve().parents[3] / "samples" / "synthetic_validation.csv"


def fields(institution: str = "cedar", year: str = "2026-27") -> dict[str, str]:
    return {
        "institution_id": str(seed_id("institutions", institution)),
        "programme_id": str(seed_id("programmes", f"{institution}/DEMO-COMP")),
        "academic_year": year,
        "schema_version": "v1",
    }


def csv_data(**changes: str) -> bytes:
    values = dict(
        zip(
            HEADERS,
            [
                "DEMO-ONE",
                "Synthetic One",
                "900000000001",
                "2026-27",
                "DEMO-COMP",
                "REGULAR",
                "ACTIVE",
                "2026-08-01",
            ],
            strict=True,
        )
    )
    values.update(changes)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    writer.writerow(values.values())
    return output.getvalue().encode()


def upload(
    client: TestClient,
    headers: dict[str, str],
    data: bytes | None = None,
    institution: str = "cedar",
    year: str = "2026-27",
) -> str:
    response = client.post(
        "/api/v1/submissions",
        headers=headers,
        data=fields(institution, year),
        files={
            "file": (
                "synthetic.csv",
                data if data is not None else csv_data(),
                "text/csv",
            )
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["validation_performed"] is False
    return str(response.json()["id"])


def run_validation(
    client: TestClient,
    identifier: str,
    headers: dict[str, str],
    *,
    repeat: bool = False,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/submissions/{identifier}/{'revalidate' if repeat else 'validate'}",
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def activate_demo(client: TestClient, identifier: str, headers: dict[str, str]) -> None:
    run = run_validation(client, identifier, headers)
    response = client.post(
        f"/api/v1/submissions/{identifier}/reviews",
        headers=headers,
        json={"validation_run_id": run["id"]},
    )
    assert response.status_code == 201, response.text
    review = response.json()
    response = client.post(
        f"/api/v1/submissions/{identifier}/activate",
        headers=headers,
        json={
            "review_id": review["id"],
            "expected_scope_revision": review["expected_scope_revision"],
            "confirm_complete_replacement": True,
            "acknowledge_review_warnings": True,
            "acknowledge_omissions": True,
        },
    )
    assert response.status_code == 200, response.text


def test_validation_workflow_and_immutable_history(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers, FIXTURE.read_bytes())
    initial = run_validation(client, identifier, headers)
    assert initial["kind"] == "INITIAL"
    assert initial["summary"]["reported_records"] == 6
    assert initial["summary"]["candidate_demo_active_records"] == 4
    assert initial["summary"]["matching_assessment"] == "INCOMPLETE"
    assert initial["current_overlap_records"] is None
    findings = client.get(
        f"/api/v1/submissions/{identifier}/findings?page_size=100", headers=headers
    ).json()["data"]
    codes = {item["rule_code"] for item in findings}
    assert {
        "REQUIRED_FIELD_MISSING",
        "INVALID_ENROLLMENT_DATE",
        "INVALID_APAAR_FORMAT",
        "DUPLICATE_COLLEGE_STUDENT_ID",
        "DUPLICATE_IN_BATCH",
        "INVALID_ACADEMIC_YEAR",
        "PROGRAMME_MISMATCH",
        "INVALID_ADMISSION_CATEGORY",
        "INVALID_ENROLLMENT_STATUS",
        "INTAKE_EXCEEDED",
    } <= codes
    rows = client.get(f"/api/v1/submissions/{identifier}/rows", headers=headers).json()[
        "data"
    ]
    assert rows[1]["validation_status"] == "INCOMPLETE"
    assert rows[0]["validation_status"] == "FLAGGED"
    assert rows[1]["apaar_verification_status"] == "NOT_CHECKED"
    assert (
        len([item for item in findings if item["record_version_id"] == rows[1]["id"]])
        == 3
    )
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/validate", headers=headers
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/revalidate", headers=headers
        ).status_code
        == 403
    )
    repeated = run_validation(
        client, identifier, auth_headers("demo_officer"), repeat=True
    )
    assert repeated["id"] != initial["id"] and repeated["summary"] == initial["summary"]
    history = client.get(
        f"/api/v1/submissions/{identifier}/validation-runs", headers=headers
    ).json()
    assert history["pagination"]["total"] == 2
    assert (
        client.get(
            f"/api/v1/submissions/{identifier}/rows?run_id={initial['id']}&status=INCOMPLETE",
            headers=headers,
        ).json()["pagination"]["total"]
        == 2
    )
    for model in (ValidationRun, ValidationFinding):
        for statement in (update(model).values(id=uuid4()), delete(model)):
            with pytest.raises(DBAPIError), seeded_session.begin_nested():
                seeded_session.execute(statement)
    scope = seeded_session.scalar(select(SubmissionScope))
    assert scope is not None and scope.current_batch_id is None and scope.revision == 0
    assert all(
        value is None
        for value in seeded_session.scalars(
            select(StudentRecordVersion.apaar_match_hash)
        )
    )


@pytest.mark.parametrize("column", HEADERS)
def test_missing_required_fields_keep_all_findings(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]], column: str
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers, csv_data(**{column: ""}))
    run_validation(client, identifier, headers)
    response = client.get(f"/api/v1/submissions/{identifier}/findings", headers=headers)
    finding = next(
        item
        for item in response.json()["data"]
        if item["rule_code"] == "REQUIRED_FIELD_MISSING"
    )
    assert finding["field_name"] == column
    assert finding["classification"] == (
        "REVIEWABLE"
        if column in {"student_name", "apaar_id", "enrollment_date"}
        else "ACTIVATION_BLOCKING"
    )
    assert (
        client.get(f"/api/v1/submissions/{identifier}/rows", headers=headers).json()[
            "data"
        ][0]["validation_status"]
        == "INCOMPLETE"
    )


@pytest.mark.parametrize("value", [None, "", "short"])
def test_missing_matching_secret_never_returns_clean_zero(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    demo_settings: Settings,
    seeded_session: Session,
    value: str | None,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    demo_settings.apaar_matching_key = SecretStr(value) if value is not None else None
    response = client.post(
        f"/api/v1/submissions/{identifier}/validate", headers=headers
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MATCHING_CONFIGURATION_UNAVAILABLE"
    assert seeded_session.scalar(select(func.count()).select_from(ValidationRun)) == 0
    assert client.get("/api/v1/health").status_code == 200


@pytest.mark.parametrize(
    "context",
    [
        "CURRENT_ACTIVE",
        "CURRENT_INACTIVE",
        "HISTORICAL",
        "UNACTIVATED_CANDIDATE",
        "DIFFERENT_YEAR",
    ],
)
def test_cross_matches_freshness_and_redaction(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    context: str,
) -> None:
    cedar = auth_headers("cedar_admin")
    maple = auth_headers("maple_admin")
    year = "2025-26" if context == "DIFFERENT_YEAR" else "2026-27"
    peer_id = upload(
        client,
        maple,
        csv_data(
            academic_year=year,
            enrollment_status="WITHDRAWN"
            if context == "CURRENT_INACTIVE"
            else "ACTIVE",
        ),
        "maple",
        year,
    )
    peer = seeded_session.get(SubmissionBatch, UUID(peer_id))
    assert peer is not None
    if context.startswith("CURRENT_") or context == "HISTORICAL":
        activate_demo(client, peer_id, maple)
    if context == "HISTORICAL":
        replacement = upload(
            client, maple, csv_data(apaar_id="900000000009"), institution="maple"
        )
        activate_demo(client, replacement, maple)
    seeded_session.commit()
    identifier = upload(client, cedar)
    result = run_validation(client, identifier, cedar)
    assert result["current_overlap_records"] == (
        1 if context == "CURRENT_ACTIVE" else 0
    )
    url = f"/api/v1/submissions/{identifier}/findings"
    admin_findings = client.get(url, headers=cedar)
    finding = next(
        item
        for item in admin_findings.json()["data"]
        if item["rule_code"] == "POTENTIAL_CROSS_INSTITUTION_DUPLICATE"
    )
    assert finding["evidence"]["match_context"] == context
    assert finding["severity"] == ("WARNING" if context == "CURRENT_ACTIVE" else "INFO")
    assert (
        "peer_references" not in admin_findings.text
        and peer_id not in admin_findings.text
    )
    officer_findings = client.get(url, headers=auth_headers("demo_officer"))
    assert peer_id in officer_findings.text
    assert "900000000001" not in officer_findings.text
    # A scope revision change makes only assessment freshness stale, not row validity.
    scope = seeded_session.get(SubmissionScope, peer.scope_id)
    assert scope is not None
    if year == "2026-27":
        scope.revision += 1
        seeded_session.commit()
        stale = client.get(
            f"/api/v1/submissions/{identifier}/validation-runs/{result['id']}",
            headers=cedar,
        ).json()
        assert (
            stale["cross_current_freshness"] == "STALE"
            and stale["current_overlap_records"] is None
        )
        refreshed = run_validation(
            client, identifier, auth_headers("demo_officer"), repeat=True
        )
        assert refreshed["cross_current_freshness"] == "FRESH"
        original = seeded_session.get(ValidationRun, UUID(result["id"]))
        assert original is not None and original.summary_json == result["summary"]


def test_new_candidate_is_as_of_run_but_new_scope_stales(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    cedar = auth_headers("cedar_admin")
    maple = auth_headers("maple_admin")
    upload(client, maple, institution="maple")
    identifier = upload(client, cedar)
    result = run_validation(client, identifier, cedar)
    upload(client, maple, institution="maple")
    url = f"/api/v1/submissions/{identifier}/validation-runs/{result['id']}"
    assert client.get(url, headers=cedar).json()["cross_current_freshness"] == "FRESH"
    upload(
        client,
        auth_headers("willow_admin"),
        csv_data(apaar_id="900000000009"),
        "willow",
    )
    assert client.get(url, headers=cedar).json()["cross_current_freshness"] == "STALE"


@pytest.mark.parametrize(
    "alias,expected", [("maple_admin", 404), ("demo_manager", 403)]
)
def test_validation_permissions(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    alias: str,
    expected: int,
) -> None:
    identifier = upload(client, auth_headers("cedar_admin"))
    headers = auth_headers(alias)
    for suffix in ("validate", "revalidate"):
        assert (
            client.post(
                f"/api/v1/submissions/{identifier}/{suffix}", headers=headers
            ).status_code
            == expected
        )
    for suffix in ("validation-runs", "findings", "feedback.csv"):
        assert (
            client.get(
                f"/api/v1/submissions/{identifier}/{suffix}", headers=headers
            ).status_code
            == expected
        )


@pytest.mark.parametrize(
    "cell",
    [
        "=1+1",
        "+1",
        "-1",
        "@SUM(1)",
        " \t=1",
        "\r=1",
        "\n=1",
        "\ttext",
        "\x01=1",
        "\u00a0=1",
        "\ufeff=1",
    ],
)
def test_formula_injection(cell: str) -> None:
    assert safe_csv_cell(cell).startswith("'")
    assert safe_csv_cell("DEMO-ONE") == "DEMO-ONE"


def test_feedback_export_and_invalid_run_inputs(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(
        client,
        headers,
        csv_data(college_student_id=" \t=SUM(1)", student_name="Synthetic\nMultiline"),
    )
    base = f"/api/v1/submissions/{identifier}"
    assert client.get(base + "/feedback.csv", headers=headers).status_code == 409
    run = run_validation(client, identifier, headers)
    response = client.get(base + "/feedback.csv", headers=headers)
    assert (
        response.status_code == 200 and response.headers["cache-control"] == "no-store"
    )
    exported = list(csv.DictReader(io.StringIO(response.text)))
    assert exported[0]["college_student_id"].startswith("'")
    assert exported[0]["source_row_number"] == "2"
    assert "900000000001" not in response.text
    assert client.get(base + "/rows?status=INVALID", headers=headers).status_code == 422
    assert (
        client.get(base + "/findings?severity=CRITICAL", headers=headers).status_code
        == 422
    )
    assert (
        client.get(base + f"/findings?run_id={uuid4()}", headers=headers).status_code
        == 404
    )
    other = upload(client, headers)
    assert (
        client.get(
            f"/api/v1/submissions/{other}/rows?run_id={run['id']}", headers=headers
        ).status_code
        == 404
    )


@pytest.mark.parametrize("mode", ["budget", "comparison", "database"])
def test_validation_failure_rolls_back_all_evidence(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    demo_settings: Settings,
    mode: str,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    if mode == "budget":
        demo_settings.validation_processing_timeout_seconds = 1e-12
    elif mode == "comparison":
        demo_settings.validation_max_comparison_records = 1
        maple = auth_headers("maple_admin")
        upload(client, maple, institution="maple")
        upload(client, maple, institution="maple")
    if mode == "database":
        with patch(
            "app.modules.validation.services.record_action",
            side_effect=ProgrammingError("redacted", {}, Exception("sensitive")),
        ):
            response = client.post(
                f"/api/v1/submissions/{identifier}/validate", headers=headers
            )
        assert response.status_code == 500 and "sensitive" not in response.text
    else:
        response = client.post(
            f"/api/v1/submissions/{identifier}/validate", headers=headers
        )
        assert response.status_code == 422
    assert seeded_session.scalar(select(func.count()).select_from(ValidationRun)) == 0
    assert (
        seeded_session.scalar(select(func.count()).select_from(ValidationFinding)) == 0
    )


def test_missing_intake_version_is_not_inferred(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    demo_settings: Settings,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    demo_settings.validation_intake_rule_version = "DEMO-NOT-CONFIGURED"
    run = run_validation(client, identifier, headers)
    assert run["summary"]["intake_assessment"] == "INCOMPLETE"
    assert run["ruleset_snapshot"]["intake_rules"] == []
    findings = client.get(
        f"/api/v1/submissions/{identifier}/findings", headers=headers
    ).json()["data"]
    assert (
        len([item for item in findings if item["rule_code"] == "MISSING_INTAKE_RULE"])
        == 5
    )


def test_concurrent_initial_validation_and_revalidation(
    db_engine: Engine, demo_settings: Settings
) -> None:
    assert (db_engine.url.database or "").startswith("sih26263_m1_test_")
    try:
        with Session(db_engine, expire_on_commit=False) as session:
            seed_demo(session, demo_settings)
            session.commit()
            user = session.get(User, seed_id("users", "cedar_admin"))
            assert user is not None
            data = csv_data()
            identifier = persist_candidate(
                session,
                user,
                UploadContext.model_validate(fields()),
                data,
                "synthetic.csv",
                parse_csv(data, demo_settings, monotonic() + 30),
                monotonic() + 30,
            ).id
        barrier = Barrier(2)

        def evaluate_concurrently(repeat: bool) -> int:
            with (
                db_engine.connect().execution_options(
                    isolation_level="REPEATABLE READ"
                ) as connection,
                Session(connection, expire_on_commit=False) as session,
            ):
                barrier.wait(timeout=10)
                try:
                    validate_candidate(
                        session,
                        seed_id("users", "demo_officer"),
                        identifier,
                        demo_settings,
                        revalidate=repeat,
                    )
                    return 201
                except APIError as error:
                    return error.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(evaluate_concurrently, [False, False]))
        assert sorted(results) == [201, 409]
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert list(executor.map(evaluate_concurrently, [True, True])) == [201, 201]
        with Session(db_engine) as session:
            assert session.scalar(select(func.count()).select_from(ValidationRun)) == 3
    finally:
        truncate_all(db_engine)


@pytest.mark.parametrize(
    "column,value,code",
    [
        ("academic_year", "2026-99", "INVALID_ACADEMIC_YEAR"),
        ("academic_year", "2026", "INVALID_ACADEMIC_YEAR"),
        ("programme_code", "OTHER", "PROGRAMME_MISMATCH"),
        ("admission_category", "UNKNOWN", "INVALID_ADMISSION_CATEGORY"),
        ("enrollment_status", "UNKNOWN", "INVALID_ENROLLMENT_STATUS"),
        ("enrollment_date", "2026-02-30", "INVALID_ENROLLMENT_DATE"),
        ("apaar_id", "９００００００００００１", "INVALID_APAAR_FORMAT"),
        ("apaar_id", "9000-00000001", "INVALID_APAAR_FORMAT"),
    ],
)
def test_invalid_values_preserved(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    column: str,
    value: str,
    code: str,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers, csv_data(**{column: value}))
    run_validation(client, identifier, headers)
    findings = client.get(
        f"/api/v1/submissions/{identifier}/findings", headers=headers
    ).json()["data"]
    assert code in {item["rule_code"] for item in findings}
    row = seeded_session.scalar(
        select(StudentRecordVersion).where(
            StudentRecordVersion.batch_id == UUID(identifier)
        )
    )
    assert row is not None and row.original_json[column] == value


def test_intake_versions_and_candidate_history_are_not_summed(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    first = run_validation(client, identifier, headers)
    rule = seeded_session.scalar(
        select(IntakeRule).where(
            IntakeRule.programme_id == seed_id("programmes", "cedar/DEMO-COMP"),
            IntakeRule.category == "REGULAR",
        )
    )
    assert rule is not None
    rule.approved_seats = 0
    seeded_session.commit()
    second = run_validation(
        client, identifier, auth_headers("demo_officer"), repeat=True
    )
    assert first["ruleset_snapshot"] != second["ruleset_snapshot"]
    old = seeded_session.get(ValidationRun, UUID(first["id"]))
    assert old is not None and old.ruleset_snapshot_json == first["ruleset_snapshot"]
    corrected = upload(
        client,
        headers,
        csv_data(admission_category="NRI", enrollment_status="TRANSFERRED"),
    )
    corrected_run = run_validation(client, corrected, headers)
    assert corrected_run["summary"]["reported_records"] == 1
    assert corrected_run["summary"]["candidate_demo_active_records"] == 0
    assert corrected_run["summary"]["category_declared_records"]["NRI"] == 1


def test_incomplete_peer_and_inactive_local_not_current_overlap(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    maple = auth_headers("maple_admin")
    cedar = auth_headers("cedar_admin")
    peer_id = upload(client, maple, csv_data(apaar_id="bad-demo"), institution="maple")
    peer = seeded_session.get(SubmissionBatch, UUID(peer_id))
    assert peer is not None
    scope = seeded_session.get(SubmissionScope, peer.scope_id)
    assert scope is not None
    activate_demo(client, peer_id, maple)
    identifier = upload(client, cedar)
    run = run_validation(client, identifier, cedar)
    assert run["current_overlap_records"] is None
    assert run["summary"]["matching_excluded_current_peer_records"] == 1
    # A separate, valid current peer and inactive local row are informational only.
    valid_peer = upload(client, maple, institution="maple")
    activate_demo(client, valid_peer, maple)
    inactive = upload(client, cedar, csv_data(enrollment_status="WITHDRAWN"))
    inactive_run = run_validation(client, inactive, cedar)
    assert inactive_run["current_overlap_records"] == 0
    findings = client.get(
        f"/api/v1/submissions/{inactive}/findings", headers=cedar
    ).json()["data"]
    assert (
        next(
            f
            for f in findings
            if f["rule_code"] == "POTENTIAL_CROSS_INSTITUTION_DUPLICATE"
        )["evidence"]["match_context"]
        == "LOCAL_INACTIVE"
    )


def test_anonymous_and_verifier_denied(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = upload(client, headers)
    for suffix in ("validate", "revalidate"):
        assert (
            client.post(f"/api/v1/submissions/{identifier}/{suffix}").status_code == 401
        )
    for suffix in ("validation-runs", "findings", "feedback.csv"):
        assert (
            client.get(f"/api/v1/submissions/{identifier}/{suffix}").status_code == 401
        )
    user = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert user is not None
    user.role = Role.AUTHORIZED_VERIFIER
    seeded_session.commit()
    assert (
        client.post(
            f"/api/v1/submissions/{identifier}/validate", headers=headers
        ).status_code
        == 403
    )


def test_loopback_http_validation_smoke(
    db_engine: Engine, demo_settings: Settings
) -> None:
    """Real HTTP + production dependencies, without TestClient/session overrides."""
    assert (db_engine.url.database or "").startswith("sih26263_m1_test_")
    process: subprocess.Popen[str] | None = None
    try:
        with Session(db_engine) as session, session.begin():
            seed_demo(session, demo_settings)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert demo_settings.demo_auth_secret is not None
        assert demo_settings.apaar_matching_key is not None
        environment = {
            **os.environ,
            "APP_ENV": "local",
            "DEMO_AUTH": "true",
            "DATABASE_URL": db_engine.url.render_as_string(hide_password=False),
            "DEMO_AUTH_SECRET": demo_settings.demo_auth_secret.get_secret_value(),
            "APAAR_MATCHING_KEY": demo_settings.apaar_matching_key.get_secret_value(),
        }
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-proxy-headers",
                "--no-access-log",
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        with httpx2.Client(
            base_url=f"http://127.0.0.1:{port}", timeout=15, trust_env=False
        ) as http:
            deadline = monotonic() + 15
            while True:
                try:
                    assert http.get("/api/v1/health").status_code == 200
                    break
                except httpx2.ConnectError:
                    assert monotonic() < deadline and process.poll() is None
                    sleep(0.1)
            assert http.get("/api/v1/ready").status_code == 200
            token = http.post(
                "/api/v1/auth/demo-login", json={"demo_alias": "cedar_admin"}
            ).json()["access_token"]
            headers = {"Authorization": "Bearer " + token}
            response = http.post(
                "/api/v1/submissions",
                headers=headers,
                data=fields(),
                files={"file": ("synthetic.csv", FIXTURE.read_bytes(), "text/csv")},
            )
            assert response.status_code == 201
            identifier = response.json()["id"]
            base = f"/api/v1/submissions/{identifier}"
            response = http.post(base + "/validate", headers=headers)
            assert response.status_code == 201, response.text
            run_id = response.json()["id"]
            for suffix in (
                "/rows",
                "/findings",
                "/validation-runs",
                f"/validation-runs/{run_id}",
                "/feedback.csv",
            ):
                response = http.get(base + suffix, headers=headers)
                assert response.status_code == 200
                assert "900000000001" not in response.text
            token = http.post(
                "/api/v1/auth/demo-login", json={"demo_alias": "demo_officer"}
            ).json()["access_token"]
            assert (
                http.post(
                    base + "/revalidate", headers={"Authorization": "Bearer " + token}
                ).status_code
                == 201
            )
            # Upload and both validation actions still left the scope inactive.
            assert not http.get(base, headers=headers).json()["is_current"]
            blocked = http.post(
                base + "/reviews", headers=headers, json={"validation_run_id": run_id}
            )
            assert (
                blocked.status_code == 201
                and not blocked.json()["eligibility"]["eligible"]
            )
            assert (
                http.post(
                    base + "/activate",
                    headers=headers,
                    json={
                        "review_id": blocked.json()["id"],
                        "expected_scope_revision": 0,
                        "confirm_complete_replacement": True,
                        "acknowledge_review_warnings": True,
                    },
                ).status_code
                == 409
            )
            good = http.post(
                "/api/v1/submissions",
                headers=headers,
                data=fields(),
                files={"file": ("synthetic.csv", csv_data(), "text/csv")},
            )
            assert good.status_code == 201
            good_base = f"/api/v1/submissions/{good.json()['id']}"
            good_run = http.post(good_base + "/validate", headers=headers)
            assert good_run.status_code == 201
            receipt = http.post(
                good_base + "/reviews",
                headers=headers,
                json={"validation_run_id": good_run.json()["id"]},
            )
            assert (
                receipt.status_code == 201 and receipt.json()["review_state"] == "READY"
            )
            confirmed = http.post(
                good_base + "/activate",
                headers=headers,
                json={
                    "review_id": receipt.json()["id"],
                    "expected_scope_revision": 0,
                    "confirm_complete_replacement": True,
                    "acknowledge_review_warnings": True,
                },
            )
            assert confirmed.status_code == 200, confirmed.text
            current = http.get(
                f"/api/v1/institutions/{fields()['institution_id']}/summary?academic_year=2026-27",
                headers=headers,
            )
            assert (
                current.status_code == 200
                and current.json()["totals"]["declared_records"] == 1
            )
            assert (
                http.get(
                    good_base + f"/reviews/{receipt.json()['id']}", headers=headers
                ).json()["review_state"]
                == "CONSUMED"
            )
        with Session(db_engine) as session:
            assert session.scalar(select(func.count()).select_from(ValidationRun)) == 3
            assert all(
                scope.current_batch_id is not None and scope.revision == 1
                for scope in session.scalars(select(SubmissionScope))
            )
    finally:
        if process is not None:
            process.terminate()
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=10)
        truncate_all(db_engine)
