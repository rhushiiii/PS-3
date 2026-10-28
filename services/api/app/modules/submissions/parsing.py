"""Bounded file parsing; intentionally no student or regulatory validation."""

import asyncio
import csv
import io
import re
import sys
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import date
from time import monotonic

from fastapi import Request
from pydantic import ValidationError
from starlette.datastructures import FormData, UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.requests import ClientDisconnect

from app.core.config import Settings
from app.core.http import APIError
from app.modules.submissions.schemas import UploadContext

HEADERS = (
    "college_student_id",
    "student_name",
    "apaar_id",
    "academic_year",
    "programme_code",
    "admission_category",
    "enrollment_status",
    "enrollment_date",
)
FORM_FIELDS = {
    "institution_id",
    "programme_id",
    "academic_year",
    "schema_version",
    "file",
}
# Actual request bytes are bounded first. Avoid an unrelated global 128 KiB cell cap.
csv.field_size_limit(sys.maxsize)


def check_budget(deadline: float) -> None:
    if monotonic() >= deadline:
        raise APIError(408, "UPLOAD_TIMEOUT", "Upload processing budget expired")


@dataclass(frozen=True, repr=False)
class ParsedRow:
    number: int
    original: dict[str, str]
    normalized: dict[str, str]
    enrollment_date: date | None


def parse_csv(data: bytes, settings: Settings, deadline: float) -> list[ParsedRow]:
    if not data:
        raise APIError(400, "INVALID_CSV", "CSV has no data records")
    if len(data) > settings.upload_max_bytes:
        raise APIError(413, "FILE_TOO_LARGE", "File exceeds configured limit")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise APIError(400, "INVALID_CSV", "CSV must use UTF-8") from None
    if "\x00" in text:
        raise APIError(400, "INVALID_CSV", "Invalid CSV content")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    rows: list[ParsedRow] = []
    try:
        if tuple(next(reader, ())) != HEADERS:
            raise APIError(422, "SCHEMA_MISMATCH", "CSV headers must match v1")
        for number, values in enumerate(reader, start=2):
            check_budget(deadline)
            if len(values) != len(HEADERS):
                raise APIError(
                    400, "INVALID_CSV", "CSV record column count differs from v1"
                )
            if len(rows) >= settings.upload_max_rows:
                raise APIError(
                    422, "ROW_LIMIT_EXCEEDED", "CSV exceeds configured record limit"
                )
            original = dict(zip(HEADERS, values, strict=True))
            normalized = {key: value.strip() for key, value in original.items()}
            for key in ("programme_code", "admission_category", "enrollment_status"):
                normalized[key] = normalized[key].upper()
            parsed_date = None
            if re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}", normalized["enrollment_date"]
            ):
                try:
                    parsed_date = date.fromisoformat(normalized["enrollment_date"])
                except ValueError:
                    pass
            rows.append(ParsedRow(number, original, normalized, parsed_date))
    except csv.Error:
        raise APIError(400, "INVALID_CSV", "Malformed CSV") from None
    if not rows:
        raise APIError(400, "INVALID_CSV", "CSV has no data records")
    check_budget(deadline)
    return rows


class CompleteMultipartParser(MultiPartParser):
    """Detect truncation while retaining Starlette's exception cleanup."""

    complete = False

    def on_end(self) -> None:
        self.complete = True


async def read_multipart(
    request: Request, settings: Settings
) -> tuple[UploadContext, bytes, str, float]:
    limit = settings.upload_max_bytes + 64 * 1024
    length = request.headers.get("content-length")
    if length is not None:
        try:
            size = int(length)
            if size < 0:
                raise ValueError
            if size > limit:
                raise APIError(
                    413, "FILE_TOO_LARGE", "Request exceeds configured limit"
                )
        except ValueError:
            raise APIError(400, "INVALID_CSV", "Invalid request length") from None
    if (
        request.headers.get("content-type", "").split(";")[0].strip().lower()
        != "multipart/form-data"
    ):
        raise APIError(400, "INVALID_CSV", "Expected multipart upload")
    body = bytearray()
    try:
        async with asyncio.timeout(settings.upload_receive_timeout_seconds):
            async for chunk in request.stream():
                if len(body) + len(chunk) > limit:
                    raise APIError(
                        413, "FILE_TOO_LARGE", "Request exceeds configured limit"
                    )
                body.extend(chunk)
    except TimeoutError:
        raise APIError(408, "UPLOAD_TIMEOUT", "Upload receive budget expired") from None
    except ClientDisconnect:
        raise APIError(400, "INVALID_CSV", "Upload disconnected") from None
    deadline = monotonic() + settings.upload_processing_timeout_seconds

    async def stream() -> AsyncGenerator[bytes]:
        yield bytes(body)
        # Raising inside parse makes Starlette close even unfinished file parts.
        if not parser.complete:
            raise MultiPartException("Incomplete multipart body")

    parser = CompleteMultipartParser(
        request.headers, stream(), max_files=1, max_fields=4, max_part_size=4096
    )
    # Within the already bounded body no file rolls out to the OS temporary folder.
    parser.spool_max_size = limit + 1
    form: FormData | None = None
    try:
        form = await parser.parse()
        check_budget(deadline)
        items = form.multi_items()
        keys = [key for key, _ in items]
        if set(keys) - FORM_FIELDS or len(keys) != len(set(keys)):
            raise APIError(
                422, "INVALID_REQUEST", "Unexpected or duplicate upload fields"
            )
        values = {key: value for key, value in items if key != "file"}
        try:
            context = UploadContext.model_validate(values)
        except ValidationError:
            raise APIError(422, "INVALID_REQUEST", "Invalid upload context") from None
        file = form.get("file")
        if not isinstance(file, UploadFile) or not file.filename:
            raise APIError(422, "INVALID_REQUEST", "One CSV file is required")
        if len(file.filename) > 255 or any(ord(char) < 32 for char in file.filename):
            raise APIError(422, "INVALID_REQUEST", "Invalid file metadata")
        if (file.content_type or "").split(";")[0].strip().lower() not in {
            "text/csv",
            "application/csv",
            "text/plain",
            "application/octet-stream",
            "application/vnd.ms-excel",
        }:
            raise APIError(400, "INVALID_CSV", "Unsupported file type")
        data = await file.read(settings.upload_max_bytes + 1)
        if len(data) > settings.upload_max_bytes:
            raise APIError(413, "FILE_TOO_LARGE", "File exceeds configured limit")
        check_budget(deadline)
        return context, data, file.filename, deadline
    except MultiPartException as exc:
        if exc.message.startswith(
            ("Too many fields", "Too many files", "Part exceeded")
        ):
            raise APIError(422, "INVALID_REQUEST", "Invalid multipart fields") from None
        raise APIError(400, "INVALID_CSV", "Malformed multipart upload") from None
    finally:
        if form is not None:
            await form.close()
