from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.core.http import AppSettings, ErrorResponse, no_store
from app.core.pagination import Page, PageNumber, PageSize
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.institutions.schemas import AcademicYear
from app.modules.records.schemas import RecordDetail, RecordRow
from app.modules.records.services import list_records, record_detail
from app.modules.validation.rules import STATUSES
from app.modules.validation.schemas import RecordStatus

router = APIRouter(
    prefix="/api/v1/records",
    tags=["Record registry"],
    responses={code: {"model": ErrorResponse} for code in (401, 403, 404, 422, 500)},
)
EnrollmentStatus = Annotated[str | None, Query(pattern=f"^({'|'.join(STATUSES)})$")]


@router.get("", response_model=Page[RecordRow])
def registry(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    institution_id: UUID | None = None,
    programme_id: UUID | None = None,
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    enrollment_status: EnrollmentStatus = None,
    validation_status: RecordStatus | None = None,
    q: Annotated[
        str | None,
        Query(
            max_length=100,
            description=(
                "Case-insensitive college_student_id prefix or student name "
                "substring. APAAR values are never searchable."
            ),
        ),
    ] = None,
    include_candidates: bool = False,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[RecordRow]:
    result = list_records(
        session,
        user,
        institution_id=institution_id,
        programme_id=programme_id,
        academic_year=academic_year,
        enrollment_status=enrollment_status,
        validation_status=validation_status,
        q=q,
        include_candidates=include_candidates,
        page=page,
        page_size=page_size,
    )
    no_store(response)
    return result


@router.get("/{record_version_id}", response_model=RecordDetail)
def detail(
    record_version_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> RecordDetail:
    result = record_detail(session, user, record_version_id, settings)
    no_store(response)
    return result
