from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

VerificationStatusLiteral = Literal[
    "SIMULATED_MATCH", "SIMULATED_MISMATCH", "PENDING", "SOURCE_UNAVAILABLE"
]


class VerificationRequest(BaseModel):
    purpose: str = Field(min_length=1, max_length=120)
    consent_ref: str = Field(min_length=1, max_length=64)


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
    provenance_label: str = (
        "SIMULATED — not an official government identity verification"
    )
