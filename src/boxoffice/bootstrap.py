import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from boxoffice.modules.analytics.module import AnalyticsModule
from boxoffice.modules.audit.module import AuditModule
from boxoffice.modules.core.infrastructure.security import JwtTokenService, Pbkdf2PasswordHasher
from boxoffice.modules.core.module import CoreModule
from boxoffice.shared.db import make_engine
from boxoffice.shared.event_bus import InProcessEventBus

DEFAULT_SECRET = "dev-secret-key-change-me-in-production-32b"


def build_app(database_url: str | None = None, secret_key: str | None = None,
              analytics_lag_s: float | None = None) -> FastAPI:
    database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///./boxoffice.db")
    if analytics_lag_s is None:
        analytics_lag_s = float(os.getenv("ANALYTICS_LAG_MS", "0")) / 1000

    engine = make_engine(database_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    bus = InProcessEventBus()
    tokens = JwtTokenService(secret_key or os.getenv("SECRET_KEY", DEFAULT_SECRET))

    core = CoreModule(engine, session_factory, bus, Pbkdf2PasswordHasher(), tokens)
    analytics = AnalyticsModule(engine, session_factory, core.api, lag_s=analytics_lag_s)
    audit = AuditModule(engine, session_factory)
    analytics.subscribe(bus)
    audit.subscribe(bus)

    app = FastAPI(title="Box Office Analytics (Lab 5: Modular Monolith)")
    app.state.token_verifier = tokens
    app.state.bus = bus
    app.state.session_factory = session_factory
    for module in (core, analytics, audit):
        module.install(app)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError):
        errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=400, content={"detail": errors})

    return app
