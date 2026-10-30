from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.database import get_snapshot_session
from app.core.http import APIError, ErrorResponse, no_store, not_found
from app.core.idempotency import IDEMPOTENCY_KEY_PATTERN
from app.core.pagination import Page, PageNumber, PageSize, paginate, paginate_list
from app.core.rate_limit import rate_limit
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.auth.models import Role
from app.modules.institutions.models import Programme
from app.modules.institutions.schemas import AcademicYear
from app.modules.institutions.services import scoped_institution, scoped_programme
from app.modules.submissions.activation import (
    activate,
    create_review,
    get_activation_session,
    review_response,
    scoped_review,
)
from app.modules.submissions.models import StudentRecordVersion, SubmissionBatch
from app.modules.submissions.parsing import (
    HEADERS,
    detect_format,
    parse_csv,
    parse_xlsx,
    read_multipart,
)
from app.modules.submissions.schemas import (
    ActivationRequest,
    ActivationResponse,
    BatchResponse,
    ReviewRequest,
    ReviewResponse,
    RowResponse,
    UploadPolicyResponse,
    UploadResponse,
)
from app.modules.submissions.services import (
    describe_batches,
    idempotent_replay,
    persist_candidate,
    require_submission_role,
    row_response,
    scoped_batch,
    upload_fingerprint,
    upload_scope,
)
from app.modules.validation.schemas import RecordStatus
from app.modules.validation.services import findings_for, record_statuses, selected_run

router = APIRouter(
    prefix="/api/v1/submissions",
    tags=["Candidate submissions"],
    responses={
        code: {"model": ErrorResponse}
        for code in (400, 401, 403, 404, 408, 409, 413, 422, 500, 503)
    },
)
IdempotencyKey = Annotated[
    str | None,
    Header(
        pattern=IDEMPOTENCY_KEY_PATTERN,
        description=(
            "Optional. Repeating a key with the same file and scope returns the "
            "original batch (HTTP 200, Idempotent-Replayed: true) without a new "
            "batch or audit event; the same key with different input is 409 "
            "IDEMPOTENCY_KEY_REUSED. Keys are scoped per institution."
        ),
    ),
]
SnapshotSession = Annotated[Session, Depends(get_snapshot_session)]
ActivationSession = Annotated[Session, Depends(get_activation_session)]
MULTIPART_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "file",
                        "institution_id",
                        "programme_id",
                        "academic_year",
                    ],
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                        "institution_id": {"type": "string", "format": "uuid"},
                        "programme_id": {"type": "string", "format": "uuid"},
                        "academic_year": {
                            "type": "string",
                            "pattern": "^[0-9]{4}-[0-9]{2}$",
                        },
                        "schema_version": {
                            "type": "string",
                            "const": "v1",
                            "default": "v1",
                        },
                    },
                }
            }
        },
    }
}


@router.get("/upload-policy", response_model=UploadPolicyResponse)
def upload_policy(
    request: Request, response: Response, user: CurrentUser
) -> UploadPolicyResponse:
    require_submission_role(user)
    settings = cast(Settings, request.app.state.settings)
    no_store(response)
    return UploadPolicyResponse(
        required_headers=list(HEADERS),
        max_file_bytes=settings.upload_max_bytes,
        max_rows=settings.upload_max_rows,
        receive_timeout_seconds=settings.upload_receive_timeout_seconds,
        processing_timeout_seconds=settings.upload_processing_timeout_seconds,
    )


@router.post(
    "/{batch_id}/reviews",
    response_model=ReviewResponse,
    status_code=201,
    dependencies=[rate_limit("reviews")],
)
def review_candidate(
    batch_id: UUID,
    body: ReviewRequest,
    response: Response,
    user: CurrentUser,
    session: SnapshotSession,
) -> ReviewResponse:
    result = create_review(session, user.id, batch_id, body.validation_run_id)
    no_store(response)
    return result


