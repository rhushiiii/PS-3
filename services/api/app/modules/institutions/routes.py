from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_snapshot_session
from app.core.http import APIError, ErrorResponse
from app.modules.auth.dependencies import (
    CurrentUser,
    DatabaseSession,
    require_metadata_role,
)
from app.modules.auth.models import Role
from app.modules.institutions.models import Institution, IntakeRule, Programme
from app.modules.institutions.schemas import (
    AcademicYear,
    InstitutionResponse,
    InstitutionSummary,
    IntakeRuleResponse,
    Page,
    ProgrammeResponse,
)
from app.modules.institutions.services import (
    current_summary,
    paginate,
    scoped_institution,
    scoped_programme,
)

router = APIRouter(
    prefix="/api/v1/institutions",
    tags=["Institutions"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get("/{institution_id}/summary", response_model=InstitutionSummary)
def summary(
    institution_id: UUID,
    response: Response,
    user: CurrentUser,
    session: Annotated[Session, Depends(get_snapshot_session)],
    academic_year: Annotated[AcademicYear, Query()],
    programme_id: UUID | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> InstitutionSummary:
    result = current_summary(
        session, user, institution_id, academic_year, programme_id, page, page_size
    )
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("", response_model=Page[InstitutionResponse])
def institutions(
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
    region: Annotated[str | None, Query(max_length=64)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> Page[InstitutionResponse]:
    require_metadata_role(user)
    if user.role == Role.INSTITUTION_ADMIN:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")
    statement = select(Institution).order_by(Institution.permanent_id)
    if region is not None:
        statement = statement.where(Institution.region == region)
    if q is not None:
        statement = statement.where(Institution.name.icontains(q, autoescape=True))
    return paginate(session, statement, InstitutionResponse, page, page_size)


@router.get("/{institution_id}", response_model=InstitutionResponse)
def institution(
    institution_id: UUID, user: CurrentUser, session: DatabaseSession
) -> InstitutionResponse:
    return InstitutionResponse.model_validate(
        scoped_institution(session, user, institution_id)
    )


@router.get("/{institution_id}/programmes", response_model=Page[ProgrammeResponse])
def programmes(
    institution_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[ProgrammeResponse]:
    scoped_institution(session, user, institution_id)
    statement = (
        select(Programme)
        .where(Programme.institution_id == institution_id)
        .order_by(Programme.code)
    )
    return paginate(session, statement, ProgrammeResponse, page, page_size)


@router.get("/{institution_id}/intake", response_model=Page[IntakeRuleResponse])
def intake(
    institution_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    academic_year: Annotated[AcademicYear, Query()],
    programme_id: UUID | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[IntakeRuleResponse]:
    scoped_institution(session, user, institution_id)
    if programme_id is not None:
        scoped_programme(session, institution_id, programme_id)
    statement = (
        select(IntakeRule)
        .where(
            IntakeRule.institution_id == institution_id,
            IntakeRule.academic_year == academic_year,
        )
        .order_by(IntakeRule.programme_id, IntakeRule.category, IntakeRule.rule_version)
    )
    if programme_id is not None:
        statement = statement.where(IntakeRule.programme_id == programme_id)
    return paginate(session, statement, IntakeRuleResponse, page, page_size)
