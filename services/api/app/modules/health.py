from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_engine
from app.core.http import database_unavailable

router = APIRouter(prefix="/api/v1", tags=["Health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unavailable"]
    database: Literal["reachable", "unreachable"]


@router.get("/health", response_model=LivenessResponse)
def health() -> LivenessResponse:
    """Public liveness; deliberately independent of PostgreSQL."""
    return LivenessResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
)
def ready(
    response: Response, engine: Annotated[Engine, Depends(get_engine)]
) -> ReadinessResponse:
    """Public database readiness; never expose connection errors or credentials."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        if not database_unavailable(exc):
            raise
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="unavailable", database="unreachable")
    return ReadinessResponse(status="ready", database="reachable")
