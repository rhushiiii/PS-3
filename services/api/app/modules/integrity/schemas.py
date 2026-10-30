from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.pagination import Pagination
from app.modules.integrity.models import Decision

Family = Literal["DATA_QUALITY", "IDENTITY_UNCERTAINTY", "COMPLIANCE"]
Severity = Literal["INFO", "LOW", "MEDIUM", "HIGH"]
Band = Literal["LOW", "MEDIUM", "HIGH"]
FAMILIES: tuple[Family, ...] = ("DATA_QUALITY", "IDENTITY_UNCERTAINTY", "COMPLIANCE")
SEVERITIES: tuple[Severity, ...] = ("INFO", "LOW", "MEDIUM", "HIGH")

DISCLAIMER = (
    "Rule-based review prompts computed from stored DEMO data. They are not fraud "
    "findings or compliance determinations, and are not official verification. "
    "Only AICTE officers decide; omission or missing data is never read as "
    "withdrawal or zero enrolment. Verification results are SIMULATED / DEMO DATA."
)
SCORE_FORMULA = "sum over non-dismissed signals of severity weight"

Reason = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)
]


class EvidenceRefs(BaseModel):
    batch_ids: list[UUID] = []
    validation_run_id: UUID | None = None
    # Counts per validation rule code; never record values.
    finding_rule_counts: dict[str, int] = {}
    case_ids: list[UUID] = []
    assessment_id: UUID | None = None
    # Capped at 20; the total is reported separately.
    record_version_ids: list[UUID] = []
    record_version_total: int = 0


class Signal(BaseModel):
    signal_key: str
    rule_id: str
    family: Family
    severity: Severity
    title: str
    calculation: str
    evidence: EvidenceRefs
    programme_id: UUID | None = None
    academic_year: str | None = None
    recommended_next_action: str
    decision: Decision | None = None
    decision_at: datetime | None = None
    dismissed: bool = False


class FamilyScore(BaseModel):
    family: Family
    signal_count: int
    active_count: int
    weighted_points: int
    max_severity: Severity | None


class ScoreSummary(BaseModel):
    components: list[FamilyScore]
    total_points: int
    band: Band
    formula: str = SCORE_FORMULA
    severity_weights: dict[str, int]
    band_thresholds: dict[str, int]


class SignalsResponse(BaseModel):
    institution_id: UUID
    academic_year: str | None
    programme_id: UUID | None
    generated_at: datetime
    source_label: str = "DEMO"
    disclaimer: str = DISCLAIMER
    parameters: dict[str, float | int]
    score: ScoreSummary
    signals: list[Signal]


class OverviewItem(BaseModel):
    institution_id: UUID
    institution_name: str
    signal_count: int
    active_count: int
    dismissed_count: int
    score: ScoreSummary


class OverviewResponse(BaseModel):
    source_label: str = "DEMO"
    disclaimer: str = DISCLAIMER
    generated_at: datetime
    academic_year: str | None
    band: Band | None
    data: list[OverviewItem]
    pagination: Pagination


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signal_key: str = Field(min_length=1, max_length=300)
    decision: Decision
    reason: Reason


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    signal_key: str
    decision: Decision
    reason: str
    decided_by: UUID
    created_at: datetime
    disclaimer: str = DISCLAIMER
