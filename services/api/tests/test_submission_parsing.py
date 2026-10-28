import asyncio
import csv
import io
from collections.abc import Iterator
from tempfile import SpooledTemporaryFile
from time import monotonic
from unittest.mock import patch

import pytest
from starlette.requests import Request
from starlette.types import Message, Scope

from app.core.config import Settings
from app.core.http import APIError
from app.modules.submissions.parsing import HEADERS, parse_csv, read_multipart
from app.seed import seed_id


def csv_bytes(rows: list[list[str]], headers: tuple[str, ...] = HEADERS) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode()


def sample_row() -> list[str]:
    return [
        " 0001 ",
        " Synthetic Learner ",
        " DEMO-MALFORMED-ID ",
        "2026-27",
        "demo-comp",
        "regular",
        "active",
        "not-a-date",
    ]


def test_normalization_is_conservative(settings: Settings) -> None:
    data = csv_bytes([sample_row()])
    row = parse_csv(data, settings, monotonic() + 30)[0]
    assert row.original["college_student_id"] == " 0001 "
    assert row.normalized["college_student_id"] == "0001"
    assert row.original["apaar_id"] == " DEMO-MALFORMED-ID "
    assert row.normalized["apaar_id"] == "DEMO-MALFORMED-ID"
    assert row.normalized["admission_category"] == "REGULAR"
    assert row.normalized["enrollment_date"] == "not-a-date"
    assert row.enrollment_date is None


def test_logical_record_numbers_preserve_multiline_values(settings: Settings) -> None:
    first = sample_row()
    first[1] = 'Synthetic\r\nLearner, "One"'
    rows = parse_csv(
        b"\xef\xbb\xbf" + csv_bytes([first, sample_row()]), settings, monotonic() + 30
    )
    assert [row.number for row in rows] == [2, 3]
    assert rows[0].original["student_name"] == 'Synthetic\r\nLearner, "One"'


@pytest.mark.parametrize("value", ["", "2026-02-30", "20260701", "07/01/2026"])
def test_unknown_dates_are_preserved(settings: Settings, value: str) -> None:
    row = sample_row()
    row[-1] = value
    result = parse_csv(csv_bytes([row]), settings, monotonic() + 30)[0]
    assert result.normalized["enrollment_date"] == value
    assert result.enrollment_date is None


def test_empty_and_unknown_student_values_are_not_validated(settings: Settings) -> None:
    row = sample_row()
    row[3:7] = ["wrong-year", "other-programme", "unknown", "unknown"]
    result = parse_csv(csv_bytes([row, [""] * 8]), settings, monotonic() + 30)
    assert len(result) == 2
    assert result[0].normalized["academic_year"] == "wrong-year"
    assert result[0].normalized["enrollment_status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "data,code",
    [
        (b"", "INVALID_CSV"),
        (csv_bytes([]), "INVALID_CSV"),
        (b"\xff", "INVALID_CSV"),
        (csv_bytes([sample_row()]) + b"\x00", "INVALID_CSV"),
        (csv_bytes([sample_row()]) + b'"unterminated', "INVALID_CSV"),
        (csv_bytes([sample_row()]) + b"\r\n", "INVALID_CSV"),
        (csv_bytes([["too", "few"]]), "INVALID_CSV"),
        (csv_bytes([sample_row()], headers=HEADERS[:-1]), "SCHEMA_MISMATCH"),
        (
            csv_bytes([sample_row()], headers=tuple(reversed(HEADERS))),
            "SCHEMA_MISMATCH",
        ),
        (csv_bytes([sample_row()], headers=(HEADERS[0],) * 8), "SCHEMA_MISMATCH"),
    ],
)
def test_csv_processing_failures_are_redacted(
    settings: Settings, data: bytes, code: str
) -> None:
    with pytest.raises(APIError) as failure:
        parse_csv(data, settings, monotonic() + 30)
    assert failure.value.code == code
    assert "DEMO-MALFORMED-ID" not in str(failure.value.detail)


def test_actual_row_byte_and_budget_limits(settings: Settings) -> None:
    one = csv_bytes([sample_row()])
    for config, data, deadline, code in [
        (
            settings.model_copy(update={"upload_max_rows": 1}),
            csv_bytes([sample_row()] * 2),
            monotonic() + 30,
            "ROW_LIMIT_EXCEEDED",
        ),
        (
            settings.model_copy(update={"upload_max_bytes": len(one) - 1}),
            one,
            monotonic() + 30,
            "FILE_TOO_LARGE",
        ),
        (settings, one, monotonic() - 1, "UPLOAD_TIMEOUT"),
    ]:
        with pytest.raises(APIError) as failure:
            parse_csv(data, config, deadline)
        assert failure.value.code == code
    exact = settings.model_copy(
        update={"upload_max_bytes": len(one), "upload_max_rows": 1}
    )
    assert len(parse_csv(one, exact, monotonic() + 30)) == 1


def test_large_cell_within_file_budget_is_preserved(settings: Settings) -> None:
    row = sample_row()
    row[1] = "X" * 140000
    assert (
        len(
            parse_csv(csv_bytes([row]), settings, monotonic() + 30)[0].original[
                "student_name"
            ]
        )
        == 140000
    )


