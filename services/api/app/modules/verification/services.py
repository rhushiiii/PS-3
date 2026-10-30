import hashlib
import json
import secrets
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.submissions.models import StudentRecordVersion
from app.modules.validation.rules import token_hash, valid_token
from app.modules.verification.models import ApaarVerification
from app.modules.verification.provider import (
    APAARProvider,
    MockAPAARProvider,
    VerificationResult,
    VerificationStatus,
)
from app.modules.verification.schemas import (
    FormatValidation,
    IdentityVerification,
    VerificationResponse,
)

RETRYABLE = {
    VerificationStatus.PENDING,
    VerificationStatus.SOURCE_UNAVAILABLE,
    VerificationStatus.SOURCE_TIMEOUT,
}


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


def build_provider(key: bytes) -> APAARProvider:
    """Factory seam: the prototype only ever builds the simulated adapter."""
    return MockAPAARProvider(key)


def call_provider(
    provider: APAARProvider,
    digest_hex: str,
    *,
    purpose: str,
    consent_ref: str,
    timeout_seconds: float,
) -> VerificationResult:
    """Run the provider under a deadline; failure is never a mismatch."""
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(
            provider.verify, digest_hex, purpose=purpose, consent_ref=consent_ref
        )
        return future.result(timeout=timeout_seconds)
    except (FutureTimeout, TimeoutError):
        status, reason = VerificationStatus.SOURCE_TIMEOUT, "PROVIDER_TIMEOUT"
    except Exception:
        # Deliberately no exception text: it could echo an identifier.
        status, reason = VerificationStatus.SOURCE_UNAVAILABLE, "PROVIDER_ERROR"
    finally:
        # Do not wait for a hung adapter; the attempt is already recorded as failed.
        executor.shutdown(wait=False)
    return VerificationResult(
        status=status,
        adapter_type=getattr(provider, "ADAPTER_TYPE", "UNKNOWN"),
        external_reference=None,
        evidence={"source_label": "SIMULATED", "purpose": purpose, "failure": reason},
    )


def format_rule(settings: Settings) -> str:
    return f"ASCII_DIGITS_LENGTH_{settings.apaar_format_length}"


def verification_response(verification: ApaarVerification) -> VerificationResponse:
    rule = verification.evidence_json_redacted.get("format_rule")
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
        provider_request_id=verification.provider_request_id,
        retry_of_id=verification.retry_of_id,
        # A stored attempt always passed the local format check (else 422, no row).
        format_validation=FormatValidation(
            valid=True, rule=rule if isinstance(rule, str) else "LOCAL_FORMAT"
        ),
        identity_verification=IdentityVerification(
            status=verification.status,
            provider_request_id=verification.provider_request_id,
            requested_at=verification.requested_at,
            completed_at=verification.completed_at,
        ),
    )


def request_fingerprint(
    user: User, record_id: UUID, purpose: str, consent_ref: str, retry_of: UUID | None
) -> str:
    canonical = json.dumps(
        [str(user.id), str(record_id), purpose, consent_ref, str(retry_of)],
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def find_replay(
    session: Session, record_id: UUID, key: str, fingerprint: str
) -> ApaarVerification | None:
    existing = session.scalar(
        select(ApaarVerification).where(
            ApaarVerification.record_version_id == record_id,
            ApaarVerification.idempotency_key == key,
        )
    )
    if existing is None:
        return None
    if existing.request_fingerprint != fingerprint:
        raise APIError(
            409,
            "IDEMPOTENCY_KEY_REUSED",
            "Idempotency-Key was already used with a different request",
        )
    return existing


def check_retry(session: Session, record_id: UUID, retry_of: UUID) -> None:
    previous = session.get(ApaarVerification, retry_of)
    if previous is None or previous.record_version_id != record_id:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    if previous.status not in RETRYABLE:
        raise APIError(
            409,
            "RETRY_NOT_ALLOWED",
            "Only pending, unavailable or timed-out attempts can be retried",
        )


def check_attempt_limit(
    session: Session, record_id: UUID, now: datetime, settings: Settings
) -> None:
    attempts = session.scalar(
        select(func.count())
        .select_from(ApaarVerification)
        .where(
            ApaarVerification.record_version_id == record_id,
            ApaarVerification.requested_at >= now - timedelta(hours=24),
        )
    )
    if (attempts or 0) >= settings.apaar_max_attempts_per_day:
        raise APIError(
            429,
            "RETRY_LIMIT",
            "Verification attempt limit reached for this record; try again later",
        )


def request_verification(
    session: Session,
    user: User,
    record_version_id: UUID,
    purpose: str,
    consent_ref: str,
    settings: Settings,
    *,
    retry_of: UUID | None = None,
    idempotency_key: str | None = None,
) -> tuple[VerificationResponse, bool]:
    """Return the response and whether it replays an earlier idempotent request."""
    require_verification_role(user, requesting=True)
    record = scoped_record(session, user, record_version_id)
    fingerprint = request_fingerprint(user, record.id, purpose, consent_ref, retry_of)
    if idempotency_key is not None:
        replay = find_replay(session, record.id, idempotency_key, fingerprint)
        if replay is not None:
            return verification_response(replay), True
    key = matching_key(settings)
    token = record.apaar_identifier_encrypted_or_demo_token
    if not valid_token(token, settings.apaar_format_length):
        raise APIError(
            422,
            "INVALID_APAAR_FORMAT",
            "Record APAAR value is not a valid local-format identifier",
        )
    if retry_of is not None:
        check_retry(session, record.id, retry_of)
    requested_at = datetime.now(UTC)
    check_attempt_limit(session, record.id, requested_at, settings)
    result = call_provider(
        build_provider(key),
        token_hash(token, key).hex(),
        purpose=purpose,
        consent_ref=consent_ref,
        timeout_seconds=settings.apaar_provider_timeout_seconds,
    )
    verification = ApaarVerification(
        id=uuid4(),
        record_version_id=record.id,
        batch_id=record.batch_id,
        requested_by=user.id,
        adapter_type=result.adapter_type,
        status=result.status,
        external_reference=result.external_reference,
        evidence_json_redacted={
            **result.evidence,
            "format_rule": format_rule(settings),
        },
        consent_ref=consent_ref,
        purpose=purpose,
        requested_at=requested_at,
        completed_at=datetime.now(UTC),
        provider_request_id="req_" + secrets.token_hex(12),
        retry_of_id=retry_of,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
    )
    try:
        with session.begin_nested():
            session.add(verification)
            session.flush()
    except IntegrityError:
        # A concurrent request won the unique (record, key) slot; replay it.
        if idempotency_key is None:
            raise
        replay = find_replay(session, record.id, idempotency_key, fingerprint)
        if replay is None:
            raise
        return verification_response(replay), True
    record_action(
        session,
        actor_id=user.id,
        institution_id=record.institution_id,
        action="APAAR_VERIFICATION_REQUESTED",
        entity_type="apaar_verifications",
        entity_id=verification.id,
    )
    session.commit()
    return verification_response(verification), False


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
