from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from boxoffice.modules.audit.application.handlers import AuditFacade, AuditRecorder
from boxoffice.modules.audit.contract import AuditApi
from boxoffice.modules.audit.infrastructure.acl.core_acl import (
    SUBSCRIBED_EVENTS, CoreEventsSubscriber, CoreEventTranslator,
)
from boxoffice.modules.audit.infrastructure.sql import AuditBase, SqlAuditRepository
from boxoffice.modules.audit.presentation.api import router
from boxoffice.shared.event_bus import InProcessEventBus


class AuditModule:
    def __init__(self, engine: Engine, session_factory: sessionmaker):
        AuditBase.metadata.create_all(engine)
        repo = SqlAuditRepository(session_factory)
        self._subscriber = CoreEventsSubscriber(CoreEventTranslator(), AuditRecorder(repo))
        self.api: AuditApi = AuditFacade(repo)

    def subscribe(self, bus: InProcessEventBus) -> None:
        for event_type in SUBSCRIBED_EVENTS:
            bus.subscribe(event_type, self._subscriber)

    def install(self, app: FastAPI) -> None:
        app.state.audit_api = self.api
        app.include_router(router)
