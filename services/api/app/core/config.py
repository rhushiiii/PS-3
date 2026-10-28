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
    apaar_matching_key: SecretStr | None = None
    apaar_format_length: int = Field(default=12, ge=1, le=64)
    validation_intake_rule_version: str = Field(
        default="DEMO-v1", min_length=1, max_length=64
    )
    validation_processing_timeout_seconds: float = Field(default=30, gt=0)
    validation_max_comparison_records: int = Field(default=100000, ge=1)

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