def multipart_body(data: bytes, *, extra: bytes = b"") -> bytes:
    fields = {
        "institution_id": str(seed_id("institutions", "cedar")),
        "programme_id": str(seed_id("programmes", "cedar/DEMO-COMP")),
        "academic_year": "2026-27",
        "schema_version": "v1",
    }
    body = b"".join(
        (
            f'--demo-boundary\r\nContent-Disposition: form-data; name="{key}"'
            f"\r\n\r\n{value}\r\n"
        ).encode()
        for key, value in fields.items()
    )
    return (
        body
        + (
            b"--demo-boundary\r\nContent-Disposition: form-data; "
            b'name="file"; filename="synthetic.csv"\r\n'
            b"Content-Type: text/csv\r\n\r\n"
        )
        + data
        + b"\r\n"
        + extra
        + b"--demo-boundary--\r\n"
    )


async def receive_upload(
    body: bytes,
    settings: Settings,
    *,
    delay: float = 0,
    disconnect: bool = False,
    content_length: str | None = None,
    chunk_size: int | None = None,
) -> tuple[bytes, str]:
    headers = [(b"content-type", b"multipart/form-data; boundary=demo-boundary")]
    if content_length is not None:
        headers.append((b"content-length", content_length.encode()))
    scope: Scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/submissions",
        "headers": headers,
        "query_string": b"",
        "scheme": "http",
    }
    offset = 0

    async def receive() -> Message:
        nonlocal offset
        await asyncio.sleep(delay)
        if disconnect or offset >= len(body):
            return {"type": "http.disconnect"}
        chunk = body[offset : offset + (chunk_size or len(body))]
        offset += len(chunk)
        return {"type": "http.request", "body": chunk, "more_body": offset < len(body)}

    _, data, filename, _ = await read_multipart(Request(scope, receive), settings)
    return data, filename


@pytest.fixture
def upload_files() -> Iterator[list[SpooledTemporaryFile[bytes]]]:
    files: list[SpooledTemporaryFile[bytes]] = []

    def tracked_file(*, max_size: int) -> SpooledTemporaryFile[bytes]:
        file: SpooledTemporaryFile[bytes] = SpooledTemporaryFile(max_size=max_size)
        files.append(file)
        return file

    with patch("starlette.formparsers.SpooledTemporaryFile", side_effect=tracked_file):
        yield files
    assert all(file.closed for file in files)


def test_multipart_resources_closed_on_success(
    settings: Settings, upload_files: list[SpooledTemporaryFile[bytes]]
) -> None:
    data = csv_bytes([sample_row()])
    assert asyncio.run(receive_upload(multipart_body(data), settings))[0] == data
    assert len(upload_files) == 1 and upload_files[0].closed
    assert getattr(upload_files[0], "_rolled", None) is False


@pytest.mark.parametrize(
    "mode",
    ["truncated", "bad_context", "extra_file", "file_limit", "processing_budget"],
)
def test_multipart_failure_cleanup(
    settings: Settings, upload_files: list[SpooledTemporaryFile[bytes]], mode: str
) -> None:
    data = csv_bytes([sample_row()])
    body = multipart_body(data)
    config = settings
    expected = {
        "truncated": 400,
        "bad_context": 422,
        "extra_file": 422,
        "file_limit": 413,
        "processing_budget": 408,
    }[mode]
    if mode == "truncated":
        body = body[: body.rfind(b"--demo-boundary--")]
    elif mode == "bad_context":
        body = body.replace(b"2026-27", b"invalid-year", 1)
    elif mode == "extra_file":
        extra = (
            b"--demo-boundary\r\nContent-Disposition: form-data; "
            b'name="file"; filename="second.csv"\r\n\r\nX\r\n'
        )
        body = multipart_body(data, extra=extra)
    elif mode == "file_limit":
        config = settings.model_copy(update={"upload_max_bytes": len(data) - 1})
    else:
        config = settings.model_copy(update={"upload_processing_timeout_seconds": 1e-9})
    with pytest.raises(APIError) as failure:
        asyncio.run(receive_upload(body, config))
    assert failure.value.status_code == expected
    assert upload_files and all(file.closed for file in upload_files)


@pytest.mark.parametrize("length", [None, "1", "99999999"])
def test_total_body_limit_before_multipart(
    settings: Settings,
    upload_files: list[SpooledTemporaryFile[bytes]],
    length: str | None,
) -> None:
    config = settings.model_copy(update={"upload_max_bytes": 1})
    with pytest.raises(APIError) as failure:
        asyncio.run(
            receive_upload(
                b"X" * 66000, config, content_length=length, chunk_size=20000
            )
        )
    assert failure.value.status_code == 413
    assert upload_files == []


def test_actual_receive_timeout_and_disconnect(settings: Settings) -> None:
    config = settings.model_copy(update={"upload_receive_timeout_seconds": 0.005})
    with pytest.raises(APIError) as failure:
        asyncio.run(receive_upload(b"", config, delay=0.03))
    assert failure.value.status_code == 408
    with pytest.raises(APIError) as failure:
        asyncio.run(receive_upload(b"", settings, disconnect=True))
    assert failure.value.status_code == 400
