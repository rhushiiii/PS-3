from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_snapshot_session
from app.core.http import AppSettings, ErrorResponse, Now, no_store
from app.core.pagination import PageNumber, PageSize, paginate_list
from app.modules.analytics import services
from app.modules.analytics.schemas import (
    CasePerformanceResponse,
    CompletenessResponse,
    GroupBy,
    TrendsResponse,
    UtilisationResponse,
)
from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.auth.models import Role, User
from app.modules.cases.models import CasePriority, CaseSeverity
from app.modules.institutions.schemas import AcademicYear
from app.modules.intake.services import POOLING_NOTE

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics (DEMO aggregates)"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
ProgrammeCode = Annotated[str | None, Query(max_length=64)]
Region = Annotated[str | None, Query(max_length=64)]


def analytics_user(user: CurrentUser) -> User:
    """Officers and managers only; institution admins have their own dashboard."""
    require_roles(user, {Role.AICTE_OFFICER, Role.AICTE_MANAGER})
    return user


def common_filters(
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    institution_id: UUID | None = None,
    region: Region = None,
    programme_code: ProgrammeCode = None,
) -> services.Filters:
    return services.Filters(academic_year, institution_id, region, programme_code)


Authorized = Annotated[User, Depends(analytics_user)]
Reader = Annotated[Session, Depends(get_snapshot_session)]
Common = Annotated[services.Filters, Depends(common_filters)]


@router.get("/enrolment-trends", response_model=TrendsResponse)
def enrolment_trends(
    response: Response,
    _: Authorized,
    session: Reader,
    filters: Common,
    now: Now,
    group_by: GroupBy = "academic_year",
    page: PageNumber = 1,
    page_size: PageSize = 50,
) -> TrendsResponse:
    meta, rows = services.enrolment_trends(session, filters, group_by, now)
    window = paginate_list(rows, page, page_size)
    no_store(response)
    return TrendsResponse(
        **meta.model_dump(),
        group_by=group_by,
        data=window.data,
        pagination=window.pagination,
    )


@router.get("/submission-completeness", response_model=CompletenessResponse)
def submission_completeness(
    response: Response,
    _: Authorized,
    session: Reader,
    filters: Common,
    now: Now,
    settings: AppSettings,
    page: PageNumber = 1,
    page_size: PageSize = 50,
) -> CompletenessResponse:
    meta, rows, rollups = services.submission_completeness(
        session, filters, settings, now
    )
    window = paginate_list(rows, page, page_size)
    no_store(response)
    return CompletenessResponse(
        **meta.model_dump(),
        stale_after_days=settings.integrity_stale_days,
        data=window.data,
        rollups_by_region=rollups,
        pagination=window.pagination,
    )


@router.get("/intake-utilisation", response_model=UtilisationResponse)
def intake_utilisation(
    response: Response,
    _: Authorized,
    session: Reader,
    filters: Common,
    now: Now,
    settings: AppSettings,
    page: PageNumber = 1,
    page_size: PageSize = 50,
) -> UtilisationResponse:
    meta, rows = services.intake_utilisation(session, filters, settings, now)
    window = paginate_list(rows, page, page_size)
    no_store(response)
    return UtilisationResponse(
        **meta.model_dump(),
        rule_version_in_use=settings.validation_intake_rule_version,
        pooling_note=POOLING_NOTE,
        data=window.data,
        pagination=window.pagination,
    )


@router.get("/case-performance", response_model=CasePerformanceResponse)
def case_performance(
    response: Response,
    _: Authorized,
    session: Reader,
    now: Now,
    settings: AppSettings,
    institution_id: UUID | None = None,
    region: Region = None,
    priority: CasePriority | None = None,
    severity: CaseSeverity | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 50,
) -> CasePerformanceResponse:
    report = services.case_performance(
        session,
        services.Filters(institution_id=institution_id, region=region),
        priority,
        severity,
        settings,
        now,
    )
    window = paginate_list(report.institutions, page, page_size)
    no_store(response)
    return CasePerformanceResponse(
        **report.meta.model_dump(),
        totals=report.totals,
        by_status=report.by_status,
        ageing=report.ageing,
        resolution_days=report.resolution,
        data=window.data,
        pagination=window.pagination,
    )
