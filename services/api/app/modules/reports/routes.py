from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import get_snapshot_session
from app.core.http import Now, error_responses
from app.core.rate_limit import rate_limit
from app.modules.analytics.services import Filters
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.cases.models import CasePriority, CaseSeverity
from app.modules.institutions.schemas import AcademicYear
from app.modules.reports import renderers
from app.modules.reports.schemas import ReportFormat, ReportKind
from app.modules.reports.services import ReportParams, build_report, record_export

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports (SIMULATED / DEMO exports)"],
    responses=error_responses(401, 403, 404, 422, 429, 503),
)
Reader = Annotated[Session, Depends(get_snapshot_session)]


@router.get(
    "/{kind}",
    dependencies=[rate_limit("exports")],
    response_class=Response,
    responses={
        200: {
            "description": "The report file (aggregates only; DEMO provenance inside)",
            "content": {
                media: {"schema": {"type": "string", "format": "binary"}}
                for media in renderers.MEDIA_TYPES.values()
            },
        }
    },
)
def export_report(
    kind: ReportKind,
    request: Request,
    user: CurrentUser,
    reader: Reader,
    audit_session: DatabaseSession,
    now: Now,
    file_format: Annotated[ReportFormat, Query(alias="format")] = "csv",
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    institution_id: UUID | None = None,
    region: Annotated[str | None, Query(max_length=64)] = None,
    programme_code: Annotated[str | None, Query(max_length=64)] = None,
    priority: CasePriority | None = None,
    severity: CaseSeverity | None = None,
) -> Response:
    settings = cast(Settings, request.app.state.settings)
    params = ReportParams(
        Filters(academic_year, institution_id, region, programme_code),
        priority,
        severity,
    )
    report = build_report(reader, kind, user, params, settings, now)
    content = renderers.render(report, file_format)
    record_export(audit_session, user, report, file_format)
    return Response(
        content,
        media_type=renderers.MEDIA_TYPES[file_format],
        headers={
            "Content-Disposition": (
                f'attachment; filename="{renderers.filename(report, file_format)}"'
            ),
            "Cache-Control": "no-store",
        },
    )
