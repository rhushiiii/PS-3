import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.core.pagination import Page, Pagination
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.credentials.models import (
    AdmissionCredential,
    CredentialRevocation,
    CredentialVerification,
)
from app.modules.credentials.schemas import (
    SOURCE_LABEL,
    CredentialSummary,
    IssueResponse,
    Outcome,
    PermittedClaims,
    RevocationResponse,
    VerificationLogEntry,
    VerifyResponse,
)
from app.modules.credentials.tokens import (
    TokenInvalid,
    VerifiedToken,
    canonical_json,
    private_key,
    public_key,
    sign_token,
    verify_token,
)
from app.modules.institutions.models import Institution, Programme
from app.modules.submissions.models import StudentRecordVersion, SubmissionScope

ISSUER_ROLES = {Role.AICTE_OFFICER, Role.INSTITUTION_ADMIN}
VERIFIER_ROLES = {Role.AICTE_OFFICER, Role.AUTHORIZED_VERIFIER}


def utc_now() -> datetime:
    """Clock dependency; tests override it to control expiry."""
    return datetime.now(UTC)


def require_role(user: User, allowed: set[Role]) -> None:
    if user.role not in allowed:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")


def not_found() -> APIError:
    return APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")


def in_scope(user: User, institution_id: UUID) -> bool:
    return user.role == Role.AICTE_OFFICER or user.institution_id == institution_id


def summary(
    credential: AdmissionCredential, revoked_at: datetime | None
) -> CredentialSummary:
    return CredentialSummary(
        id=credential.id,
        record_version_id=credential.record_version_id,
        institution_id=credential.institution_id,
        issued_by=credential.issued_by,
        issued_at=credential.issued_at,
        expires_at=credential.expires_at,
        kid=credential.kid,
        source_label=credential.source_label,
        revoked=revoked_at is not None,
        revoked_at=revoked_at,
    )


def permitted(
    claims: dict[str, str], issued: datetime, expires: datetime
) -> PermittedClaims:
    return PermittedClaims(
        institution_name=claims["institution_name"],
        programme_code=claims["programme_code"],
        academic_year=claims["academic_year"],
        admission_category=claims["admission_category"],
        enrollment_status=claims["enrollment_status"],
        issued_at=issued,
        expires_at=expires,
    )


def issue_credential(
    session: Session,
    user: User,
    record_version_id: UUID,
    settings: Settings,
    now: datetime,
) -> IssueResponse:
    require_role(user, ISSUER_ROLES)
    record = session.get(StudentRecordVersion, record_version_id)
    if record is None or not in_scope(user, record.institution_id):
        raise not_found()
    key = private_key(settings)
    if key is None:
        raise APIError(
            422,
            "CREDENTIAL_SIGNING_UNAVAILABLE",
            "Credential signing is not configured",
        )
    is_current = session.scalar(
        select(SubmissionScope.id).where(
            SubmissionScope.current_batch_id == record.batch_id
        )
    )
    if is_current is None:
        raise APIError(
            409,
            "CREDENTIAL_RECORD_NOT_CURRENT",
            "Credentials need a record in the current activated snapshot",
        )
    if record.enrollment_status.strip().upper() != "ACTIVE":
        raise APIError(
            409,
            "CREDENTIAL_RECORD_NOT_ACTIVE",
            "Credentials can only be issued for ACTIVE enrolment records",
        )
    institution = session.get(Institution, record.institution_id)
    programme = session.get(Programme, record.programme_id)
    if institution is None or programme is None:
        raise not_found()
    claims = {
        "institution_name": institution.name,
        "programme_code": programme.code,
        "academic_year": record.academic_year,
        "admission_category": record.admission_category.strip().upper(),
        "enrollment_status": "ACTIVE",
        "source_label": SOURCE_LABEL,
    }
    issued = now.replace(microsecond=0)
    expires = issued + timedelta(days=settings.credential_ttl_days)
    credential = AdmissionCredential(
        id=uuid4(),
        record_version_id=record.id,
        institution_id=record.institution_id,
        issued_by=user.id,
        issued_at=issued,
        expires_at=expires,
        kid=settings.credential_key_id,
        claims_sha256=hashlib.sha256(canonical_json(claims)).hexdigest(),
        source_label=SOURCE_LABEL,
    )
    token = sign_token(
        key,
        settings,
        jti=str(credential.id),
        issued_at=int(issued.timestamp()),
        expires_at=int(expires.timestamp()),
        claims=claims,
    )
    session.add(credential)
    session.flush()
    record_action(
        session,
        actor_id=user.id,
        institution_id=record.institution_id,
        action="CREDENTIAL_ISSUED",
        entity_type="admission_credentials",
        entity_id=credential.id,
    )
    session.commit()
    return IssueResponse(
        credential=summary(credential, None),
        token=token,
        claims=permitted(claims, issued, expires),
    )


