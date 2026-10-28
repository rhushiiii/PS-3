"""One shared error envelope and request ID for the API."""

from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from psycopg import OperationalError as DriverOperationalError
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code, message, headers)
        self.code = code


def database_unavailable(exc: SQLAlchemyError) -> bool:
    if isinstance(exc, PoolTimeoutError):
        return True
    if not isinstance(exc, DBAPIError):
        return False
    state = getattr(exc.orig, "sqlstate", None)
    return bool(
        exc.connection_invalidated
        or (
            isinstance(state, str)
            and (
                state.startswith("08") or state in {"53300", "57P01", "57P02", "57P03"}
            )
        )
        or (state is None and isinstance(exc.orig, DriverOperationalError))
    )


def install_http_handling(application: FastAPI) -> None:
    @application.middleware("http")
    async def request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Generate IDs rather than trusting arbitrary client header values.
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    async def error_response(request: Request, exc: Exception) -> JSONResponse:
        status_code, code, message = 500, "INTERNAL_ERROR", "Unexpected server error"
        headers: dict[str, str] = {}
        if isinstance(exc, HTTPException):
            status_code = exc.status_code
            code = (
                exc.code
                if isinstance(exc, APIError)
                else {404: "RESOURCE_NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
                    status_code, "HTTP_ERROR"
                )
            )
            message = str(exc.detail)
            headers.update(exc.headers or {})
        elif isinstance(exc, RequestValidationError):
            status_code, code, message = 422, "INVALID_REQUEST", "Invalid request"
        elif isinstance(exc, SQLAlchemyError):
            if database_unavailable(exc):
                status_code, code, message = (
                    503,
                    "DATABASE_UNAVAILABLE",
                    "Database unavailable",
                )
            else:
                status_code, code, message = (
                    500,
                    "DATABASE_ERROR",
                    "Unexpected database error",
                )
        identifier = str(getattr(request.state, "request_id", uuid4()))
        headers["X-Request-ID"] = identifier
        headers["Cache-Control"] = "no-store"
        body = ErrorResponse(
            error=ErrorDetail(code=code, message=message, request_id=identifier)
        )
        return JSONResponse(body.model_dump(), status_code=status_code, headers=headers)

    for error_type in (
        HTTPException,
        RequestValidationError,
        SQLAlchemyError,
        Exception,
    ):
        application.add_exception_handler(error_type, error_response)
