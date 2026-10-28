"""Pagination shared by institution and submission APIs."""

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.database import Base


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int


class Page[T](BaseModel):
    data: list[T]
    pagination: Pagination


def paginate[Model: Base, View: BaseModel](
    session: Session,
    statement: Select[Model],
    view: type[View],
    page: int,
    page_size: int,
) -> Page[View]:
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.scalars(statement.offset((page - 1) * page_size).limit(page_size))
    return Page[View](
        data=[view.model_validate(row) for row in rows],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )
