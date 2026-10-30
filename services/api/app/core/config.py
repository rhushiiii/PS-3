import base64
import binascii
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: SecretStr
    cors_origins: list[str] = ["http://localhost:3000"]
    demo_auth: bool = False
    app_env: Literal["local", "production"] = "production"
    demo_auth_secret: SecretStr | None = None
    demo_token_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    upload_max_rows: int = Field(default=1000, ge=1)
    upload_receive_timeout_seconds: float = Field(default=30, gt=0)
    upload_processing_timeout_seconds: float = Field(default=30, gt=0)
    # Global cap on bytes actually received for every route except the upload route
    # (which keeps UPLOAD_MAX_BYTES and its own receive timeout).
    request_max_bytes: int = Field(default=1024 * 1024, ge=1)
    # Report exports are refused (422 REPORT_TOO_LARGE) above this many data rows.
    report_max_rows: int = Field(default=10000, ge=1)
    # Per-process sliding-window limits, requests per 60 seconds per user (or IP).
    rate_limit_enabled: bool = True
    rate_limit_demo_login_per_minute: int = Field(default=10, ge=1)
    rate_limit_uploads_per_minute: int = Field(default=20, ge=1)
    rate_limit_reviews_per_minute: int = Field(default=30, ge=1)
    rate_limit_exports_per_minute: int = Field(default=10, ge=1)
    rate_limit_credentials_per_minute: int = Field(default=30, ge=1)
    rate_limit_verification_per_minute: int = Field(default=30, ge=1)
    rate_limit_cases_per_minute: int = Field(default=60, ge=1)
    rate_limit_intake_per_minute: int = Field(default=30, ge=1)
    apaar_matching_key: SecretStr | None = None
    apaar_format_length: int = Field(default=12, ge=1, le=64)
    # Simulated provider call budget and per-record attempt cap (rolling 24h).
    apaar_provider_timeout_seconds: float = Field(default=5, gt=0, le=60)
    apaar_max_attempts_per_day: int = Field(default=5, ge=1, le=1000)
    # Ed25519 private seed, base64 of exactly 32 bytes. No default; never logged.
    credential_signing_key: SecretStr | None = None
    credential_key_id: str = Field(default="demo-key-1", min_length=1, max_length=64)
    credential_issuer: str = Field(
        default="PRAVYA-DEMO-ISSUER", min_length=1, max_length=120
    )
    credential_ttl_days: int = Field(default=365, ge=1, le=3650)
    validation_intake_rule_version: str = Field(
        default="DEMO-v1", min_length=1, max_length=64
    )
    validation_processing_timeout_seconds: float = Field(default=30, gt=0)
    validation_max_comparison_records: int = Field(default=100000, ge=1)
    # Env-overridable as JSON, e.g. CASE_DUE_DAYS_BY_PRIORITY='{"LOW":30,...}'.
    case_due_days_by_priority: dict[str, int] = {
        "LOW": 30,
        "MEDIUM": 14,
        "HIGH": 7,
        "URGENT": 3,
    }
    case_escalation_after_days_overdue: int = Field(default=7, ge=0, le=365)
    # Integrity review prompts (rule-based, DEMO defaults, not official thresholds).
    # Share of prior snapshot rows removed or changed that raises a review prompt.
    integrity_change_ratio_threshold: float = Field(default=0.25, gt=0, le=1)
    # REQUEST_CORRECTION events on one case (or in total) that raise a prompt.
    integrity_repeated_corrections_threshold: int = Field(default=2, ge=1, le=100)
    # Days without an activated snapshot before a programme is prompted as stale.
    integrity_stale_days: int = Field(default=90, ge=1, le=3650)
    # Env-overridable as JSON, e.g. INTEGRITY_SEVERITY_WEIGHTS='{"INFO":0,...}'.
    integrity_severity_weights: dict[str, int] = {
        "INFO": 0,
        "LOW": 1,
        "MEDIUM": 3,
        "HIGH": 5,
    }
    # Review-priority bands: points >= medium -> MEDIUM, >= high -> HIGH.
    integrity_band_medium_points: int = Field(default=4, ge=1, le=10000)
    integrity_band_high_points: int = Field(default=10, ge=2, le=10000)

    @model_validator(mode="after")
    def restrict_demo_mode(self) -> Self:
        if not self.demo_auth:
            return self
        if self.app_env != "local":
            raise ValueError("DEMO_AUTH requires APP_ENV=local")
        if (
            self.demo_auth_secret is None
            or len(self.demo_auth_secret.get_secret_value().encode()) < 32
        ):
            raise ValueError(
                "Demo authentication requires a secret of at least 32 bytes"
            )
        for origin in self.cors_origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("Demo CORS origins must be explicit local origins")
        return self

    @field_validator("credential_signing_key")
    @classmethod
    def require_ed25519_seed(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        try:
            seed = base64.b64decode(value.get_secret_value(), validate=True)
        except (binascii.Error, ValueError):
            seed = b""
        if len(seed) != 32:
            raise ValueError("CREDENTIAL_SIGNING_KEY must be base64 of 32 bytes")
        return value

    @field_validator("case_due_days_by_priority")
    @classmethod
    def require_every_priority(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != {"LOW", "MEDIUM", "HIGH", "URGENT"} or any(
            not 1 <= days <= 365 for days in value.values()
        ):
            raise ValueError(
                "CASE_DUE_DAYS_BY_PRIORITY needs LOW, MEDIUM, HIGH and URGENT "
                "with 1-365 days each"
            )
        return value

    @field_validator("integrity_severity_weights")
    @classmethod
    def require_every_severity(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != {"INFO", "LOW", "MEDIUM", "HIGH"} or any(
            not 0 <= points <= 1000 for points in value.values()
        ):
            raise ValueError(
                "INTEGRITY_SEVERITY_WEIGHTS needs INFO, LOW, MEDIUM and HIGH "
                "with 0-1000 points each"
            )
        return value

    @model_validator(mode="after")
    def order_integrity_bands(self) -> Self:
        if self.integrity_band_high_points <= self.integrity_band_medium_points:
            raise ValueError(
                "INTEGRITY_BAND_HIGH_POINTS must exceed INTEGRITY_BAND_MEDIUM_POINTS"
            )
        return self

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
        except ArgumentError:
            raise ValueError("DATABASE_URL must be a PostgreSQL Psycopg URL") from None
        if url.drivername != "postgresql+psycopg" or not url.database:
            raise ValueError("DATABASE_URL must be a PostgreSQL Psycopg URL")
        return value
