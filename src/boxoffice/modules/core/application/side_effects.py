import logging

from boxoffice.shared.events import EventPublisher, IntegrationEvent

log = logging.getLogger(__name__)


class SideEffects:

    def __init__(self, publisher: EventPublisher | None = None):
        self._publisher = publisher

    def emit(self, event: IntegrationEvent) -> None:
        if self._publisher is None:
            return
        try:
            self._publisher.publish(event)
        except Exception:
            log.exception("Publishing failed for %s", type(event).__name__)
