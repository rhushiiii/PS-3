from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

SOURCE_LABEL = "DEMO"
PROVENANCE_NOTICE = (
    "DEMO credential signed by a prototype key; not an official AICTE, APAAR "
    "or government document"
)
Outcome = Literal["VALID", "INVALID", "EXPIRED", "REVOKED", "UNAVAILABLE"]


class IssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_version_id: UUID


class PermittedClaims(BaseModel):
    """The only data a verifier may see. No APAAR, no student name."""

    institution_name: str
    programme_code: str
    academic_year: str
    admission_category: str
    enrollment_status: str
    issued_at: datetime
    expires_at: datetime


class CredentialSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_version_id: UUID
    institution_id: UUID
    issued_by: UUID
    issued_at: datetime
    expires_at: datetime
    kid: str
    source_label: str
    revoked: bool = False
    revoked_at: datetime | None = None


class IssueResponse(BaseModel):
    credential: CredentialSummary
    token: str
    claims: PermittedClaims
    source_label: str = SOURCE_LABEL
    notice: str = "The token is shown once and is not stored. " + PROVENANCE_NOTICE


class RevokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)
    ]


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: Annotated[str, StringConstraints(min_length=1, max_length=8192)]
    # Both are mandatory: absence means deny, with no check and no log row.
    purpose: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    consent_ref: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)
    ]


class VerifyResponse(BaseModel):
    verification_id: UUID
    outcome: Outcome
    claims: PermittedClaims | None
    verified_at: datetime
    source_label: str = SOURCE_LABEL
    notice: str = PROVENANCE_NOTICE


class VerificationLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    credential_id: UUID | None
    verifier_user_id: UUID
    outcome: Outcome
    purpose: str
    consent_ref: str
    verified_at: datetime


class RevocationResponse(BaseModel):
    credential_id: UUID
    revoked_by: UUID
    revoked_at: datetime
