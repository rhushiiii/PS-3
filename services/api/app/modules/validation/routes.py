from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import error_responses, no_store
from app.core.pagination import (
    Page,
    PageNumber,
    PageSize,
    paginate_list,
    paginate_rows,
)
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.submissions.services import scoped_batch
from app.modules.validation.models import ValidationRun
from app.modules.validation.schemas import (
    Classification,
    FindingResponse,
    RunResponse,
    Severity,
)
from app.modules.validation.services import (
    feedback_csv,
    finding_response,
    findings_for,
    get_validation_session,
    require_run,
    run_response,
    validate_candidate,
)

router = APIRouter(
    prefix="/api/v1/submissions",
    tags=["Local student validation"],
    responses=error_responses(401, 403, 404, 409, 422, 500, 503),
)
ValidationSession = Annotated[Session, Depends(get_validation_session)]


@router.post("/{batch_id}/validate", response_model=RunResponse, status_code=201)
def validate(
    batch_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: ValidationSession,
) -> RunResponse:
    result = validate_candidate(
        session, user.id, batch_id, cast(Settings, request.app.state.settings)
    )
    no_store(response)
    return result


@router.post("/{batch_id}/revalidate", response_model=RunResponse, status_code=201)
def revalidate(
    batch_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: ValidationSession,
) -> RunResponse:
    result = validate_candidate(
        session,
        user.id,
        batch_id,
        cast(Settings, request.app.state.settings),
        revalidate=True,
    )
    no_store(response)
    return result


@router.get("/{batch_id}/validation-runs", response_model=Page[RunResponse])
def history(
    batch_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[RunResponse]:
    scoped_batch(session, user, batch_id)
    result = paginate_rows(
        session,
        select(ValidationRun)
        .where(ValidationRun.batch_id == batch_id)
        .order_by(ValidationRun.completed_at.desc(), ValidationRun.id.desc()),
        lambda run: run_response(session, run),
        page,
        page_size,
    )
    no_store(response)
    return result


@router.get("/{batch_id}/validation-runs/{run_id}", response_model=RunResponse)
def detail(
    batch_id: UUID,
    run_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
) -> RunResponse:
    scoped_batch(session, user, batch_id)
    no_store(response)
    return run_response(session, require_run(session, batch_id, run_id))


@router.get("/{batch_id}/findings", response_model=Page[FindingResponse])
def findings(
    batch_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    run_id: UUID | None = None,
    rule_code: Annotated[str | None, Query(max_length=64)] = None,
    severity: Severity | None = None,
    classification: Classification | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[FindingResponse]:
    scoped_batch(session, user, batch_id)
    run = require_run(session, batch_id, run_id)
    description = run_response(session, run)
    selected = [
        item
        for item in findings_for(session, run)
        if (rule_code is None or item.rule_code == rule_code)
        and (severity is None or item.severity == severity)
        and (classification is None or item.classification == classification)
    ]
    window = paginate_list(selected, page, page_size)
    no_store(response)
    return Page[FindingResponse](
        data=[finding_response(item, description, user) for item in window.data],
        pagination=window.pagination,
    )


@router.get("/{batch_id}/feedback.csv", response_class=Response)
def feedback(
    batch_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    run_id: UUID | None = None,
) -> Response:
    batch = scoped_batch(session, user, batch_id)
    run = require_run(session, batch_id, run_id)
    return Response(
        content=feedback_csv(session, batch, run, user),
        media_type="text/csv; charset=utf-8",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="feedback-{run.id}.csv"',
            "X-Content-Type-Options": "nosniff",
        },
    )
