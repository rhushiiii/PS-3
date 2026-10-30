"""Idempotency-Key rules shared by the upload and verification APIs."""

from collections.abc import Sequence

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.http import APIError

IDEMPOTENCY_KEY_PATTERN = r"^[A-Za-z0-9._:-]{8,128}$"


def check_fingerprint(stored: str | None, new: str, message: str) -> None:
    """Raise the shared 409 when a replayed key carried a different request."""
    if stored != new:
        raise APIError(409, "IDEMPOTENCY_KEY_REUSED", message)


def find_replay[Model: Base](
    session: Session,
    model: type[Model],
    key_filter: Sequence[ColumnElement[bool]],
    *,
    fingerprint_attr: str,
    fingerprint: str,
    message: str,
) -> Model | None:
    """The row a replayed key produced, or None; 409 if the key carried new input."""
    existing = session.scalar(select(model).where(*key_filter))
    if existing is None:
        return None
    check_fingerprint(getattr(existing, fingerprint_attr), fingerprint, message)
    return existing
