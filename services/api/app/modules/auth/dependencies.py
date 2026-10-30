from collections.abc import Collection
from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.http import APIError
from app.modules.auth.models import Role, User
from app.modules.auth.services import (
    TokenVerifier,
    unauthenticated,
)
from app.modules.institutions.models import Institution

bearer = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_session)]


def get_current_user(
    request: Request,
    session: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    verifier = cast(TokenVerifier | None, request.app.state.token_verifier)
    if verifier is None or credentials is None:
        raise unauthenticated()
    user = verifier.authenticate(credentials.credentials, request, session)
    if not user.active:
        raise unauthenticated()
    if user.institution_id is not None:
        institution = session.get(Institution, user.institution_id)
        if institution is None or not institution.active:
            raise unauthenticated()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(user: User, allowed: Collection[Role]) -> None:
    """Raise the shared 403 unless the user's role is in `allowed`."""
    if user.role not in allowed:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")


def require_metadata_role(user: User) -> None:
    require_roles(
        user, {Role.INSTITUTION_ADMIN, Role.AICTE_OFFICER, Role.AICTE_MANAGER}
    )
