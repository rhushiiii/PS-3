import io
import zipfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from threading import Barrier
from time import monotonic
from typing import Any
from uuid import UUID

import pytest
from conftest import counts, truncate_all
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
)
from app.modules.submissions.parsing import HEADERS, parse_csv, parse_xlsx
from app.modules.submissions.schemas import UploadContext
from app.modules.submissions.services import (
    idempotent_replay,
    persist_candidate,
    upload_fingerprint,
)
from app.seed import seed_demo, seed_id

FIXTURE = Path(__file__).resolve().parents[3] / "samples" / "synthetic_admissions.csv"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
KEY = "synthetic-key-0001"


def context_fields(institution: str = "cedar") -> dict[str, str]:
    return {
        "institution_id": str(seed_id("institutions", institution)),
        "programme_id": str(seed_id("programmes", f"{institution}/DEMO-COMP")),
        "academic_year": "2026-27",
        "schema_version": "v1",
    }


def workbook_bytes(rows: list[list[Any]], headers: tuple[str, ...] = HEADERS) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(list(headers))
    for row in rows:
        sheet.append(row)
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def sample_rows() -> list[list[Any]]:
    return [
        [
            "DEMO-STUDENT-001",
            "Synthetic Learner One",
            900000000001,
            "2026-27",
            "DEMO-COMP",
            "REGULAR",
            "ACTIVE",
            date(2026, 7, 1),
        ],
        [
            "DEMO-STUDENT-002",
            "Synthetic Learner Two",
            "DEMO-MALFORMED-APAAR",
            "2026-27",
            "DEMO-COMP",
            "NRI",
            "ACTIVE",
            "not-a-date",
        ],
        [
            "DEMO-STUDENT-003",
            None,
            "000000000003",
            "2026-27",
            "DEMO-COMP",
            "SUPERNUMERARY",
            "WITHDRAWN",
            datetime(2026, 7, 3),
        ],
    ]


def post_file(
    client: TestClient,
    headers: dict[str, str],
    data: bytes,
    *,
    name: str = "synthetic.xlsx",
    content_type: str = XLSX_TYPE,
    fields: dict[str, str] | None = None,
    key: str | None = None,
) -> Any:
    extra = {"Idempotency-Key": key} if key is not None else {}
    return client.post(
        "/api/v1/submissions",
        headers={**headers, **extra},
        data=fields or context_fields(),
        files={"file": (name, data, content_type)},
    )


def test_policy_lists_accepted_formats(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    response = client.get(
        "/api/v1/submissions/upload-policy", headers=auth_headers("cedar_admin")
    )
    assert response.json()["accepted_formats"] == ["csv", "xlsx"]


def test_xlsx_rows_equal_csv_equivalent(settings: Settings) -> None:
    deadline = monotonic() + 30
    expected = parse_csv(FIXTURE.read_bytes(), settings, deadline)
    actual = parse_xlsx(workbook_bytes(sample_rows()), settings, deadline)
    assert [
        (r.number, r.original, r.normalized, r.enrollment_date) for r in actual
    ] == [(r.number, r.original, r.normalized, r.enrollment_date) for r in expected]


def test_xlsx_upload_http_provenance(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    response = post_file(client, headers, workbook_bytes(sample_rows()))
    assert response.status_code == 201, response.text
    detail = client.get(f"/api/v1/submissions/{response.json()['id']}", headers=headers)
    assert detail.json()["source"] == "XLSX_UPLOAD" and detail.json()["row_count"] == 3
    assert counts(seeded_session) == (1, 1, 3)


def test_wrong_headers_rejected(settings: Settings) -> None:
    data = workbook_bytes(sample_rows(), headers=(*HEADERS[:-1], "other"))
    with pytest.raises(APIError) as caught:
        parse_xlsx(data, settings, monotonic() + 30)
    assert caught.value.status_code == 422 and caught.value.code == "SCHEMA_MISMATCH"


def test_formula_cells_are_not_evaluated(settings: Settings) -> None:
    rows = sample_rows()
    rows[0][1] = "=1+1"
    parsed = parse_xlsx(workbook_bytes(rows), settings, monotonic() + 30)
    assert parsed[0].original["student_name"] == ""


def with_member(data: bytes, name: str, content: bytes) -> bytes:
    stream = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(data)) as source,
        zipfile.ZipFile(stream, "w") as target,
    ):
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename == "[Content_Types].xml" and name == "macro":
                payload = payload.replace(
                    b"sheet.main+xml", b"sheet.macroEnabled.main+xml"
                )
            target.writestr(info.filename, payload)
        if name != "macro":
            target.writestr(name, content)
    return stream.getvalue()


