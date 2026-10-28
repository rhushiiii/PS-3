from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.database import build_engine
from app.core.http import install_http_handling
from app.modules.auth.routes import demo_router
from app.modules.auth.routes import router as identity_router
from app.modules.auth.services import DemoTokenVerifier
from app.modules.health import router
from app.modules.institutions.routes import router as institution_router
from app.modules.submissions.routes import router as submission_router
from app.modules.validation.routes import router as validation_router


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
    install_http_handling(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )
    application.include_router(router)
    application.include_router(identity_router)
    application.include_router(institution_router)
    application.include_router(submission_router)
    application.include_router(validation_router)
    if config.demo_auth:
        application.include_router(demo_router)
    return application
