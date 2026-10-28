from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CaseStatus = Literal[
    "OPEN", "AWAITING_CORRECTION", "UNDER_REVIEW", "RESOLVED", "CLOSED"
]
CaseCategory = Literal[
    "POTENTIAL_DUPLICATE", "APAAR_MISMATCH", "INTAKE_DISCREPANCY", "OTHER"
]
CaseAction = Literal["COMMENT", "REQUEST_CORRECTION", "ASSIGNED", "RESOLVED", "CLOSED"]
CaseEventAction = Literal[
    "OPENED",
    "COMMENT",
    "REQUEST_CORRECTION",
    "CORRECTION_RECEIVED",
    "ASSIGNED",
    "RESOLVED",
    "CLOSED",
]


class CaseCreateRequest(BaseModel):
    category: CaseCategory
    summary: str = Field(min_length=1, max_length=2000)
    record_version_ids: list[UUID] = Field(min_length=1, max_length=50)


class CaseActionRequest(BaseModel):
    action: CaseAction
    comment: str | None = Field(default=None, max_length=2000)
    assigned_to: UUID | None = None


class CaseEventResponse(BaseModel):
    id: UUID
    case_id: UUID
    actor_id: UUID | None
    action: CaseEventAction
    comment: str | None
    linked_batch_id: UUID | None
    created_at: datetime


class CaseResponse(BaseModel):
    id: UUID
    institution_id: UUID
    opened_by: UUID
    assigned_to: UUID | None
    status: CaseStatus
    category: CaseCategory
    summary: str
    opened_at: datetime
    resolved_at: datetime | None
    record_version_ids: list[UUID]
    events: list[CaseEventResponse]
