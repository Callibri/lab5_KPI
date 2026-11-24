from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from boxoffice.modules.analytics.application.handlers import AnalyticsFacade, ProjectionHandler
from boxoffice.modules.analytics.contract import AnalyticsApi
from boxoffice.modules.analytics.infrastructure.acl.core_acl import (
    SUBSCRIBED_EVENTS, CoreEventTranslator, CoreGatewayAdapter,
)
from boxoffice.modules.analytics.infrastructure.orm import AnalyticsBase
from boxoffice.modules.analytics.infrastructure.read_repository import SqlAnalyticsReadRepository
from boxoffice.modules.analytics.infrastructure.store import store_factory
from boxoffice.modules.analytics.infrastructure.subscriber import CoreEventsSubscriber
from boxoffice.modules.analytics.presentation.api import router
from boxoffice.modules.core.contract import CoreApi
from boxoffice.shared.event_bus import InProcessEventBus


class AnalyticsModule:
    def __init__(self, engine: Engine, session_factory: sessionmaker, core_api: CoreApi, lag_s: float = 0.0):
        AnalyticsBase.metadata.create_all(engine)
        handler = ProjectionHandler(store_factory(session_factory), CoreGatewayAdapter(core_api))
        self._subscriber = CoreEventsSubscriber(CoreEventTranslator(), handler, lag_s)
        self.api: AnalyticsApi = AnalyticsFacade(SqlAnalyticsReadRepository(session_factory))

    def subscribe(self, bus: InProcessEventBus) -> None:
        for event_type in SUBSCRIBED_EVENTS:
            bus.subscribe(event_type, self._subscriber)

    def install(self, app: FastAPI) -> None:
        app.state.analytics_api = self.api
        app.include_router(router)
