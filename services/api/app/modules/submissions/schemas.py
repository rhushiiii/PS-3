from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
)

from app.modules.institutions.schemas import AcademicYear
from app.modules.submissions.models import ProcessingStatus


class UploadContext(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    institution_id: UUID
    programme_id: UUID
    academic_year: AcademicYear
    schema_version: Literal["v1"] = "v1"


class UploadResponse(BaseModel):
    id: UUID
    status: Literal["COMPLETED"] = "COMPLETED"
    validation_performed: Literal[False] = False
    warnings: list[str] = Field(default_factory=list)


class UploadPolicyResponse(BaseModel):
    schema_version: Literal["v1"] = "v1"
    required_headers: list[str]
    encoding: Literal["UTF-8"] = "UTF-8"
    accepts_utf8_bom: Literal[True] = True
    accepted_formats: list[Literal["csv", "xlsx"]] = ["csv", "xlsx"]
    max_file_bytes: int
    max_rows: int
    receive_timeout_seconds: float
    processing_timeout_seconds: float


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scope_id: UUID
    institution_id: UUID
    programme_id: UUID
    academic_year: str
    uploaded_by: UUID
    source: str
    file_sha256: str
    file_size_bytes: int
    schema_version: str
    submission_mode: str
    status: ProcessingStatus
    row_count: int
    base_batch_id: UUID | None
    base_scope_revision: int
    received_at: datetime
    completed_at: datetime | None
    activated_at: datetime | None
    activation_review_id: UUID | None
    snapshot_state: Literal["CANDIDATE", "CURRENT", "PREVIOUS"] = "CANDIDATE"
    activation_provenance: dict[str, Any] | None = None
    activation_eligibility: dict[str, Any] | None = None
    is_current: bool = False
    validation_performed: bool = False
    latest_validation_run_id: UUID | None = None
    validation_summary: dict[str, object] | None = None
    warnings: list[str] = Field(default_factory=list)


class RowResponse(BaseModel):
    id: UUID
    batch_id: UUID
    source_row_number: int
    college_student_id: str
    student_name: str
    academic_year: str
    programme_code: str
    admission_category: str
    enrollment_status: str
    enrollment_date: date | None
    apaar_id_masked: str
    validation_status: Literal["VALID", "FLAGGED", "INCOMPLETE"] | None = None
    validation_run_id: UUID | None = None
    apaar_verification_status: Literal["NOT_CHECKED"] = "NOT_CHECKED"
    abc_reconciliation_status: Literal["NOT_REQUESTED"] = "NOT_REQUESTED"


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    validation_run_id: UUID


class ActivationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    review_id: UUID
    expected_scope_revision: StrictInt = Field(ge=0)
    confirm_complete_replacement: Literal[True]
    acknowledge_review_warnings: Literal[True]
    acknowledge_omissions: StrictBool = False

    @field_validator(
        "confirm_complete_replacement", "acknowledge_review_warnings", mode="before"
    )
    @classmethod
    def explicit_confirmation(cls, value: object) -> object:
        if value is not True:
            raise ValueError("Explicit true confirmation is required")
        return value


class OmittedRecord(BaseModel):
    record_version_id: UUID
    source_row_number: int
    college_student_id: str
    previous_enrollment_status: str
    previous_admission_category: str


class ReviewResponse(BaseModel):
    id: UUID
    batch_id: UUID
    scope_id: UUID
    institution_id: UUID
    programme_id: UUID
    academic_year: str
    validation_run_id: UUID
    reviewed_by: UUID
    created_at: datetime
    expected_scope_revision: int
    expected_current_batch_id: UUID | None
    review_policy_version: str
    review_state: Literal["READY", "BLOCKED", "STALE", "CONSUMED"]
    snapshot: dict[str, Any]
    eligibility: dict[str, Any]
    assessment_now: dict[str, Any]
    omitted_records: list[OmittedRecord] | None
    omission_pagination: dict[str, int] | None
    receipt_label: str = "Information presented for review; not proof it was read"


class ActivationResponse(BaseModel):
    batch_id: UUID
    scope_id: UUID
    review_id: UUID
    validation_run_id: UUID
    previous_batch_id: UUID | None
    scope_revision: int
    activated_by: UUID
    activated_at: datetime
    counts: dict[str, Any]
    source_label: Literal["DEMO"] = "DEMO"
