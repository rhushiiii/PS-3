from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from sqlalchemy import select

from app.core.http import ErrorResponse, Now, no_store, settings_of
from app.core.pagination import Page, PageNumber, PageSize, paginate
from app.modules.auth.dependencies import CurrentUser, DatabaseSession, require_roles
from app.modules.auth.models import Role
from app.modules.institutions.schemas import AcademicYear
from app.modules.intake.services import intake_actor
from app.modules.integrity.models import IntegrityDecision
from app.modules.integrity.schemas import (
    Band,
    DecisionRequest,
    DecisionResponse,
    OverviewResponse,
    SignalsResponse,
)
from app.modules.integrity.services import (
    institution_signals,
    overview,
    record_decision,
)

router = APIRouter(
    prefix="/api/v1/integrity",
    tags=["Integrity review prompts (DEMO)"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    request: Request,
    response: Response,
    now: Now,
    user: CurrentUser,
    session: DatabaseSession,
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    band: Band | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> OverviewResponse:
    require_roles(user, {Role.AICTE_OFFICER, Role.AICTE_MANAGER})
    no_store(response)
    return overview(
        session,
        settings_of(request),
        now,
        academic_year,
        band,
        page,
        page_size,
    )


@router.get("/institutions/{institution_id}/signals", response_model=SignalsResponse)
def get_signals(
    institution_id: UUID,
    request: Request,
    response: Response,
    now: Now,
    user: CurrentUser,
    session: DatabaseSession,
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    programme_id: UUID | None = None,
) -> SignalsResponse:
    no_store(response)
    return institution_signals(
        session,
        settings_of(request),
        user,
        institution_id,
        now,
        academic_year,
        programme_id,
    )


@router.post(
    "/institutions/{institution_id}/decisions",
    response_model=DecisionResponse,
    status_code=201,
)
def post_decision(
    institution_id: UUID,
    body: DecisionRequest,
    request: Request,
    now: Now,
    user: CurrentUser,
    session: DatabaseSession,
) -> DecisionResponse:
    return DecisionResponse.model_validate(
        record_decision(
            session,
            settings_of(request),
            user,
            institution_id,
            body,
            now,
        )
    )


@router.get(
    "/institutions/{institution_id}/decisions", response_model=Page[DecisionResponse]
)
def get_decisions(
    institution_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    signal_key: Annotated[str | None, Query(max_length=300)] = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[DecisionResponse]:
    intake_actor(session, user, institution_id, officer_only=True)
    statement = (
        select(IntegrityDecision)
        .where(IntegrityDecision.institution_id == institution_id)
        .order_by(IntegrityDecision.created_at.desc(), IntegrityDecision.id.desc())
    )
    if signal_key is not None:
        statement = statement.where(IntegrityDecision.signal_key == signal_key)
    no_store(response)
    return paginate(session, statement, DecisionResponse, page, page_size)
