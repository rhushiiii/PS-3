from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, StringConstraints

VerificationStatusLiteral = Literal[
    "SIMULATED_MATCH",
    "SIMULATED_MISMATCH",
    "PENDING",
    "SOURCE_UNAVAILABLE",
    "SOURCE_TIMEOUT",
]


PROVENANCE_LABEL = "SIMULATED — not an official government identity verification"
FORMAT_NOTE = "format check is local; not identity verification"


class VerificationRequest(BaseModel):
    purpose: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    consent_ref: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    # Only an earlier attempt of the same record in a retryable state is accepted.
    retry_of: UUID | None = None


class FormatValidation(BaseModel):
    valid: bool
    rule: str
    note: str = FORMAT_NOTE


class IdentityVerification(BaseModel):
    status: VerificationStatusLiteral
    source_type: Literal["SIMULATED"] = "SIMULATED"
    provenance_label: str = PROVENANCE_LABEL
    provider_request_id: str | None
    requested_at: datetime
    completed_at: datetime


class VerificationResponse(BaseModel):
    id: UUID
    record_version_id: UUID
    batch_id: UUID
    requested_by: UUID
    adapter_type: str
    status: VerificationStatusLiteral
    external_reference: str | None
    evidence: dict[str, Any]
    requested_at: datetime
    completed_at: datetime
    provenance_label: str = PROVENANCE_LABEL
    provider_request_id: str | None
    retry_of_id: UUID | None
    format_validation: FormatValidation
    identity_verification: IdentityVerification
