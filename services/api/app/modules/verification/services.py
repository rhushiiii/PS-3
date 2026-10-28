from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.submissions.models import StudentRecordVersion
from app.modules.validation.rules import token_hash, valid_token
from app.modules.verification.models import ApaarVerification
from app.modules.verification.provider import MockAPAARProvider
from app.modules.verification.schemas import VerificationResponse


def require_verification_role(user: User, *, requesting: bool = False) -> None:
    allowed = (
        {Role.AICTE_OFFICER}
        if requesting
        else {Role.INSTITUTION_ADMIN, Role.AICTE_OFFICER}
    )
    if user.role not in allowed:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")


def scoped_record(
    session: Session, user: User, record_version_id: UUID
) -> StudentRecordVersion:
    require_verification_role(user)
    record = session.get(StudentRecordVersion, record_version_id)
    if record is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    if user.role == Role.INSTITUTION_ADMIN and record.institution_id != (
        user.institution_id
    ):
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return record


def matching_key(settings: Settings) -> bytes:
    secret = settings.apaar_matching_key
    if secret is None or len(secret.get_secret_value().encode()) < 32:
        raise APIError(
            422,
            "MATCHING_CONFIGURATION_UNAVAILABLE",
            "APAAR matching requires an environment key of at least 32 bytes",
        )
    return secret.get_secret_value().encode()


def verification_response(verification: ApaarVerification) -> VerificationResponse:
    return VerificationResponse(
        id=verification.id,
        record_version_id=verification.record_version_id,
        batch_id=verification.batch_id,
        requested_by=verification.requested_by,
        adapter_type=verification.adapter_type,
        status=verification.status,
        external_reference=verification.external_reference,
        evidence=verification.evidence_json_redacted,
        requested_at=verification.requested_at,
        completed_at=verification.completed_at,
    )


def request_verification(
    session: Session,
    user: User,
    record_version_id: UUID,
    purpose: str,
    consent_ref: str,
    settings: Settings,
) -> VerificationResponse:
    require_verification_role(user, requesting=True)
    record = scoped_record(session, user, record_version_id)
    key = matching_key(settings)
    token = record.apaar_identifier_encrypted_or_demo_token
    if not valid_token(token, settings.apaar_format_length):
        raise APIError(
            422,
            "INVALID_APAAR_FORMAT",
            "Record APAAR value is not a valid local-format identifier",
        )
    digest_hex = token_hash(token, key).hex()
    requested_at = datetime.now(UTC)
    result = MockAPAARProvider(key).verify(
        digest_hex, purpose=purpose, consent_ref=consent_ref
    )
    verification = ApaarVerification(
        id=uuid4(),
        record_version_id=record.id,
        batch_id=record.batch_id,
        requested_by=user.id,
        adapter_type=result.adapter_type,
        status=result.status,
        external_reference=result.external_reference,
        evidence_json_redacted=result.evidence,
        consent_ref=consent_ref,
        purpose=purpose,
        requested_at=requested_at,
        completed_at=datetime.now(UTC),
    )
    session.add(verification)
    session.flush()
    record_action(
        session,
        actor_id=user.id,
        institution_id=record.institution_id,
        action="APAAR_VERIFICATION_REQUESTED",
        entity_type="apaar_verifications",
        entity_id=verification.id,
    )
    session.commit()
    return verification_response(verification)


def verification_history(
    session: Session, record_version_id: UUID
) -> list[ApaarVerification]:
    return list(
        session.scalars(
            select(ApaarVerification)
            .where(ApaarVerification.record_version_id == record_version_id)
            .order_by(
                ApaarVerification.requested_at.desc(), ApaarVerification.id.desc()
            )
        )
    )
