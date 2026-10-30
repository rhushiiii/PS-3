"""Pagination shared by institution and submission APIs."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.database import Base

PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int


class Page[T](BaseModel):
    data: list[T]
    pagination: Pagination


def paginate_list[T](items: Sequence[T], page: int, page_size: int) -> Page[T]:
    """Slice an in-memory list into one page; the total counts every item."""
    start = (page - 1) * page_size
    return Page(
        data=list(items[start : start + page_size]),
        pagination=Pagination(page=page, page_size=page_size, total=len(items)),
    )


def count_rows[*Row](session: Session, statement: Select[*Row]) -> int:
    """Count the rows a select returns, ignoring its ordering."""
    subquery = statement.order_by(None).subquery()
    return session.scalar(select(func.count()).select_from(subquery)) or 0


def window[*Row](statement: Select[*Row], page: int, page_size: int) -> Select[*Row]:
    """Restrict a select to the rows of one page."""
    return statement.offset((page - 1) * page_size).limit(page_size)


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
