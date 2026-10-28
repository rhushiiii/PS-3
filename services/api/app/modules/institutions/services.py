from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.http import APIError
from app.core.pagination import paginate as paginate
from app.modules.auth.dependencies import require_metadata_role
from app.modules.auth.models import Role, User
from app.modules.institutions.models import Institution, Programme

if TYPE_CHECKING:
    from app.modules.institutions.schemas import InstitutionSummary


def scoped_institution(
    session: Session, user: User, institution_id: UUID
) -> Institution:
    require_metadata_role(user)
    if user.role == Role.INSTITUTION_ADMIN and user.institution_id != institution_id:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    institution = session.get(Institution, institution_id)
    if institution is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return institution


def scoped_programme(
    session: Session, institution_id: UUID, programme_id: UUID
) -> None:
    programme = session.scalar(
        select(Programme.id).where(
            Programme.id == programme_id, Programme.institution_id == institution_id
        )
    )
    if programme is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")


def current_summary(
    session: Session,
    user: User,
    institution_id: UUID,
    year: str,
    programme_id: UUID | None,
    page: int,
    page_size: int,
) -> "InstitutionSummary":
    # Counts belong to submissions; institution API owns only the scoped view.
    from app.core.pagination import Pagination
    from app.modules.institutions.schemas import InstitutionSummary, ProgrammeSummary
    from app.modules.submissions.models import SubmissionScope
    from app.modules.submissions.services import batch_rows, snapshot_counts

    scoped_institution(session, user, institution_id)
    if programme_id is not None:
        scoped_programme(session, institution_id, programme_id)
    statement = (
        select(Programme)
        .where(Programme.institution_id == institution_id)
        .order_by(Programme.code)
    )
    if programme_id is not None:
        statement = statement.where(Programme.id == programme_id)
    programmes = list(session.scalars(statement))
    scopes = {
        scope.programme_id: scope
        for scope in session.scalars(
            select(SubmissionScope).where(
                SubmissionScope.institution_id == institution_id,
                SubmissionScope.academic_year == year,
            )
        )
    }
    items = []
    all_rows = []
    available = 0
    for programme in programmes:
        scope = scopes.get(programme.id)
        current = scope.current_batch_id if scope else None
        records = batch_rows(session, current) if current else []
        all_rows.extend(records)
        available += current is not None
        items.append(
            ProgrammeSummary(
                programme_id=programme.id,
                programme_code=programme.code,
                has_current_snapshot=current is not None,
                counts=snapshot_counts(records) if current else None,
            )
        )
    return InstitutionSummary(
        institution_id=institution_id,
        academic_year=year,
        totals=snapshot_counts(all_rows),
        coverage={
            "programmes": len(programmes),
            "with_current_snapshot": available,
            "status": "NONE"
            if not available
            else "COMPLETE"
            if available == len(programmes)
            else "PARTIAL",
        },
        data=items[(page - 1) * page_size : page * page_size],
        pagination=Pagination(page=page, page_size=page_size, total=len(items)),
    )