def list_credentials(
    session: Session, user: User, page: int, page_size: int
) -> Page[CredentialSummary]:
    require_role(user, ISSUER_ROLES)
    statement = select(AdmissionCredential, CredentialRevocation.revoked_at).outerjoin(
        CredentialRevocation,
        CredentialRevocation.credential_id == AdmissionCredential.id,
    )
    if user.role == Role.INSTITUTION_ADMIN:
        statement = statement.where(
            AdmissionCredential.institution_id == user.institution_id
        )
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.execute(
        statement.order_by(
            AdmissionCredential.issued_at.desc(), AdmissionCredential.id.desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page[CredentialSummary](
        data=[summary(credential, revoked_at) for credential, revoked_at in rows],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


def revoke_credential(
    session: Session, user: User, credential_id: UUID, reason: str
) -> RevocationResponse:
    require_role(user, ISSUER_ROLES)
    credential = session.get(AdmissionCredential, credential_id)
    if credential is None or not in_scope(user, credential.institution_id):
        raise not_found()
    revocation = CredentialRevocation(
        id=uuid4(), credential_id=credential.id, revoked_by=user.id, reason=reason
    )
    conflict = APIError(
        409, "CREDENTIAL_ALREADY_REVOKED", "Credential is already revoked"
    )
    if session.scalar(
        select(CredentialRevocation.id).where(
            CredentialRevocation.credential_id == credential.id
        )
    ):
        raise conflict
    try:
        with session.begin_nested():
            session.add(revocation)
            session.flush()
    except IntegrityError:
        raise conflict from None
    session.refresh(revocation)
    record_action(
        session,
        actor_id=user.id,
        institution_id=credential.institution_id,
        action="CREDENTIAL_REVOKED",
        entity_type="admission_credentials",
        entity_id=credential.id,
    )
    session.commit()
    return RevocationResponse(
        credential_id=credential.id,
        revoked_by=user.id,
        revoked_at=revocation.revoked_at,
    )


def assess_token(
    session: Session, token: str, settings: Settings, now: datetime
) -> tuple[Outcome, UUID | None, VerifiedToken | None]:
    """Signature first; the database only adds revocation, never authenticity."""
    public = public_key(settings)
    if public is None:
        return "UNAVAILABLE", None, None
    try:
        verified = verify_token(token, public, settings)
        credential_id = UUID(verified.jti)
    except (TokenInvalid, ValueError):
        return "INVALID", None, None
    credential = session.get(AdmissionCredential, credential_id)
    if (
        credential is None
        or credential.kid != settings.credential_key_id
        or credential.claims_sha256
        != hashlib.sha256(canonical_json(verified.claims)).hexdigest()
        or int(credential.expires_at.timestamp()) != verified.expires_at
    ):
        return "INVALID", None, None
    revoked = session.scalar(
        select(CredentialRevocation.id).where(
            CredentialRevocation.credential_id == credential.id
        )
    )
    if revoked is not None:
        return "REVOKED", credential.id, verified
    if int(now.timestamp()) >= verified.expires_at:
        return "EXPIRED", credential.id, verified
    return "VALID", credential.id, verified


def verify_credential(
    session: Session,
    user: User,
    token: str,
    purpose: str,
    consent_ref: str,
    settings: Settings,
    now: datetime,
) -> VerifyResponse:
    require_role(user, VERIFIER_ROLES)
    outcome, credential_id, verified = assess_token(session, token, settings, now)
    # The log row never receives the token, only the outcome and declared purpose.
    log = CredentialVerification(
        id=uuid4(),
        credential_id=credential_id,
        verifier_user_id=user.id,
        outcome=outcome,
        purpose=purpose,
        consent_ref=consent_ref,
    )
    session.add(log)
    session.flush()
    session.refresh(log)
    session.commit()
    claims = None
    if verified is not None:
        claims = permitted(
            verified.claims,
            datetime.fromtimestamp(verified.issued_at, UTC),
            datetime.fromtimestamp(verified.expires_at, UTC),
        )
    return VerifyResponse(
        verification_id=log.id,
        outcome=outcome,
        claims=claims,
        verified_at=log.verified_at,
    )


def verification_log(
    session: Session, user: User, page: int, page_size: int
) -> Page[VerificationLogEntry]:
    require_role(user, VERIFIER_ROLES)
    statement = select(CredentialVerification)
    if user.role == Role.AUTHORIZED_VERIFIER:
        statement = statement.where(CredentialVerification.verifier_user_id == user.id)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.scalars(
        statement.order_by(
            CredentialVerification.verified_at.desc(), CredentialVerification.id.desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page[VerificationLogEntry](
        data=[VerificationLogEntry.model_validate(row) for row in rows],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )
