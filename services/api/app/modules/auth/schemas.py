from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.models import Role


class DemoLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    demo_alias: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    demo_mode: Literal[True] = True


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: Role
    institution_id: UUID | None
    demo_mode: bool = True
