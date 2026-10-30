from alembic import context
from app.core.config import Settings
from app.core.database import Base, build_engine
from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.cases import models as case_models  # noqa: F401
from app.modules.credentials import models as credential_models  # noqa: F401
from app.modules.institutions import models as institution_models  # noqa: F401
from app.modules.intake import models as intake_models  # noqa: F401
from app.modules.integrity import models as integrity_models  # noqa: F401
from app.modules.notifications import models as notification_models  # noqa: F401
from app.modules.submissions import models as submission_models  # noqa: F401
from app.modules.validation import models as validation_models  # noqa: F401
from app.modules.verification import models as verification_models  # noqa: F401

# Explicit imports register feature-owned tables with the shared metadata.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=Settings().database_url.get_secret_value(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = build_engine(Settings())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
