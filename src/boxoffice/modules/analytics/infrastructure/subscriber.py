import time

from boxoffice.modules.analytics.application.handlers import ProjectionHandler
from boxoffice.modules.analytics.infrastructure.acl.core_acl import CoreEventTranslator
from boxoffice.shared.events import IntegrationEvent


class CoreEventsSubscriber:

    def __init__(self, translator: CoreEventTranslator, handler: ProjectionHandler, lag_s: float = 0.0):
        self._translator, self._handler, self._lag = translator, handler, lag_s

    def __call__(self, event: IntegrationEvent) -> None:
        if self._lag:
            time.sleep(self._lag)
        for command in self._translator.translate(event):
            self._handler.handle(command)
