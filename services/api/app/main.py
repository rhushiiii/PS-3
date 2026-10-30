from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.database import build_engine
from app.core.http import install_http_handling
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import (
    BodyLimitMiddleware,
    SecurityHeadersMiddleware,
    install_log_redaction,
)
from app.modules.analytics.routes import router as analytics_router
from app.modules.audit.routes import router as audit_router
from app.modules.auth.routes import demo_router
from app.modules.auth.routes import router as identity_router
from app.modules.auth.services import DemoTokenVerifier
from app.modules.cases.routes import router as cases_router
from app.modules.credentials.routes import router as credentials_router
from app.modules.health import router
from app.modules.institutions.routes import router as institution_router
from app.modules.intake.routes import router as intake_router
from app.modules.integrity.routes import router as integrity_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.records.routes import router as records_router
from app.modules.reports.routes import router as reports_router
from app.modules.submissions.routes import router as submission_router
from app.modules.validation.routes import router as validation_router
from app.modules.verification.routes import router as verification_router


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(config)
        app.state.engine = engine
        app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title="SIH26263 Prototype API", version="0.1.0", lifespan=lifespan
    )
    application.state.settings = config
    application.state.token_verifier = (
        DemoTokenVerifier(config) if config.demo_auth else None
    )
    application.state.rate_limiter = SlidingWindowLimiter()
    install_log_redaction()
    # add_middleware stacks outward: the body cap must stay innermost (it raises
    # through the shared error handler); security headers outermost (all responses).
    application.add_middleware(
        BodyLimitMiddleware,
        max_bytes=config.request_max_bytes,
        exempt={("POST", "/api/v1/submissions")},  # upload keeps UPLOAD_MAX_BYTES
    )
    install_http_handling(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Accept", "Authorization", "Content-Type", "Idempotency-Key"],
        expose_headers=["Idempotent-Replayed", "Retry-After", "Content-Disposition"],
    )
    application.add_middleware(SecurityHeadersMiddleware)
    application.include_router(router)
    application.include_router(identity_router)
    application.include_router(institution_router)
    application.include_router(intake_router)
    application.include_router(submission_router)
    application.include_router(validation_router)
    application.include_router(verification_router)
    application.include_router(cases_router)
    application.include_router(notifications_router)
    application.include_router(records_router)
    application.include_router(integrity_router)
    application.include_router(credentials_router)
    application.include_router(analytics_router)
    application.include_router(reports_router)
    application.include_router(audit_router)
    if config.demo_auth:
        application.include_router(demo_router)
    return application
