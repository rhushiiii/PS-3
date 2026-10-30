from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.modules.cases.models import (
    CaseCategory,
    CaseEventAction,
    CasePriority,
    CaseSeverity,
    CaseStatus,
)

CaseAction = Literal[
    "COMMENT",
    "ASSIGNED",
    "START_REVIEW",
    "REQUEST_CORRECTION",
    "RESPONSE_SUBMITTED",
    "UPDATED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
]


class CaseCreateRequest(BaseModel):
    category: CaseCategory
    summary: str = Field(min_length=1, max_length=2000)
    record_version_ids: list[UUID] = Field(min_length=1, max_length=50)
    priority: CasePriority = "MEDIUM"
    severity: CaseSeverity = "MEDIUM"
    due_at: AwareDatetime | None = None


class CaseActionRequest(BaseModel):
    action: CaseAction
    comment: str | None = Field(default=None, max_length=2000)
    assigned_to: UUID | None = None
    resolution_reason: str | None = Field(default=None, max_length=2000)
    priority: CasePriority | None = None
    severity: CaseSeverity | None = None
    due_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def fields_match_action(self) -> Self:
        closing = self.action in {"RESOLVED", "REJECTED"}
        reason_ok = (
            bool((self.resolution_reason or "").strip())
            if closing
            else self.resolution_reason is None
        )
        updates = (self.priority, self.severity, self.due_at)
        if not (
            (self.action == "ASSIGNED") == (self.assigned_to is not None)
            and reason_ok
            and (self.action == "UPDATED") == any(v is not None for v in updates)
        ):
            raise ValueError("Fields do not match the requested action")
        return self


class AssigneeResponse(BaseModel):
    id: UUID
    display_name: str


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
    priority: CasePriority
    severity: CaseSeverity
    due_at: datetime | None
    resolution_reason: str | None
    is_overdue: bool
    is_escalated: bool
    age_days: int
    record_version_ids: list[UUID]
    events: list[CaseEventResponse]
