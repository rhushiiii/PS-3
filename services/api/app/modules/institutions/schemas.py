from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

from app.core.pagination import Page as Page
from app.core.pagination import Pagination
from app.modules.institutions.models import AdmissionCategory


def consecutive_academic_year(value: str) -> str:
    if int(value[-2:]) != (int(value[:4]) + 1) % 100:
        raise ValueError("Academic year must contain consecutive years")
    return value


AcademicYear = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{4}-[0-9]{2}$"),
    AfterValidator(consecutive_academic_year),
]


class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    permanent_id: str
    name: str
    region: str
    active: bool


class ProgrammeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    code: str
    name: str
    active: bool


class IntakeRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    programme_id: UUID
    academic_year: str
    category: AdmissionCategory
    approved_seats: int
    rule_version: str
    source_label: str


class ProgrammeSummary(BaseModel):
    programme_id: UUID
    programme_code: str
    has_current_snapshot: bool
    counts: dict[str, Any] | None


class InstitutionSummary(BaseModel):
    institution_id: UUID
    academic_year: str
    source_label: Literal["DEMO"] = "DEMO"
    count_basis: Literal["AVAILABLE_ACTIVATED_DECLARATIONS"] = (
        "AVAILABLE_ACTIVATED_DECLARATIONS"
    )
    totals: dict[str, Any]
    coverage: dict[str, Any]
    data: list[ProgrammeSummary]
    pagination: Pagination
