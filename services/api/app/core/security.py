"""Request-wide hardening: security headers, body-size cap and log redaction."""

import logging
import re
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.http import APIError
from app.modules.audit.services import APAAR_RUN, MASK

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Resource-Policy": "same-site",
}


class SecurityHeadersMiddleware:
    """Pure ASGI so it also covers streaming and error responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        is_api = str(scope["path"]).startswith("/api/")

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {name.lower() for name, _ in message["headers"]}
                added = dict(SECURITY_HEADERS)
                if is_api and b"cache-control" not in existing:
                    added["Cache-Control"] = "no-store"
                message["headers"] = [
                    *(
                        (name, value)
                        for name, value in message["headers"]
                        if name.lower().decode() not in {h.lower() for h in added}
                    ),
                    *((k.lower().encode(), v.encode()) for k, v in added.items()),
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)


class BodyLimitMiddleware:
    """Caps bytes actually received (not just the declared Content-Length).

    The error is raised from ``receive`` inside the route, so it passes through the
    shared APIError handler (same envelope and request ID). It must therefore sit
    innermost, below the HTTP middleware. Routes that never read a body are not
    affected. ``exempt`` (method, path) pairs keep their own, larger bounds.
    """

    def __init__(
        self, app: ASGIApp, max_bytes: int, exempt: set[tuple[str, str]]
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.exempt = exempt

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or (scope["method"], scope["path"]) in self.exempt:
            await self.app(scope, receive, send)
            return
        received = 0

        def too_large() -> APIError:
            return APIError(413, "REQUEST_TOO_LARGE", "Request body too large")

        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > self.max_bytes:

            async def refuse(*_: Any) -> Message:
                raise too_large()

            await self.app(scope, refuse, send)
            return

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise too_large()
            return message

        await self.app(scope, limited_receive, send)


# ----------------------------------------------------------------- log redaction

BEARER = re.compile(r"(?i)\bBearer\s+[^\s,;'\"]+")
JWS_LIKE = re.compile(r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")
IDEMPOTENCY = re.compile(r"(?i)(idempotency-key['\"]?\s*[:=]\s*['\"]?)[^\s,;'\"}\])]+")


def redact_text(text: str) -> str:
    text = BEARER.sub(f"Bearer {MASK}", text)
    text = JWS_LIKE.sub(MASK, text)
    text = IDEMPOTENCY.sub(rf"\1{MASK}", text)
    return APAAR_RUN.sub(MASK, text)


class RedactingFilter(logging.Filter):
    """Masks identifiers and credentials in the final message and traceback."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except (TypeError, ValueError):
            message = str(record.msg)
        record.msg = redact_text(message)
        record.args = None
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = redact_text(record.exc_text)
        return True


REDACTED_LOGGERS = ("", "uvicorn", "uvicorn.error", "uvicorn.access")


def install_log_redaction() -> None:
    """Idempotent. Filters on loggers and their handlers, plus a record factory.

    Python does not run an ancestor logger's filters for child-logger records, and
    handlers may be attached later, so the factory is the guarantee: every record
    is masked as it is created.
    """
    redactor = RedactingFilter()
    for name in REDACTED_LOGGERS:
        logger = logging.getLogger(name)
        if not any(isinstance(f, RedactingFilter) for f in logger.filters):
            logger.addFilter(redactor)
        for handler in logger.handlers:
            if not any(isinstance(f, RedactingFilter) for f in handler.filters):
                handler.addFilter(redactor)
    current = logging.getLogRecordFactory()
    if not getattr(current, "redacting", False):

        def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = current(*args, **kwargs)
            redactor.filter(record)
            return record

        factory.redacting = True  # type: ignore[attr-defined]
        logging.setLogRecordFactory(factory)
