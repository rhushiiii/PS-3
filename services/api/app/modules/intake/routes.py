from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from sqlalchemy import select

from app.core.config import Settings
from app.core.http import APIError, ErrorResponse
from app.core.pagination import Page, paginate
from app.core.rate_limit import rate_limit
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.institutions.models import IntakeRule
from app.modules.institutions.schemas import AcademicYear
from app.modules.intake.models import (
    IntakeAssessment,
    IntakeDeclaration,
    IntakeRuleChange,
)
from app.modules.intake.schemas import (
    AssessmentResponse,
    AssessmentSummary,
    DeclarationRequest,
    DeclarationResponse,
    RuleChangeRequest,
    RuleChangeResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.modules.intake.services import (
    change_rule,
    create_assessment,
    declare,
    intake_actor,
    latest_declaration,
    scoped_assessment,
    simulate,
)
from app.modules.submissions.services import scoped_batch

router = APIRouter(
    prefix="/api/v1",
    tags=["Intake governance (DEMO)"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def rule_version(request: Request) -> str:
    return cast(Settings, request.app.state.settings).validation_intake_rule_version


@router.patch(
    "/institutions/{institution_id}/intake/{rule_id}",
    response_model=RuleChangeResponse,
    dependencies=[rate_limit("intake")],
)
def patch_rule(
    institution_id: UUID,
    rule_id: UUID,
    body: RuleChangeRequest,
    user: CurrentUser,
    session: DatabaseSession,
) -> RuleChangeResponse:
    return RuleChangeResponse.model_validate(
        change_rule(session, user, institution_id, rule_id, body)
    )


@router.get(
    "/institutions/{institution_id}/intake/changes",
    response_model=Page[RuleChangeResponse],
)
def rule_changes(
    institution_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    response: Response,
    intake_rule_id: UUID | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[RuleChangeResponse]:
    intake_actor(session, user, institution_id)
    statement = (
        select(IntakeRuleChange)
        .join(IntakeRule, IntakeRule.id == IntakeRuleChange.intake_rule_id)
        .where(IntakeRule.institution_id == institution_id)
        .order_by(IntakeRuleChange.created_at.desc(), IntakeRuleChange.id.desc())
    )
    if intake_rule_id is not None:
        statement = statement.where(IntakeRuleChange.intake_rule_id == intake_rule_id)
    response.headers["Cache-Control"] = "no-store"
    return paginate(session, statement, RuleChangeResponse, page, page_size)


@router.post(
    "/institutions/{institution_id}/declarations",
    response_model=DeclarationResponse,
    status_code=201,
)
def create_declaration(
    institution_id: UUID,
    body: DeclarationRequest,
    user: CurrentUser,
    session: DatabaseSession,
) -> DeclarationResponse:
    return DeclarationResponse.model_validate(
        declare(session, user, institution_id, body)
    )


@router.get(
    "/institutions/{institution_id}/declarations/latest",
    response_model=DeclarationResponse,
)
def latest(
    institution_id: UUID,
    programme_id: UUID,
    academic_year: Annotated[AcademicYear, Query()],
    user: CurrentUser,
    session: DatabaseSession,
) -> DeclarationResponse:
    intake_actor(session, user, institution_id)
    declaration = latest_declaration(
        session, institution_id, programme_id, academic_year
    )
    if declaration is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return DeclarationResponse.model_validate(declaration)


@router.get(
    "/institutions/{institution_id}/declarations",
    response_model=Page[DeclarationResponse],
)
def declarations(
    institution_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    programme_id: UUID | None = None,
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[DeclarationResponse]:
    intake_actor(session, user, institution_id)
    statement = (
        select(IntakeDeclaration)
        .where(IntakeDeclaration.institution_id == institution_id)
        .order_by(IntakeDeclaration.created_at.desc(), IntakeDeclaration.id.desc())
    )
    if programme_id is not None:
        statement = statement.where(IntakeDeclaration.programme_id == programme_id)
    if academic_year is not None:
        statement = statement.where(IntakeDeclaration.academic_year == academic_year)
    return paginate(session, statement, DeclarationResponse, page, page_size)


@router.post(
    "/institutions/{institution_id}/intake/simulate",
    response_model=SimulationResponse,
    dependencies=[rate_limit("intake")],
)
def simulate_intake(
    institution_id: UUID,
    body: SimulationRequest,
    request: Request,
    user: CurrentUser,
    session: DatabaseSession,
) -> SimulationResponse:
    return simulate(session, user, institution_id, body, rule_version(request))


@router.post(
    "/submissions/{batch_id}/intake-assessments",
    response_model=AssessmentResponse,
    status_code=201,
    dependencies=[rate_limit("intake")],
)
def post_assessment(
    batch_id: UUID, request: Request, user: CurrentUser, session: DatabaseSession
) -> AssessmentResponse:
    return create_assessment(session, user, batch_id, rule_version(request))


@router.get(
    "/submissions/{batch_id}/intake-assessments",
    response_model=Page[AssessmentSummary],
)
def assessments(
    batch_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[AssessmentSummary]:
    scoped_batch(session, user, batch_id)
    statement = (
        select(IntakeAssessment)
        .where(IntakeAssessment.batch_id == batch_id)
        .order_by(IntakeAssessment.computed_at.desc(), IntakeAssessment.id.desc())
    )
    return paginate(session, statement, AssessmentSummary, page, page_size)


@router.get(
    "/submissions/{batch_id}/intake-assessments/{assessment_id}",
    response_model=AssessmentResponse,
)
def assessment(
    batch_id: UUID, assessment_id: UUID, user: CurrentUser, session: DatabaseSession
) -> AssessmentResponse:
    return AssessmentResponse.model_validate(
        scoped_assessment(session, user, batch_id, assessment_id)
    )
