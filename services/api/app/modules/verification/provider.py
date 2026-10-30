from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from app.modules.validation.rules import token_hash


class VerificationStatus(StrEnum):
    SIMULATED_MATCH = "SIMULATED_MATCH"
    SIMULATED_MISMATCH = "SIMULATED_MISMATCH"
    PENDING = "PENDING"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    adapter_type: str
    external_reference: str | None
    evidence: dict[str, object] = field(default_factory=dict)


class APAARProvider(Protocol):
    """Never contact a real government system; see docs/05_VALIDATION_AND_ABC.md."""

    def verify(
        self, apaar_match_hash_hex: str, *, purpose: str, consent_ref: str
    ) -> VerificationResult: ...


class MockAPAARProvider:
    """Deterministic simulated adapter. Results always carry SIMULATED provenance."""

    ADAPTER_TYPE = "MOCK_V1"
    _FIXTURE_TOKENS: dict[str, VerificationStatus] = {
        "900000000001": VerificationStatus.SIMULATED_MATCH,
        "900000000002": VerificationStatus.SIMULATED_MISMATCH,
        "900000000003": VerificationStatus.SOURCE_UNAVAILABLE,
        "900000000004": VerificationStatus.SOURCE_TIMEOUT,
    }

    def __init__(self, key: bytes) -> None:
        self._fixtures = {
            token_hash(token, key).hex(): status
            for token, status in self._FIXTURE_TOKENS.items()
        }

    def verify(
        self, apaar_match_hash_hex: str, *, purpose: str, consent_ref: str
    ) -> VerificationResult:
        status = self._fixtures.get(apaar_match_hash_hex, VerificationStatus.PENDING)
        return VerificationResult(
            status=status,
            adapter_type=self.ADAPTER_TYPE,
            external_reference=None,
            evidence={
                "source_label": "SIMULATED",
                "purpose": purpose,
            },
        )
