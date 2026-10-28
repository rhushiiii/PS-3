from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

RecordStatus = Literal["VALID", "FLAGGED", "INCOMPLETE"]
Severity = Literal["ERROR", "WARNING", "INFO"]
Classification = Literal["ACTIVATION_BLOCKING", "REVIEWABLE"]


class RunResponse(BaseModel):
    id: UUID
    batch_id: UUID
    kind: Literal["INITIAL", "REVALIDATION"]
    requested_by: UUID
    evaluated_at: datetime
    completed_at: datetime
    ruleset_version: str
    ruleset_snapshot: dict[str, Any]
    summary: dict[str, Any]
    cross_current_freshness: Literal["FRESH", "STALE"]
    current_overlap_records: int | None
    historical_assessment: Literal["AS_OF_RUN"] = "AS_OF_RUN"
    validity_label: str = "Local validation only; not official APAAR verification"


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    batch_id: UUID
    record_version_id: UUID | None
    ordinal: int
    rule_code: str
    severity: Severity
    classification: Classification
    field_name: str | None
    explanation: str
    evidence: dict[str, Any]
    evaluated_at: datetime
    cross_current_freshness: Literal["FRESH", "STALE"]
