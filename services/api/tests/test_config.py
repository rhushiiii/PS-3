import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    "url", ["sqlite:///app.db", "postgresql://localhost/demo", "not-a-url"]
)
def test_only_psycopg_postgresql_is_accepted(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url=SecretStr(url))


def test_settings_do_not_display_password(settings: Settings) -> None:
    assert "synthetic-secret" not in repr(settings)
