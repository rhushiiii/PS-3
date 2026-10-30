from collections.abc import Callable
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.http import not_found
from app.core.pagination import paginate as paginate
from app.core.pagination import paginate_list
from app.modules.auth.dependencies import require_metadata_role
from app.modules.auth.models import Role, User
from app.modules.institutions.models import Institution, Programme

if TYPE_CHECKING:
    from app.modules.institutions.schemas import InstitutionSummary


def scoped_entity[Model: Base](
    session: Session,
    user: User,
    model: type[Model],
    entity_id: UUID,
    gate: "Callable[[User], None]",
    *,
    owner_attr: str = "institution_id",
) -> Model:
    """Fetch an entity under the shared 404: missing and out-of-scope look alike."""
    gate(user)
    entity = session.get(model, entity_id)
    if entity is None or (
        user.role == Role.INSTITUTION_ADMIN
        and getattr(entity, owner_attr) != user.institution_id
    ):
        raise not_found()
    return entity


def scoped_institution(
    session: Session, user: User, institution_id: UUID
) -> Institution:
    return scoped_entity(
        session,
        user,
        Institution,
        institution_id,
        require_metadata_role,
        owner_attr="id",
    )


def forced_institution_id(user: User, requested: UUID | None) -> UUID | None:
    """Admins always see their own institution; a foreign id is a 404, never a leak."""
    if user.role != Role.INSTITUTION_ADMIN:
        return requested
    if requested is not None and requested != user.institution_id:
        raise not_found()
    return user.institution_id


def scoped_programme(
    session: Session, institution_id: UUID, programme_id: UUID
) -> None:
    programme = session.scalar(
        select(Programme.id).where(
            Programme.id == programme_id, Programme.institution_id == institution_id
        )
    )
    if programme is None:
        raise not_found()


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
    window = paginate_list(items, page, page_size)
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
        data=window.data,
        pagination=window.pagination,
    )
