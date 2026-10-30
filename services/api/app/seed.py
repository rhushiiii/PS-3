"""Run explicitly with python -m app.seed; never run automatically at startup."""

import json
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import Base, build_engine
from app.modules.audit.models import AuditEvent
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.institutions.models import (
    AdmissionCategory,
    Institution,
    IntakeRule,
    Programme,
)


class SeedConflict(ValueError):
    """Existing data conflicts with an expected synthetic fixture."""


def seed_id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"sih26263/synthetic/{kind}/{key}")


def ensure_fixture[Model: Base](
    session: Session,
    model: type[Model],
    key: str,
    values: dict[str, object],
    institution_id: UUID | None,
) -> bool:
    identifier = seed_id(model.__tablename__, key)
    existing = session.get(model, identifier)
    created = existing is None
    if existing is not None:
        if any(getattr(existing, name) != value for name, value in values.items()):
            raise SeedConflict(
                "Existing synthetic data differs; no changes were committed"
            )
    else:
        session.add(model(id=identifier, **values))
        session.flush()
    event_id = seed_id("seed_audit", str(identifier))
    if session.get(AuditEvent, event_id) is None:
        record_action(
            session,
            actor_id=None,
            institution_id=institution_id,
            action="DEMO_SEED",
            entity_type=model.__tablename__,
            entity_id=identifier,
            event_id=event_id,
        )
        session.flush()
    return created


def seed_demo(session: Session, settings: Settings) -> dict[str, int]:
    if settings.app_env != "local" or not settings.demo_auth:
        raise ValueError("Seeding requires explicitly enabled local demo mode")
    created = 0
    for index, slug in enumerate(("cedar", "maple", "willow"), start=1):
        institution_id = seed_id("institutions", slug)
        created += ensure_fixture(
            session,
            Institution,
            slug,
            {
                "permanent_id": f"DEMO-INST-{index:03d}",
                "name": f"Demo {slug.title()} Institute",
                "region": f"DEMO_REGION_{index}",
                "active": True,
            },
            institution_id,
        )
        for code, name in (
            ("DEMO-COMP", "Demo Computing"),
            ("DEMO-ELEC", "Demo Electronics"),
        ):
            programme_key = f"{slug}/{code}"
            programme_id = seed_id("programmes", programme_key)
            created += ensure_fixture(
                session,
                Programme,
                programme_key,
                {
                    "institution_id": institution_id,
                    "code": code,
                    "name": name,
                    "active": True,
                },
                institution_id,
            )
            for category in AdmissionCategory:
                created += ensure_fixture(
                    session,
                    IntakeRule,
                    f"{programme_key}/2026-27/{category}/DEMO-v1",
                    {
                        "institution_id": institution_id,
                        "programme_id": programme_id,
                        "academic_year": "2026-27",
                        "category": category,
                        "approved_seats": 3
                        if category == AdmissionCategory.REGULAR
                        else 1,
                        "rule_version": "DEMO-v1",
                        "source_label": "DEMO",
                    },
                    institution_id,
                )
        alias = f"{slug}_admin"
        created += ensure_fixture(
            session,
            User,
            alias,
            {
                "email": f"{alias}@sih26263.invalid",
                "password_hash": None,
                "role": Role.INSTITUTION_ADMIN,
                "institution_id": institution_id,
                "active": True,
                "demo_alias": alias,
                "is_demo": True,
            },
            institution_id,
        )
    for alias, role in (
        ("demo_officer", Role.AICTE_OFFICER),
        ("demo_manager", Role.AICTE_MANAGER),
        ("demo_officer_2", Role.AICTE_OFFICER),
        ("demo_verifier", Role.AUTHORIZED_VERIFIER),
    ):
        created += ensure_fixture(
            session,
            User,
            alias,
            {
                "email": f"{alias}@sih26263.invalid",
                "password_hash": None,
                "role": role,
                "institution_id": None,
                "active": True,
                "demo_alias": alias,
                "is_demo": True,
            },
            None,
        )
    return {"created": created, "expected_fixture_records": 46}


def main() -> int:
    try:
        settings = Settings()
        # Refuse before opening a connection if the local demo opt-in is absent.
        if settings.app_env != "local" or not settings.demo_auth:
            raise ValueError("Local demo mode is required")
        engine = build_engine(settings)
        try:
            with Session(engine) as session, session.begin():
                result = seed_demo(session, settings)
        finally:
            engine.dispose()
    except (ValueError, SQLAlchemyError):
        print(
            "Demo seed failed: check local demo settings, migrations "
            "and fixture conflicts."
        )
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
