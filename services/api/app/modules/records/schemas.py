from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.modules.cases.models import CasePriority, CaseSeverity, CaseStatus
from app.modules.validation.schemas import FindingResponse, RecordStatus
from app.modules.verification.schemas import VerificationStatusLiteral

SnapshotState = Literal["CURRENT", "SUPERSEDED", "CANDIDATE"]


class RecordRow(BaseModel):
    record_version_id: UUID
    institution_id: UUID
    institution_name: str
    programme_id: UUID
    programme_code: str
    programme_name: str
    academic_year: str
    college_student_id: str
    student_name: str
    masked_apaar: str
    category: str
    enrollment_status: str
    enrollment_date: date | None
    # Status in the batch's latest completed validation run; None if never validated.
    validation_status: RecordStatus | None
    batch_id: UUID
    is_current: bool
    snapshot_state: SnapshotState
    source_label: Literal["DEMO"] = "DEMO"


class Provenance(BaseModel):
    batch_id: UUID
    received_at: datetime
    source: str
    snapshot_state: SnapshotState
    activated_at: datetime | None
    superseded_by_batch_id: UUID | None


class VerificationSummary(BaseModel):
    status: VerificationStatusLiteral
    adapter_type: str
    source_type: Literal["SIMULATED"] = "SIMULATED"
    requested_at: datetime
    completed_at: datetime
    provenance_label: str


class RelatedCase(BaseModel):
    id: UUID
    status: CaseStatus
    priority: CasePriority
    severity: CaseSeverity
    is_overdue: bool
    opened_at: datetime


class FieldChange(BaseModel):
    field: str
    previous: str | None
    current: str | None


class HistoryEntry(BaseModel):
    record_version_id: UUID
    batch_id: UUID
    received_at: datetime
    snapshot_state: SnapshotState
    changes: list[FieldChange]
    # APAAR values are never diffed or returned; None for the first version.
    apaar_changed: bool | None


class RecordDetail(RecordRow):
    provenance: Provenance
    snapshot_presence: Literal[
        "IN_LATEST_SNAPSHOT", "NOT_IN_LATEST_SNAPSHOT", "NOT_APPLICABLE"
    ]
    presence_note: str | None
    findings: list[FindingResponse]
    verification: VerificationSummary | None
    cases: list[RelatedCase]
    history: list[HistoryEntry]
