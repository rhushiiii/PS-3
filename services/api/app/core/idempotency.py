"""Idempotency-Key rules shared by the upload and verification APIs."""

from app.core.http import APIError

IDEMPOTENCY_KEY_PATTERN = r"^[A-Za-z0-9._:-]{8,128}$"


def check_fingerprint(stored: str | None, new: str, message: str) -> None:
    """Raise the shared 409 when a replayed key carried a different request."""
    if stored != new:
        raise APIError(409, "IDEMPOTENCY_KEY_REUSED", message)
