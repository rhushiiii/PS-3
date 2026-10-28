from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, Timestamps


class Role(StrEnum):
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    AICTE_OFFICER = "AICTE_OFFICER"
    AICTE_MANAGER = "AICTE_MANAGER"
    AUTHORIZED_VERIFIER = "AUTHORIZED_VERIFIER"


class User(Timestamps, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role <> 'INSTITUTION_ADMIN' OR institution_id IS NOT NULL",
            name="ck_admin_requires_institution",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, create_constraint=True, name="user_role")
    )
    institution_id: Mapped[UUID | None] = mapped_column(ForeignKey("institutions.id"))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    demo_alias: Mapped[str | None] = mapped_column(String(64), unique=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
