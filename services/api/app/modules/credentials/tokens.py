"""Compact Ed25519 JWS for DEMO admission credentials.

Format: base64url(header).base64url(payload).base64url(signature). The signature
check is the only thing that establishes authenticity; a QR code or scan is just
a carrier for this string. Never log or persist a token.
"""

import base64
import binascii
import json
import re
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from app.core.config import Settings

TOKEN_TYPE = "PRAVYA-CRED"
ALGORITHM = "EdDSA"
CLAIM_KEYS = (
    "institution_name",
    "programme_code",
    "academic_year",
    "admission_category",
    "enrollment_status",
    "source_label",
)
_B64URL = re.compile(r"^[A-Za-z0-9_-]*$")


class TokenInvalid(Exception):
    """The token is malformed, forged or not meant for this issuer."""


@dataclass(frozen=True)
class VerifiedToken:
    jti: str
    issued_at: int
    expires_at: int
    claims: dict[str, str]


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    if not _B64URL.fullmatch(text) or len(text) % 4 == 1:
        raise TokenInvalid
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except (binascii.Error, ValueError):
        raise TokenInvalid from None


def canonical_json(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def private_key(settings: Settings) -> Ed25519PrivateKey | None:
    secret = settings.credential_signing_key
    if secret is None:
        return None
    return Ed25519PrivateKey.from_private_bytes(
        base64.b64decode(secret.get_secret_value(), validate=True)
    )


def public_key(settings: Settings) -> Ed25519PublicKey | None:
    key = private_key(settings)
    return key.public_key() if key is not None else None


def sign_token(
    key: Ed25519PrivateKey,
    settings: Settings,
    *,
    jti: str,
    issued_at: int,
    expires_at: int,
    claims: dict[str, str],
) -> str:
    header = {"alg": ALGORITHM, "typ": TOKEN_TYPE, "kid": settings.credential_key_id}
    payload = {
        "iss": settings.credential_issuer,
        "jti": jti,
        "iat": issued_at,
        "exp": expires_at,
        "claims": claims,
    }
    signing_input = (
        b64url_encode(canonical_json(header))
        + "."
        + b64url_encode(canonical_json(payload))
    )
    signature = key.sign(signing_input.encode("ascii"))
    return signing_input + "." + b64url_encode(signature)


def _json_object(data: bytes) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except ValueError:
        raise TokenInvalid from None
    if not isinstance(value, dict):
        raise TokenInvalid
    return value


def verify_token(
    token: str, public: Ed25519PublicKey, settings: Settings
) -> VerifiedToken:
    """Check header, signature, issuer and shape; expiry/revocation are the caller's."""
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenInvalid
    header_bytes, payload_bytes, signature = (b64url_decode(part) for part in parts)
    header = _json_object(header_bytes)
    # Pin the algorithm: never honour "none" or any header-chosen algorithm.
    if (
        header.get("alg") != ALGORITHM
        or header.get("typ") != TOKEN_TYPE
        or header.get("kid") != settings.credential_key_id
    ):
        raise TokenInvalid
    try:
        public.verify(signature, (parts[0] + "." + parts[1]).encode("ascii"))
    except InvalidSignature:
        raise TokenInvalid from None
    payload = _json_object(payload_bytes)
    claims = payload.get("claims")
    jti, issued_at, expires_at = (
        payload.get("jti"),
        payload.get("iat"),
        payload.get("exp"),
    )
    if (
        payload.get("iss") != settings.credential_issuer
        or not isinstance(jti, str)
        or not isinstance(issued_at, int)
        or not isinstance(expires_at, int)
        or isinstance(issued_at, bool)
        or isinstance(expires_at, bool)
        or not isinstance(claims, dict)
        or set(claims) != set(CLAIM_KEYS)
        or not all(isinstance(claims[name], str) for name in CLAIM_KEYS)
    ):
        raise TokenInvalid
    return VerifiedToken(jti, issued_at, expires_at, {k: claims[k] for k in CLAIM_KEYS})