@pytest.mark.parametrize(
    ("filename", "make"),
    [
        ("synthetic.xlsx", lambda good: b"not a zip at all"),
        ("synthetic.xlsx", lambda good: good[: len(good) // 2]),
        ("synthetic.xlsx", lambda good: b"PK\x03\x04" + b"garbage" * 20),
        ("synthetic.xlsx", lambda good: with_member(good, "macro", b"")),
        ("synthetic.xlsx", lambda good: with_member(good, "xl/vbaProject.bin", b"x")),
        ("synthetic.xlsx", lambda good: b"\xd0\xcf\x11\xe0" + b"\x00" * 64),
        ("synthetic.xlsm", lambda good: good),
        ("synthetic.csv", lambda good: good),
        (
            "synthetic.xlsx",
            lambda good: b"PK\x05\x06" + b"\0" * 18,
        ),
    ],
)
def test_invalid_workbooks_rejected_without_batch(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    filename: str,
    make: Callable[[bytes], bytes],
) -> None:
    good = workbook_bytes(sample_rows())
    response = post_file(client, auth_headers("cedar_admin"), make(good), name=filename)
    assert 400 <= response.status_code < 500, response.text
    assert counts(seeded_session) == (0, 0, 0)


def test_xlsx_extension_with_csv_content_rejected(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    response = post_file(
        client, auth_headers("cedar_admin"), FIXTURE.read_bytes(), name="a.xlsx"
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_XLSX"
    assert counts(seeded_session) == (0, 0, 0)


def test_row_limit_and_uncompressed_cap(settings: Settings) -> None:
    limited = settings.model_copy(update={"upload_max_rows": 2})
    with pytest.raises(APIError) as caught:
        parse_xlsx(workbook_bytes(sample_rows()), limited, monotonic() + 30)
    assert caught.value.status_code == 422
    assert caught.value.code == "ROW_LIMIT_EXCEEDED"
    exact = limited.model_copy(update={"upload_max_rows": 3})
    assert len(parse_xlsx(workbook_bytes(sample_rows()), exact, monotonic() + 30)) == 3
    bomb = with_member(workbook_bytes(sample_rows()), "xl/pad.xml", b"0" * (60 << 20))
    huge = settings.model_copy(update={"upload_max_bytes": 100 << 20})
    with pytest.raises(APIError) as expansion:
        parse_xlsx(bomb, huge, monotonic() + 30)
    assert expansion.value.status_code == 413


def audits(session: Session) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "SUBMISSION_UPLOADED")
        )
        or 0
    )


def test_idempotent_replay_returns_original(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    data = FIXTURE.read_bytes()
    first = post_file(
        client, headers, data, name="a.csv", content_type="text/csv", key=KEY
    )
    second = post_file(
        client, headers, data, name="b.csv", content_type="text/csv", key=KEY
    )
    assert first.status_code == 201 and second.status_code == 200
    assert second.json() == first.json()
    assert second.headers["idempotent-replayed"] == "true"
    assert counts(seeded_session) == (1, 1, 3) and audits(seeded_session) == 1
    # Without the header every accepted upload remains a distinct candidate.
    third = post_file(client, headers, data, name="a.csv", content_type="text/csv")
    assert third.status_code == 201 and third.json()["id"] != first.json()["id"]
    assert counts(seeded_session)[1] == 2


def test_key_reuse_with_different_input_conflicts(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    data = FIXTURE.read_bytes()
    kwargs: dict[str, Any] = {"name": "a.csv", "content_type": "text/csv", "key": KEY}
    assert post_file(client, headers, data, **kwargs).status_code == 201
    other = post_file(client, headers, data + b"\n", **kwargs)
    assert other.status_code == 409
    assert other.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert counts(seeded_session)[1] == 1 and audits(seeded_session) == 1


def test_key_is_scoped_per_institution(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    data = FIXTURE.read_bytes()
    kwargs: dict[str, Any] = {"name": "a.csv", "content_type": "text/csv", "key": KEY}
    first = post_file(client, auth_headers("cedar_admin"), data, **kwargs)
    second = post_file(
        client,
        auth_headers("maple_admin"),
        data,
        fields=context_fields("maple"),
        **kwargs,
    )
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert counts(seeded_session)[1] == 2


@pytest.mark.parametrize(
    "key", ["short", "x" * 129, "bad key with spaces", "bad/key/chars!"]
)
def test_invalid_idempotency_key_rejected(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    key: str,
) -> None:
    response = client.post(
        "/api/v1/submissions",
        headers={
            **auth_headers("cedar_admin"),
            "Idempotency-Key": key,
        },
        data=context_fields(),
        files={"file": ("a.csv", FIXTURE.read_bytes(), "text/csv")},
    )
    assert response.status_code == 422 and counts(seeded_session) == (0, 0, 0)
    assert key not in response.text


def test_openapi_documents_key_and_replay(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/submissions"][
        "post"
    ]
    assert any(p["name"] == "idempotency-key" for p in operation["parameters"])
    assert "200" in operation["responses"]


def test_concurrent_identical_keyed_uploads_create_one_batch(
    db_engine: Engine, demo_settings: Settings
) -> None:
    assert (db_engine.url.database or "").startswith("sih26263_m1_test_")
    barrier = Barrier(2)
    data = FIXTURE.read_bytes()
    try:
        with Session(db_engine) as session, session.begin():
            seed_demo(session, demo_settings)

        def upload_candidate() -> UUID:
            with Session(db_engine, expire_on_commit=False) as session:
                user = session.get(User, seed_id("users", "cedar_admin"))
                assert user is not None
                context = UploadContext.model_validate(context_fields())
                deadline = monotonic() + 30
                rows = parse_csv(data, demo_settings, deadline)
                idempotency = (KEY, upload_fingerprint(data, context))
                barrier.wait(timeout=10)
                try:
                    return persist_candidate(
                        session,
                        user,
                        context,
                        data,
                        "a.csv",
                        rows,
                        deadline,
                        idempotency=idempotency,
                    ).id
                except IntegrityError:
                    replay = idempotent_replay(
                        session, context.institution_id, *idempotency
                    )
                    assert replay is not None
                    return replay.id

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(upload_candidate) for _ in range(2)]
            ids = [future.result(timeout=30) for future in futures]
        assert len(set(ids)) == 1
        with Session(db_engine) as session:
            assert counts(session)[1] == 1 and audits(session) == 1
            assert (
                session.scalar(select(func.count()).select_from(StudentRecordVersion))
                == 3
            )
            assert session.scalar(select(SubmissionBatch.idempotency_key)) == KEY
    finally:
        truncate_all(db_engine)
