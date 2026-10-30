import base64
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_validation import activate_demo, csv_data, upload

from app.core.config import Settings
from app.core.database import Base
from app.modules.audit.models import AuditEvent
from app.modules.credentials import tokens
from app.modules.credentials.models import (
    AdmissionCredential,
    CredentialRevocation,
    CredentialVerification,
)
from app.modules.credentials.services import utc_now
from app.modules.submissions.models import StudentRecordVersion

SEED = bytes(range(32))
APAAR = "900000000001"
STUDENT_NAME = "Synthetic One"
Headers = Callable[[str], dict[str, str]]


@pytest.fixture(autouse=True)
def signing_key(demo_settings: Settings) -> None:
    demo_settings.credential_signing_key = SecretStr(base64.b64encode(SEED).decode())


def activated_record(
    client: TestClient,
    auth_headers: Headers,
    session: Session,
    *,
    institution: str = "cedar",
    **changes: str,
) -> str:
    admin = auth_headers(f"{institution}_admin")
    identifier = upload(client, admin, csv_data(**changes), institution=institution)
    activate_demo(client, identifier, admin)
    record = session.scalar(
        select(StudentRecordVersion).where(StudentRecordVersion.batch_id == identifier)
    )
    assert record is not None
    return str(record.id)


def issue(client: TestClient, headers: dict[str, str], record: str) -> Any:
    return client.post(
        "/api/v1/credentials", headers=headers, json={"record_version_id": record}
    )


def verify(
    client: TestClient,
    headers: dict[str, str],
    token: str,
    *,
    purpose: str | None = "ADMISSION_CHECK",
    consent_ref: str | None = "consent-demo-1",
) -> Any:
    body: dict[str, str] = {"token": token}
    if purpose is not None:
        body["purpose"] = purpose
    if consent_ref is not None:
        body["consent_ref"] = consent_ref
    return client.post("/api/v1/credentials/verify", headers=headers, json=body)


def issued_token(
    client: TestClient, auth_headers: Headers, session: Session, **changes: str
) -> str:
    record = activated_record(client, auth_headers, session, **changes)
    response = issue(client, auth_headers("demo_officer"), record)
    assert response.status_code == 201, response.text
    return str(response.json()["token"])


def resign(settings: Settings, token: str, **overrides: Any) -> str:
    """Validly sign a modified copy of a token's header/payload (forgery helper)."""
    header_part, payload_part, _ = token.split(".")
    header = json.loads(tokens.b64url_decode(header_part))
    payload = json.loads(tokens.b64url_decode(payload_part))
    header.update(overrides.get("header", {}))
    payload.update(overrides.get("payload", {}))
    key = tokens.private_key(settings)
    assert key is not None
    signing_input = (
        tokens.b64url_encode(tokens.canonical_json(header))
        + "."
        + tokens.b64url_encode(tokens.canonical_json(payload))
    )
    return signing_input + "." + tokens.b64url_encode(key.sign(signing_input.encode()))


def test_issue_and_verify_valid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    record = activated_record(client, auth_headers, seeded_session)
    response = issue(client, auth_headers("demo_officer"), record)
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["source_label"] == "DEMO"
    token = body["token"]
    header_part, payload_part, signature_part = token.split(".")
    header = json.loads(tokens.b64url_decode(header_part))
    payload = json.loads(tokens.b64url_decode(payload_part))
    assert header == {"alg": "EdDSA", "typ": "PRAVYA-CRED", "kid": "demo-key-1"}
    assert payload["iss"] == "PRAVYA-DEMO-ISSUER"
    assert payload["jti"] == body["credential"]["id"]
    assert payload["exp"] - payload["iat"] == 365 * 86400
    assert payload["claims"] == {
        "institution_name": "Demo Cedar Institute",
        "programme_code": "DEMO-COMP",
        "academic_year": "2026-27",
        "admission_category": "REGULAR",
        "enrollment_status": "ACTIVE",
        "source_label": "DEMO",
    }
    assert len(tokens.b64url_decode(signature_part)) == 64

    verifier = auth_headers("demo_verifier")
    result = verify(client, verifier, token)
    assert result.status_code == 200, result.text
    outcome = result.json()
    assert outcome["outcome"] == "VALID"
    assert outcome["source_label"] == "DEMO"
    assert set(outcome["claims"]) == {
        "institution_name",
        "programme_code",
        "academic_year",
        "admission_category",
        "enrollment_status",
        "issued_at",
        "expires_at",
    }
    assert outcome["claims"]["institution_name"] == "Demo Cedar Institute"
    # Officers may verify too.
    assert verify(client, auth_headers("demo_officer_2"), token).json()["outcome"] == (
        "VALID"
    )


