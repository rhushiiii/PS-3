"""Shared "latest wins" query idioms.

Every domain history is append-only, so the newest row per key is picked by an
explicit stamp plus an id tie-break — never by "whatever row happens to exist".
Column arguments are loosely typed: SQLAlchemy's instrumented attributes and
ColumnElements are interchangeable here, and the tie-break is the contract.
The statement's own row type flows through unchanged, so callers keep full typing.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select
from sqlalchemy.dialects.postgresql import distinct_on


def latest_row[*Ts](statement: Select[*Ts], stamp: Any, tie: Any) -> Select[*Ts]:
    """Newest single row: stamp desc with id as the deterministic tie-break."""
    return statement.order_by(stamp.desc(), tie.desc()).limit(1)


def latest_per_key[*Ts](
    statement: Select[*Ts], key: Sequence[Any], stamp: Any, tie: Any
) -> Select[*Ts]:
    """Newest row per key in one query (PostgreSQL DISTINCT ON)."""
    return statement.order_by(*key, stamp.desc(), tie.desc()).ext(distinct_on(*key))
