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


def test_case_workflow_settings_are_validated(settings: Settings) -> None:
    assert settings.case_due_days_by_priority["URGENT"] == 3
    assert settings.case_escalation_after_days_overdue == 7
    for bad in (
        {"LOW": 30},
        {"LOW": 0, "MEDIUM": 14, "HIGH": 7, "URGENT": 3},
        {"LOW": 30, "MEDIUM": 14, "HIGH": 7, "URGENT": 3, "OTHER": 1},
    ):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                database_url=SecretStr("postgresql+psycopg://u@localhost/d"),
                case_due_days_by_priority=bad,
            )
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url=SecretStr("postgresql+psycopg://u@localhost/d"),
            case_escalation_after_days_overdue=-1,
        )
