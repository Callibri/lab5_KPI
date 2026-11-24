from typing import Callable, Iterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from boxoffice.modules.core.application.registry import Handlers
from boxoffice.modules.core.domain.errors import (
    AuthenticationError, ConflictError, DomainError, DomainValidationError, NotFoundError,
)
from boxoffice.modules.core.presentation.routers import auth_router, movies_router, reports_router

ERROR_STATUS = {
    DomainValidationError: 400,
    AuthenticationError: 401,
    NotFoundError: 404,
    ConflictError: 409,
}


def install(app: FastAPI, handlers_scope: Callable[[], Iterator[Handlers]]) -> None:
    app.state.core_handlers_scope = handlers_scope
    for router in (auth_router, movies_router, reports_router):
        app.include_router(router)

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError):
        status = next((code for cls, code in ERROR_STATUS.items() if isinstance(exc, cls)), 500)
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        return JSONResponse(status_code=status, content={"detail": str(exc)}, headers=headers)
