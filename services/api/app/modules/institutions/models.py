from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, Timestamps


class AdmissionCategory(StrEnum):
    REGULAR = "REGULAR"
    SUPERNUMERARY = "SUPERNUMERARY"
    NRI = "NRI"
    OCI = "OCI"
    FOREIGN_NATIONAL = "FOREIGN_NATIONAL"


class Institution(Timestamps, Base):
    __tablename__ = "institutions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    permanent_id: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class Programme(Timestamps, Base):
    __tablename__ = "programmes"
    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_programme_institution_code"
        ),
        UniqueConstraint("id", "institution_id", name="uq_programme_id_institution"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class IntakeRule(Timestamps, Base):
    __tablename__ = "intake_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["programme_id", "institution_id"],
            ["programmes.id", "programmes.institution_id"],
            name="fk_intake_programme_institution",
        ),
        UniqueConstraint(
            "institution_id",
            "programme_id",
            "academic_year",
            "category",
            "rule_version",
            name="uq_intake_scope_category_version",
        ),
        CheckConstraint("approved_seats >= 0", name="ck_intake_nonnegative_capacity"),
        CheckConstraint(
            "academic_year ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_intake_year_format"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(index=True)
    programme_id: Mapped[UUID]
    academic_year: Mapped[str] = mapped_column(String(7))
    category: Mapped[AdmissionCategory] = mapped_column(
        Enum(
            AdmissionCategory,
            native_enum=False,
            create_constraint=True,
            name="admission_category",
        )
    )
    approved_seats: Mapped[int]
    rule_version: Mapped[str] = mapped_column(String(64))
    source_label: Mapped[str] = mapped_column(String(64))
