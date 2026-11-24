from typing import Iterator

from fastapi import Request

from boxoffice.modules.core.application.registry import Handlers
from boxoffice.shared.web import require_user


def get_handlers(request: Request) -> Iterator[Handlers]:
    yield from request.app.state.core_handlers_scope()
