from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from time import monotonic
from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import OperationalError as DriverOperationalError
from sqlalchemy import Engine, delete, event, func, select, text, update
from sqlalchemy.exc import (
    DBAPIError,
    OperationalError,
    ProgrammingError,
)
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import Role, User
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.parsing import HEADERS, parse_csv
from app.modules.submissions.schemas import UploadContext
from app.modules.submissions.services import persist_candidate
from app.seed import seed_demo, seed_id

FIXTURE = Path(__file__).resolve().parents[3] / "samples" / "synthetic_admissions.csv"


@pytest.mark.parametrize("alias", ["cedar_admin", "demo_officer"])
def test_upload_policy_uses_parser_headers_and_configured_limits(
    client: TestClient,
    application: FastAPI,
    auth_headers: Callable[[str], dict[str, str]],
    alias: str,
) -> None:
    application.state.settings = application.state.settings.model_copy(
        update={
            "upload_max_bytes": 2048,
            "upload_max_rows": 2,
            "upload_receive_timeout_seconds": 7.5,
            "upload_processing_timeout_seconds": 9.5,
        }
    )
    response = client.get(
        "/api/v1/submissions/upload-policy", headers=auth_headers(alias)
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "schema_version": "v1",
        "required_headers": list(HEADERS),
        "encoding": "UTF-8",
        "accepts_utf8_bom": True,
        "max_file_bytes": 2048,
        "max_rows": 2,
        "receive_timeout_seconds": 7.5,
        "processing_timeout_seconds": 9.5,
    }


