from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.modules.institutions.models import AdmissionCategory
from app.modules.institutions.schemas import AcademicYear

DEMO_NOTICE = (
    "DEMO rule values for the prototype; not official AICTE policy. "
    "Rules-generated flags are not fraud determinations; officers decide."
)

Reason = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)
]
Basis = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class RuleChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approved_seats: int = Field(ge=0, le=1_000_000)
    reason: Reason


class RuleChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    intake_rule_id: UUID
    changed_by: UUID
    old_approved_seats: int
    new_approved_seats: int
    old_rule_version: str
    new_rule_version: str
    reason: str
    created_at: datetime
    source_label: str = "DEMO"
    notice: str = DEMO_NOTICE


class DeclarationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    programme_id: UUID
    academic_year: AcademicYear
    declared_total: int = Field(ge=0, le=10_000_000)
    basis: Basis


class DeclarationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    programme_id: UUID
    academic_year: str
    declared_total: int
    source_label: str
    basis: str
    declared_by: UUID
    created_at: datetime


class AssessmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    batch_id: UUID
    institution_id: UUID
    programme_id: UUID
    academic_year: str
    scope_revision: int
    current_batch_id: UUID | None
    computed_by: UUID
    computed_at: datetime
    rule_version: str
    source_label: str = "DEMO"


class AssessmentResponse(AssessmentSummary):
    result: dict[str, Any]


class Addition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: AdmissionCategory
    count: int = Field(ge=1, le=1_000_000)


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    programme_id: UUID
    academic_year: AcademicYear
    additions: list[Addition] = Field(min_length=1, max_length=20)


class SimulationResponse(BaseModel):
    institution_id: UUID
    programme_id: UUID
    academic_year: str
    has_current_snapshot: bool
    current_batch_id: UUID | None
    rule_version: str
    source_label: str = "DEMO"
    notice: str = DEMO_NOTICE
    categories: list[dict[str, Any]]
    persisted: bool = False