@router.get("/{batch_id}/reviews/{review_id}", response_model=ReviewResponse)
def review_detail(
    batch_id: UUID,
    review_id: UUID,
    response: Response,
    user: CurrentUser,
    session: SnapshotSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> ReviewResponse:
    result = review_response(
        session,
        scoped_review(session, user, batch_id, review_id),
        page=page,
        page_size=page_size,
    )
    no_store(response)
    return result


@router.post(
    "/{batch_id}/activate",
    response_model=ActivationResponse,
    dependencies=[rate_limit("reviews")],
)
def activate_candidate(
    batch_id: UUID,
    body: ActivationRequest,
    response: Response,
    user: CurrentUser,
    session: ActivationSession,
) -> ActivationResponse:
    result = activate(session, user.id, batch_id, body)
    no_store(response)
    return result


@router.post(
    "",
    status_code=201,
    response_model=UploadResponse,
    openapi_extra=MULTIPART_SCHEMA,
    dependencies=[rate_limit("uploads")],
    responses={200: {"model": UploadResponse, "description": "Idempotent replay"}},
    description=(
        "Synthetic demo data only. Creates an unvalidated, inactive candidate "
        "snapshot from a CSV or XLSX file. An idempotent replay returns the "
        "original body with status 200 instead of 201."
    ),
)
async def upload(
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    idempotency_key: IdempotencyKey = None,
) -> UploadResponse:
    require_submission_role(user, uploading=True)
    settings = cast(Settings, request.app.state.settings)
    context, data, filename, deadline = await read_multipart(request, settings)

    # Database/file work is synchronous, executed off the event loop; never queued.
    def process() -> tuple[UploadResponse, bool]:
        upload_scope(session, user, context)
        idempotency = None
        if idempotency_key is not None:
            idempotency = (idempotency_key, upload_fingerprint(data, context))
            replay = idempotent_replay(session, context.institution_id, *idempotency)
            if replay is not None:
                return replay, True
        source_format = detect_format(data, filename)
        rows = (
            parse_xlsx(data, settings, deadline)
            if source_format == "xlsx"
            else parse_csv(data, settings, deadline)
        )
        try:
            return (
                persist_candidate(
                    session,
                    user,
                    context,
                    data,
                    filename,
                    rows,
                    deadline,
                    source=f"{source_format.upper()}_UPLOAD",
                    idempotency=idempotency,
                ),
                False,
            )
        except IntegrityError as error:
            # A concurrent identical request won the unique index: return its batch.
            constraint = getattr(error.orig, "diag", None)
            if (
                idempotency is None
                or getattr(constraint, "constraint_name", None)
                != "uq_batch_idempotency"
            ):
                raise
            replay = idempotent_replay(session, context.institution_id, *idempotency)
            if replay is None:
                raise
            return replay, True

    result, replayed = await run_in_threadpool(process)
    if replayed:
        response.status_code = 200
        response.headers["Idempotent-Replayed"] = "true"
    no_store(response)
    return result


@router.get("", response_model=Page[BatchResponse])
def history(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    institution_id: UUID | None = None,
    programme_id: UUID | None = None,
    academic_year: Annotated[AcademicYear | None, Query()] = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[BatchResponse]:
    require_submission_role(user)
    if user.role == Role.INSTITUTION_ADMIN:
        if institution_id is not None and institution_id != user.institution_id:
            raise not_found()
        institution_id = user.institution_id
    if institution_id is not None:
        scoped_institution(session, user, institution_id)
        if programme_id is not None:
            scoped_programme(session, institution_id, programme_id)
    elif programme_id is not None:
        # Officer-only path: still validate the programme exists before filtering.
        if session.get(Programme, programme_id) is None:
            raise not_found()
    statement = select(SubmissionBatch).order_by(
        SubmissionBatch.received_at.desc(), SubmissionBatch.id.desc()
    )
    if institution_id is not None:
        statement = statement.where(SubmissionBatch.institution_id == institution_id)
    if programme_id is not None:
        statement = statement.where(SubmissionBatch.programme_id == programme_id)
    if academic_year is not None:
        statement = statement.where(SubmissionBatch.academic_year == academic_year)
    result = paginate(session, statement, BatchResponse, page, page_size)
    describe_batches(session, result.data)
    no_store(response)
    return result


@router.get("/{batch_id}", response_model=BatchResponse)
def detail(
    batch_id: UUID, response: Response, user: CurrentUser, session: DatabaseSession
) -> BatchResponse:
    batch = scoped_batch(session, user, batch_id)
    result = describe_batches(session, [BatchResponse.model_validate(batch)])[0]
    no_store(response)
    return result


@router.get("/{batch_id}/rows", response_model=Page[RowResponse])
def rows(
    batch_id: UUID,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
    run_id: UUID | None = None,
    status: RecordStatus | None = None,
) -> Page[RowResponse]:
    batch = scoped_batch(session, user, batch_id)
    run = selected_run(session, batch.id, run_id)
    if status is not None and run is None:
        raise APIError(409, "VALIDATION_NOT_RUN", "No completed validation run exists")
    statuses = record_statuses(findings_for(session, run)) if run else {}
    records = list(
        session.scalars(
            select(StudentRecordVersion)
            .where(StudentRecordVersion.batch_id == batch.id)
            .order_by(StudentRecordVersion.source_row_number)
        )
    )
    selected = [
        record
        for record in records
        if status is None or statuses.get(record.id, "VALID") == status
    ]
    window = paginate_list(selected, page, page_size)
    results = []
    for record in window.data:
        result = row_response(record)
        result.validation_status = statuses.get(record.id, "VALID") if run else None
        result.validation_run_id = run.id if run else None
        results.append(result)
    no_store(response)
    return Page[RowResponse](
        data=results,
        pagination=window.pagination,
    )