def test_claims_and_token_carry_no_apaar_or_name(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    decoded = "".join(
        tokens.b64url_decode(part).decode() for part in token.split(".")[:2]
    )
    assert APAAR not in decoded and STUDENT_NAME not in decoded
    assert "DEMO-ONE" not in decoded
    result = verify(client, auth_headers("demo_verifier"), token)
    assert APAAR not in result.text and STUDENT_NAME not in result.text


def test_tampered_payload_is_invalid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    header, payload, signature = token.split(".")
    data = json.loads(tokens.b64url_decode(payload))
    data["claims"]["admission_category"] = "NRI"
    forged = ".".join(
        [header, tokens.b64url_encode(tokens.canonical_json(data)), signature]
    )
    result = verify(client, auth_headers("demo_verifier"), forged)
    assert result.status_code == 200
    assert result.json() == {
        **result.json(),
        "outcome": "INVALID",
        "claims": None,
    }


def test_tampered_signature_is_invalid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    header, payload, signature = token.split(".")
    raw = bytearray(tokens.b64url_decode(signature))
    raw[0] ^= 1
    forged = ".".join([header, payload, tokens.b64url_encode(bytes(raw))])
    result = verify(client, auth_headers("demo_verifier"), forged)
    assert result.json()["outcome"] == "INVALID"
    assert result.json()["claims"] is None


@pytest.mark.parametrize(
    "mangle",
    [
        lambda t: "",
        lambda t: "not-a-token",
        lambda t: t + ".extra",
        lambda t: t.rsplit(".", 1)[0],
        lambda t: "!!!." + ".".join(t.split(".")[1:]),
        lambda t: t.replace(".", ".é", 1),
        lambda t: t[:-5] + "A" * 5,
    ],
)
def test_malformed_tokens_are_invalid(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
    mangle: Callable[[str], str],
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    bad = mangle(token) or "x"
    result = verify(client, auth_headers("demo_verifier"), bad)
    assert result.status_code == 200, result.text
    assert result.json()["outcome"] == "INVALID"
    assert result.json()["claims"] is None


def test_alg_none_and_other_algs_are_invalid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    verifier = auth_headers("demo_verifier")
    header, payload, _ = token.split(".")
    none_header = tokens.b64url_encode(
        tokens.canonical_json(
            {"alg": "none", "typ": "PRAVYA-CRED", "kid": "demo-key-1"}
        )
    )
    assert verify(client, verifier, f"{none_header}.{payload}.").json()["outcome"] == (
        "INVALID"
    )
    # Even a correctly produced signature is refused when the header names another alg.
    for alg in ("none", "HS256", "RS256", "eddsa"):
        forged = resign(tokens_settings(client), token, header={"alg": alg})
        assert verify(client, verifier, forged).json()["outcome"] == "INVALID"
    assert header  # original header untouched


def tokens_settings(client: TestClient) -> Settings:
    app = client.app
    assert isinstance(app, FastAPI)
    settings = app.state.settings
    assert isinstance(settings, Settings)
    return settings


def test_wrong_issuer_unknown_kid_and_typ_are_invalid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    settings = tokens_settings(client)
    verifier = auth_headers("demo_verifier")
    for forged in (
        resign(settings, token, payload={"iss": "SOMEONE-ELSE"}),
        resign(settings, token, header={"kid": "other-key"}),
        resign(settings, token, header={"typ": "JWT"}),
        resign(settings, token, payload={"jti": "not-a-uuid"}),
    ):
        result = verify(client, verifier, forged)
        assert result.json()["outcome"] == "INVALID"
        assert result.json()["claims"] is None


def test_validly_signed_token_for_unknown_credential_is_invalid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    forged = resign(
        tokens_settings(client),
        token,
        payload={"jti": "00000000-0000-4000-8000-000000000000"},
    )
    result = verify(client, auth_headers("demo_verifier"), forged)
    assert result.json()["outcome"] == "INVALID"
    assert result.json()["claims"] is None


def test_signature_from_different_key_is_invalid(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    attacker = tokens_settings(client).model_copy(
        update={
            "credential_signing_key": SecretStr(
                base64.b64encode(bytes(reversed(range(32)))).decode()
            )
        }
    )
    forged = resign(attacker, token)
    assert verify(client, auth_headers("demo_verifier"), forged).json()["outcome"] == (
        "INVALID"
    )


def test_expired_credential(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
    application: FastAPI,
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    later = datetime.now(UTC) + timedelta(days=366)
    application.dependency_overrides[utc_now] = lambda: later
    result = verify(client, auth_headers("demo_verifier"), token)
    assert result.json()["outcome"] == "EXPIRED"
    assert result.json()["claims"]["institution_name"] == "Demo Cedar Institute"


def test_ttl_setting_controls_expiry(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
    demo_settings: Settings,
    application: FastAPI,
) -> None:
    demo_settings.credential_ttl_days = 1
    token = issued_token(client, auth_headers, seeded_session)
    verifier = auth_headers("demo_verifier")
    assert verify(client, verifier, token).json()["outcome"] == "VALID"
    later = datetime.now(UTC) + timedelta(days=2)
    application.dependency_overrides[utc_now] = lambda: later
    assert verify(client, verifier, token).json()["outcome"] == "EXPIRED"


def test_revoked_credential_returns_limited_claims(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    record = activated_record(client, auth_headers, seeded_session)
    admin = auth_headers("cedar_admin")
    issued = issue(client, admin, record).json()
    revoke = client.post(
        f"/api/v1/credentials/{issued['credential']['id']}/revoke",
        headers=admin,
        json={"reason": "Issued in error (synthetic)"},
    )
    assert revoke.status_code == 200, revoke.text
    result = verify(client, auth_headers("demo_verifier"), issued["token"])
    assert result.json()["outcome"] == "REVOKED"
    assert set(result.json()["claims"]) == {
        "institution_name",
        "programme_code",
        "academic_year",
        "admission_category",
        "enrollment_status",
        "issued_at",
        "expires_at",
    }
    assert "Issued in error" not in result.text
    again = client.post(
        f"/api/v1/credentials/{issued['credential']['id']}/revoke",
        headers=admin,
        json={"reason": "Second attempt"},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "CREDENTIAL_ALREADY_REVOKED"
    listing = client.get("/api/v1/credentials", headers=admin).json()["data"]
    assert listing[0]["revoked"] is True and listing[0]["revoked_at"]
    audit = seeded_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "CREDENTIAL_REVOKED")
    ).all()
    assert [str(e.entity_id) for e in audit] == [issued["credential"]["id"]]
    assert "Issued in error" not in str(audit[0].metadata_redacted)


def test_revoke_validation_and_scope(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    record = activated_record(client, auth_headers, seeded_session)
    issued = issue(client, auth_headers("cedar_admin"), record).json()
    url = f"/api/v1/credentials/{issued['credential']['id']}/revoke"
    assert (
        client.post(url, headers=auth_headers("cedar_admin"), json={"reason": "x"})
    ).status_code == 422
    assert (
        client.post(url, headers=auth_headers("cedar_admin"), json={})
    ).status_code == 422
    for alias, status in (
        ("maple_admin", 404),
        ("demo_verifier", 403),
        ("demo_manager", 403),
    ):
        response = client.post(url, headers=auth_headers(alias), json={"reason": "abc"})
        assert response.status_code == status, alias
    assert (
        seeded_session.scalar(select(func.count()).select_from(CredentialRevocation))
        == 0
    )
    ok = client.post(
        url, headers=auth_headers("demo_officer"), json={"reason": "officer decision"}
    )
    assert ok.status_code == 200


def test_signing_key_unset(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
    demo_settings: Settings,
) -> None:
    record = activated_record(client, auth_headers, seeded_session)
    token = str(issue(client, auth_headers("demo_officer"), record).json()["token"])
    demo_settings.credential_signing_key = None
    unavailable = issue(client, auth_headers("demo_officer"), record)
    assert unavailable.status_code == 422
    assert unavailable.json()["error"]["code"] == "CREDENTIAL_SIGNING_UNAVAILABLE"
    result = verify(client, auth_headers("demo_verifier"), token)
    assert result.status_code == 200
    assert result.json()["outcome"] == "UNAVAILABLE"
    assert result.json()["claims"] is None
    logged = seeded_session.scalars(select(CredentialVerification)).all()
    assert [(row.outcome, row.credential_id) for row in logged] == [
        ("UNAVAILABLE", None)
    ]
    assert (
        seeded_session.scalar(select(func.count()).select_from(AdmissionCredential))
        == 1
    )


def test_invalid_signing_key_is_rejected_at_configuration(
    demo_settings: Settings,
) -> None:
    for bad in ("not base64!", base64.b64encode(b"short").decode()):
        with pytest.raises(ValueError, match="CREDENTIAL_SIGNING_KEY") as error:
            Settings(
                _env_file=None,
                database_url=demo_settings.database_url,
                credential_signing_key=SecretStr(bad),
            )
        assert bad not in str(error.value)


@pytest.mark.parametrize(
    "omit",
    [{"purpose": None}, {"consent_ref": None}, {"purpose": "", "consent_ref": "c"}],
)
def test_missing_purpose_or_consent_is_denied_without_log(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
    omit: dict[str, str | None],
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    kwargs: dict[str, Any] = omit
    result = verify(client, auth_headers("demo_verifier"), token, **kwargs)
    assert result.status_code == 422
    assert token not in result.text
    assert (
        seeded_session.scalar(select(func.count()).select_from(CredentialVerification))
        == 0
    )


def test_verification_log_rows_and_visibility(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    verifier = auth_headers("demo_verifier")
    officer = auth_headers("demo_officer_2")
    verify(client, verifier, token, purpose="CHECK_A", consent_ref="consent-a")
    verify(client, verifier, "garbage", purpose="CHECK_B", consent_ref="consent-b")
    verify(client, officer, token, purpose="CHECK_C", consent_ref="consent-c")

    mine = client.get("/api/v1/credentials/verifications", headers=verifier).json()
    assert mine["pagination"]["total"] == 2
    assert [row["outcome"] for row in mine["data"]] == ["INVALID", "VALID"]
    assert {row["purpose"] for row in mine["data"]} == {"CHECK_A", "CHECK_B"}
    # Unverified input never gets a credential id.
    assert mine["data"][0]["credential_id"] is None
    assert mine["data"][1]["credential_id"] is not None
    assert "token" not in mine["data"][0]

    everything = client.get(
        "/api/v1/credentials/verifications?page_size=2&page=1", headers=officer
    ).json()
    assert everything["pagination"] == {"page": 1, "page_size": 2, "total": 3}
    assert len(everything["data"]) == 2


def test_tokens_are_never_persisted_or_audited(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    verify(client, auth_headers("demo_verifier"), token)
    verify(client, auth_headers("demo_verifier"), token + "x")
    seeded_session.flush()
    hits: list[str] = []
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            found = seeded_session.scalar(
                text(
                    f'SELECT count(*) FROM "{table.name}" '
                    f'WHERE strpos("{column.name}"::text, :needle) > 0'
                ),
                {"needle": token.split(".")[2]},
            )
            hits += [f"{table.name}.{column.name}"] * (found or 0)
            found = seeded_session.scalar(
                text(
                    f'SELECT count(*) FROM "{table.name}" '
                    f'WHERE strpos("{column.name}"::text, :needle) > 0'
                ),
                {"needle": token.split(".")[1]},
            )
            hits += [f"{table.name}.{column.name}"] * (found or 0)
    assert hits == []


def test_issue_requires_current_active_record(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    # Superseded: a replacement snapshot makes the first record non-current.
    first = activated_record(client, auth_headers, seeded_session)
    activated_record(
        client, auth_headers, seeded_session, college_student_id="DEMO-TWO"
    )
    stale = issue(client, officer, first)
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "CREDENTIAL_RECORD_NOT_CURRENT"
    # Withdrawn records in the current snapshot are not eligible either.
    withdrawn = activated_record(
        client,
        auth_headers,
        seeded_session,
        institution="maple",
        enrollment_status="WITHDRAWN",
    )
    response = issue(client, auth_headers("maple_admin"), withdrawn)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CREDENTIAL_RECORD_NOT_ACTIVE"
    # Never-activated upload.
    admin = auth_headers("willow_admin")
    batch = upload(client, admin, institution="willow")
    candidate = seeded_session.scalar(
        select(StudentRecordVersion).where(StudentRecordVersion.batch_id == batch)
    )
    assert candidate is not None
    assert issue(client, officer, str(candidate.id)).status_code == 409
    assert (
        seeded_session.scalar(select(func.count()).select_from(AdmissionCredential))
        == 0
    )


def test_issue_scope_and_roles(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    record = activated_record(client, auth_headers, seeded_session)
    assert issue(client, auth_headers("maple_admin"), record).status_code == 404
    for alias in ("demo_verifier", "demo_manager"):
        assert issue(client, auth_headers(alias), record).status_code == 403
    assert (
        issue(
            client,
            auth_headers("demo_officer"),
            "00000000-0000-4000-8000-000000000000",
        ).status_code
        == 404
    )
    own = issue(client, auth_headers("cedar_admin"), record)
    assert own.status_code == 201
    audit = seeded_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "CREDENTIAL_ISSUED")
    ).all()
    assert len(audit) == 1
    assert str(audit[0].entity_id) == own.json()["credential"]["id"]
    assert own.json()["token"] not in str(audit[0].metadata_redacted)
    assert audit[0].metadata_redacted == {
        "actor_kind": "USER",
        "source_label": "DEMO",
    }


def test_list_is_scoped_and_has_no_tokens(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    cedar = activated_record(client, auth_headers, seeded_session)
    maple = activated_record(client, auth_headers, seeded_session, institution="maple")
    issue(client, auth_headers("cedar_admin"), cedar)
    issue(client, auth_headers("maple_admin"), maple)
    own = client.get("/api/v1/credentials", headers=auth_headers("cedar_admin"))
    assert own.json()["pagination"]["total"] == 1
    assert "token" not in own.text
    everything = client.get(
        "/api/v1/credentials", headers=auth_headers("demo_officer_2")
    )
    assert everything.json()["pagination"]["total"] == 2
    for alias in ("demo_verifier", "demo_manager"):
        assert (
            client.get("/api/v1/credentials", headers=auth_headers(alias)).status_code
            == 403
        )
    assert client.get("/api/v1/credentials").status_code == 401


def test_verify_role_matrix(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    for alias in ("cedar_admin", "demo_manager"):
        denied = verify(client, auth_headers(alias), token)
        assert denied.status_code == 403
        assert (
            client.get(
                "/api/v1/credentials/verifications", headers=auth_headers(alias)
            ).status_code
            == 403
        )
    assert verify(client, {}, token).status_code == 401
    assert (
        seeded_session.scalar(select(func.count()).select_from(CredentialVerification))
        == 0
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/submissions",
        "/api/v1/records",
        "/api/v1/cases",
        "/api/v1/cases/assignees",
        "/api/v1/institutions",
        "/api/v1/notifications",
        "/api/v1/integrity/overview",
    ],
)
def test_verifier_has_no_other_access(
    client: TestClient, auth_headers: Headers, path: str
) -> None:
    response = client.get(path, headers=auth_headers("demo_verifier"))
    assert response.status_code == 403, (path, response.text)


def test_verifier_cannot_use_other_writes(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    record = activated_record(client, auth_headers, seeded_session)
    verifier = auth_headers("demo_verifier")
    response = client.post(
        f"/api/v1/records/{record}/apaar-verify",
        headers=verifier,
        json={"purpose": "X", "consent_ref": "c"},
    )
    assert response.status_code == 403
    assert client.get(f"/api/v1/records/{record}", headers=verifier).status_code == 403
    assert client.get("/api/v1/me", headers=verifier).json()["role"] == (
        "AUTHORIZED_VERIFIER"
    )


def test_credential_rows_are_immutable(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    token = issued_token(client, auth_headers, seeded_session)
    verify(client, auth_headers("demo_verifier"), token)
    credential = seeded_session.scalar(select(AdmissionCredential))
    assert credential is not None
    credential.expires_at = credential.expires_at + timedelta(days=1)
    with pytest.raises(DBAPIError):
        seeded_session.flush()
    seeded_session.rollback()
    log = seeded_session.scalar(select(CredentialVerification))
    assert log is not None
    seeded_session.delete(log)
    with pytest.raises(DBAPIError):
        seeded_session.flush()
    seeded_session.rollback()
