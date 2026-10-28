"""Export public contracts without connecting to a database or serving requests."""

import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "services" / "api"))

from pydantic import SecretStr  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

config = Settings(
    _env_file=None,
    database_url=SecretStr("postgresql+psycopg://schema:synthetic@127.0.0.1/schema"),
    app_env="local",
    demo_auth=True,
    # Ephemeral schema-export configuration only; no server or token is created.
    demo_auth_secret=SecretStr(secrets.token_urlsafe(48)),
    cors_origins=["http://localhost:3000"],
)
print(json.dumps(create_app(config).openapi(), sort_keys=True))