def test_upload_policy_requires_submission_role(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    path = "/api/v1/submissions/upload-policy"
    assert client.get(path).status_code == 401
    assert client.get(path, headers=auth_headers("demo_manager")).status_code == 403
    manager = seeded_session.scalar(
        select(User).where(User.demo_alias == "demo_manager")
    )
    assert manager is not None
    manager.role = Role.AUTHORIZED_VERIFIER
    seeded_session.flush()
    assert client.get(path, headers=auth_headers("demo_manager")).status_code == 403


@pytest.fixture
def admission_csv() -> bytes:
    return FIXTURE.read_bytes()


def context_fields(
    institution: str = "cedar", programme: str | None = None
) -> dict[str, str]:
    return {
        "institution_id": str(seed_id("institutions", institution)),
        "programme_id": str(
            seed_id("programmes", f"{programme or institution}/DEMO-COMP")
        ),
        "academic_year": "2026-27",
        "schema_version": "v1",
    }


def post_csv(
    client: TestClient,
    headers: dict[str, str],
    data: bytes,
    fields: dict[str, str] | None = None,
) -> str:
    response = client.post(
        "/api/v1/submissions",
        headers=headers,
        data=fields or context_fields(),
        files={"file": ("synthetic.csv", data, "text/csv")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["validation_performed"] is False
    return str(response.json()["id"])


def counts(session: Session) -> tuple[int, int, int]:
    values = tuple(
        session.scalar(select(func.count()).select_from(model)) or 0
        for model in (SubmissionScope, SubmissionBatch, StudentRecordVersion)
    )
    return values[0], values[1], values[2]


def test_upload_persistence_provenance_and_masked_read(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = post_csv(client, headers, admission_csv)
    detail = client.get(f"/api/v1/submissions/{identifier}", headers=headers)
    assert detail.status_code == 200
    metadata = detail.json()
    assert metadata["status"] == "COMPLETED" and metadata["row_count"] == 3
    assert (
        metadata["source"] == "CSV_UPLOAD" and metadata["submission_mode"] == "SNAPSHOT"
    )
    assert metadata["file_size_bytes"] == len(admission_csv)
    assert metadata["base_scope_revision"] == 0 and metadata["base_batch_id"] is None
    assert not metadata["is_current"] and metadata["activated_at"] is None
    assert "activation_eligible" not in metadata and "filename" not in metadata
    assert detail.headers["cache-control"] == "no-store"
    response = client.get(f"/api/v1/submissions/{identifier}/rows", headers=headers)
    rows = response.json()["data"]
    assert len(rows) == 3
    assert [row["source_row_number"] for row in rows] == [2, 3, 4]
    assert all(row["validation_status"] is None for row in rows)
    assert all(row["apaar_verification_status"] == "NOT_CHECKED" for row in rows)
    assert (
        "900000000001" not in response.text
        and "DEMO-MALFORMED-APAAR" not in response.text
    )
    assert (
        "original_json" not in response.text and "normalized_json" not in response.text
    )
    records = seeded_session.scalars(
        select(StudentRecordVersion).order_by(StudentRecordVersion.source_row_number)
    ).all()
    assert records[1].original_json["apaar_id"] == "DEMO-MALFORMED-APAAR"
    assert records[1].normalized_json["enrollment_date"] == "not-a-date"
    assert records[1].enrollment_date is None and records[1].apaar_match_hash is None
    assert counts(seeded_session) == (1, 1, 3)
    scope = seeded_session.scalar(select(SubmissionScope))
    assert scope is not None and scope.current_batch_id is None and scope.revision == 0
    audit = seeded_session.scalar(
        select(AuditEvent).where(AuditEvent.action == "SUBMISSION_UPLOADED")
    )
    assert audit is not None and str(audit.entity_id) == identifier
    assert "apaar" not in str(audit.metadata_redacted).lower()


def test_repeated_uploads_preserve_history_and_never_activate(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
) -> None:
    headers = auth_headers("cedar_admin")
    first = post_csv(client, headers, admission_csv)
    old_payloads = [
        row.original_json.copy()
        for row in seeded_session.scalars(select(StudentRecordVersion))
    ]
    second = post_csv(client, headers, admission_csv)
    assert first != second
    assert counts(seeded_session) == (1, 2, 6)
    history = client.get("/api/v1/submissions?page_size=1", headers=headers).json()
    assert history["pagination"]["total"] == 2 and len(history["data"]) == 1
    assert history["data"][0]["warnings"] == ["DUPLICATE_UPLOAD"]
    assert seeded_session.scalar(select(SubmissionScope.current_batch_id)) is None
    assert seeded_session.scalar(select(SubmissionScope.revision)) == 0
    assert [
        row.original_json
        for row in seeded_session.scalars(
            select(StudentRecordVersion).where(
                StudentRecordVersion.batch_id == UUID(first)
            )
        )
    ] == old_payloads
    assert (
        client.get(f"/api/v1/submissions/{first}", headers=headers).status_code == 200
    )


@pytest.mark.parametrize("row_count,expected_status", [(1000, 201), (1001, 422)])
def test_default_row_limit_at_http_boundary(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
    row_count: int,
    expected_status: int,
) -> None:
    lines = admission_csv.splitlines(keepends=True)
    data = lines[0] + lines[1] * row_count
    response = client.post(
        "/api/v1/submissions",
        headers=auth_headers("cedar_admin"),
        data=context_fields(),
        files={"file": ("synthetic.csv", data, "text/csv")},
    )
    assert response.status_code == expected_status
    if expected_status == 201:
        assert counts(seeded_session) == (1, 1, 1000)
        assert seeded_session.scalar(select(SubmissionScope.current_batch_id)) is None
    else:
        assert response.json()["error"]["code"] == "ROW_LIMIT_EXCEEDED"
        assert counts(seeded_session) == (0, 0, 0)


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_row_payloads_are_database_immutable(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
    operation: str,
) -> None:
    post_csv(client, auth_headers("cedar_admin"), admission_csv)
    with pytest.raises(DBAPIError), seeded_session.begin_nested():
        if operation == "update":
            seeded_session.execute(
                update(StudentRecordVersion).values(full_name_demo="changed")
            )
        else:
            seeded_session.execute(delete(StudentRecordVersion))
    assert counts(seeded_session) == (1, 1, 3)


def test_batch_lifecycle_remains_manageable(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
) -> None:
    identifier = post_csv(client, auth_headers("cedar_admin"), admission_csv)
    seeded_session.execute(
        update(SubmissionBatch)
        .where(SubmissionBatch.id == UUID(identifier))
        .values(status="PROCESSING")
    )
    seeded_session.flush()
    assert counts(seeded_session) == (1, 1, 3)


@pytest.mark.parametrize("suffix", ["", "/rows"])
def test_foreign_batch_and_rows_hidden(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
    suffix: str,
) -> None:
    identifier = post_csv(client, auth_headers("cedar_admin"), admission_csv)
    response = client.get(
        f"/api/v1/submissions/{identifier}{suffix}", headers=auth_headers("maple_admin")
    )
    assert response.status_code == 404


@pytest.mark.parametrize("alias", ["demo_manager", "demo_officer"])
def test_non_admin_cannot_upload(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
    alias: str,
) -> None:
    response = client.post(
        "/api/v1/submissions",
        headers=auth_headers(alias),
        data=context_fields(),
        files={"file": ("synthetic.csv", admission_csv, "text/csv")},
    )
    assert response.status_code == 403


def test_history_is_tenant_scoped_and_officer_can_read(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
) -> None:
    cedar = auth_headers("cedar_admin")
    identifier = post_csv(client, cedar, admission_csv)
    maple = auth_headers("maple_admin")
    assert client.get("/api/v1/submissions", headers=maple).json()["data"] == []
    assert (
        client.get(
            "/api/v1/submissions", headers=auth_headers("demo_manager")
        ).status_code
        == 403
    )
    officer = auth_headers("demo_officer")
    assert (
        client.get(
            f"/api/v1/submissions/{identifier}/rows", headers=officer
        ).status_code
        == 200
    )
    assert (
        client.get("/api/v1/submissions", headers=officer).json()["pagination"]["total"]
        == 1
    )
    foreign = context_fields("maple")["institution_id"]
    assert (
        client.get(
            f"/api/v1/submissions?institution_id={foreign}", headers=cedar
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    "fields", [context_fields("maple"), context_fields("cedar", "maple")]
)
def test_scope_cannot_be_forged(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
    seeded_session: Session,
    fields: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/submissions",
        headers=auth_headers("cedar_admin"),
        data=fields,
        files={"file": ("synthetic.csv", admission_csv, "text/csv")},
    )
    assert response.status_code == 404 and counts(seeded_session) == (0, 0, 0)


@pytest.mark.parametrize(
    "data,expected", [(b"", 400), (b"bad headers", 422), (b"\xff", 400)]
)
def test_rejected_file_creates_no_partial_batch(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    data: bytes,
    expected: int,
) -> None:
    response = client.post(
        "/api/v1/submissions",
        headers=auth_headers("cedar_admin"),
        data=context_fields(),
        files={"file": ("synthetic.csv", data, "text/csv")},
    )
    assert response.status_code == expected
    assert counts(seeded_session) == (0, 0, 0)


def test_real_constraint_failure_rolls_back_and_is_not_outage(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    headers = auth_headers("cedar_admin")

    def break_row(session: Session, flush_context: object, instances: object) -> None:
        for item in session.new:
            if isinstance(item, StudentRecordVersion):
                item.source_row_number = 1

    event.listen(seeded_session, "before_flush", break_row)
    try:
        response = client.post(
            "/api/v1/submissions",
            headers=headers,
            data=context_fields(),
            files={"file": ("synthetic.csv", admission_csv, "text/csv")},
        )
    finally:
        event.remove(seeded_session, "before_flush", break_row)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert counts(seeded_session) == (0, 0, 0)
    assert "900000000001" not in response.text + caplog.text


@pytest.mark.parametrize("kind", ["outage", "programming", "budget"])
def test_write_failures_roll_back(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
    kind: str,
) -> None:
    error = {
        "outage": OperationalError("", {}, DriverOperationalError("sensitive")),
        "programming": ProgrammingError("", {}, Exception("sensitive")),
        "budget": APIError(408, "UPLOAD_TIMEOUT", "Upload processing budget expired"),
    }[kind]
    with patch("app.modules.submissions.services.record_action", side_effect=error):
        response = client.post(
            "/api/v1/submissions",
            headers=auth_headers("cedar_admin"),
            data=context_fields(),
            files={"file": ("synthetic.csv", admission_csv, "text/csv")},
        )
    assert (
        response.status_code == {"outage": 503, "programming": 500, "budget": 408}[kind]
    )
    assert counts(seeded_session) == (0, 0, 0)
    assert "sensitive" not in response.text


def test_processing_budget_before_commit_rolls_back_flushed_rows(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
) -> None:
    checks = 0

    def expire(deadline: float) -> None:
        nonlocal checks
        checks += 1
        if checks == 5:  # Before commit, after all three records have flushed.
            assert (
                seeded_session.scalar(
                    select(func.count()).select_from(StudentRecordVersion)
                )
                == 3
            )
            raise APIError(408, "UPLOAD_TIMEOUT", "Upload processing budget expired")

    with patch("app.modules.submissions.services.check_budget", side_effect=expire):
        response = client.post(
            "/api/v1/submissions",
            headers=auth_headers("cedar_admin"),
            data=context_fields(),
            files={"file": ("synthetic.csv", admission_csv, "text/csv")},
        )
    assert response.status_code == 408 and counts(seeded_session) == (0, 0, 0)


def test_anonymous_and_validation_filter_rejected(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
) -> None:
    assert client.post("/api/v1/submissions").status_code == 401
    assert client.get("/api/v1/submissions").status_code == 401
    headers = auth_headers("cedar_admin")
    identifier = post_csv(client, headers, admission_csv)
    assert (
        client.get(
            f"/api/v1/submissions/{identifier}/rows?status=VALID", headers=headers
        ).status_code
        == 409
    )
    assert (
        client.get(
            f"/api/v1/submissions/{identifier}/rows?page_size=101", headers=headers
        ).status_code
        == 422
    )


def test_metadata_and_logs_do_not_expose_filename_or_identifier(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    headers = auth_headers("cedar_admin")
    response = client.post(
        "/api/v1/submissions",
        headers=headers,
        data=context_fields(),
        files={"file": ("900000000001.csv", admission_csv, "text/csv")},
    )
    assert response.status_code == 201
    identifier = response.json()["id"]
    for path in (
        "/api/v1/submissions",
        f"/api/v1/submissions/{identifier}",
        f"/api/v1/submissions/{identifier}/rows",
    ):
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        assert "900000000001" not in response.text
    assert "900000000001" not in caplog.text


@pytest.mark.parametrize(
    "token,masked", [("1", "*"), ("1234", "****"), ("01234", "*1234")]
)
def test_short_identifiers_never_fully_displayed(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
    token: str,
    masked: str,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = post_csv(
        client, headers, admission_csv.replace(b"900000000001", token.encode())
    )
    rows = client.get(f"/api/v1/submissions/{identifier}/rows", headers=headers).json()[
        "data"
    ]
    assert rows[0]["apaar_id_masked"] == masked


def test_row_scope_contradictions_remain_unvalidated_candidate_data(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
) -> None:
    data = admission_csv.replace(
        b"2026-27,DEMO-COMP,REGULAR,ACTIVE", b"bad-year,other,unknown,unknown"
    )
    headers = auth_headers("cedar_admin")
    identifier = post_csv(client, headers, data)
    row = seeded_session.scalar(
        select(StudentRecordVersion).where(StudentRecordVersion.source_row_number == 2)
    )
    assert row is not None
    assert (
        row.academic_year == "2026-27"
        and row.normalized_json["academic_year"] == "bad-year"
    )
    assert row.admission_category == "UNKNOWN" and row.enrollment_status == "UNKNOWN"
    response = client.get(f"/api/v1/submissions/{identifier}/rows", headers=headers)
    assert response.json()["data"][0]["validation_status"] is None


def test_rejected_correction_does_not_modify_existing_candidate(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    admission_csv: bytes,
) -> None:
    headers = auth_headers("cedar_admin")
    identifier = post_csv(client, headers, admission_csv)
    response = client.post(
        "/api/v1/submissions",
        headers=headers,
        data=context_fields(),
        files={"file": ("synthetic.csv", b"broken", "text/csv")},
    )
    assert response.status_code == 422 and counts(seeded_session) == (1, 1, 3)
    assert (
        client.get(f"/api/v1/submissions/{identifier}/rows", headers=headers).json()[
            "pagination"
        ]["total"]
        == 3
    )


@pytest.mark.parametrize("extra", ["role", "institution_id"])
def test_duplicate_or_extra_multipart_fields_rejected(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    admission_csv: bytes,
    seeded_session: Session,
    extra: str,
) -> None:
    fields = context_fields()
    parts = [(key, (None, value)) for key, value in fields.items()]
    parts += [(extra, (None, "forged"))]
    # Build bytes with the same wire helper used by the HTTP client, without
    # allowing a dict to erase duplicate field names.
    import httpx2

    body = httpx2.Request(
        "POST",
        "http://localhost",
        files=parts + [("file", ("synthetic.csv", admission_csv, "text/csv"))],
    )
    response = client.post(
        "/api/v1/submissions",
        headers={
            **auth_headers("cedar_admin"),
            "Content-Type": body.headers["content-type"],
        },
        content=body.read(),
    )
    assert response.status_code == 422 and counts(seeded_session) == (0, 0, 0)


def test_concurrent_uploads_share_scope_without_overwriting(
    db_engine: Engine,
    demo_settings: Settings,
    admission_csv: bytes,
) -> None:
    # This test needs genuinely independent committed transactions, not a shared
    # rollback fixture. Cleanup is restricted to this fresh throwaway database.
    assert (db_engine.url.database or "").startswith("sih26263_m1_test_")
    barrier = Barrier(2)
    try:
        with Session(db_engine) as session, session.begin():
            seed_demo(session, demo_settings)

        def upload_candidate() -> UUID:
            with Session(db_engine, expire_on_commit=False) as session:
                user = session.get(User, seed_id("users", "cedar_admin"))
                assert user is not None
                context = UploadContext.model_validate(context_fields())
                deadline = monotonic() + 30
                rows = parse_csv(admission_csv, demo_settings, deadline)
                barrier.wait(timeout=10)
                return persist_candidate(
                    session,
                    user,
                    context,
                    admission_csv,
                    "synthetic.csv",
                    rows,
                    deadline,
                ).id

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(upload_candidate) for _ in range(2)]
            ids = [future.result(timeout=30) for future in futures]
        assert len(set(ids)) == 2
        with Session(db_engine) as session:
            assert counts(session) == (1, 2, 6)
            scope = session.scalar(select(SubmissionScope))
            assert (
                scope is not None
                and scope.current_batch_id is None
                and scope.revision == 0
            )
    finally:
        with db_engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE submission_reviews, apaar_verifications, "
                    "case_events, case_records, review_cases, "
                    "validation_findings, "
                    "validation_runs, "
                    "student_record_versions, submission_batches, "
                    "submission_scopes, "
                    "audit_events, users, intake_rules, programmes, institutions"
                )
            )
