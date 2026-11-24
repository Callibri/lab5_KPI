import logging
import queue
import threading
import time
from collections import defaultdict
from typing import Callable

from boxoffice.shared.events import IntegrationEvent
from boxoffice.shared.events import EventPublisher

log = logging.getLogger(__name__)
_STOP = object()


class InProcessEventBus(EventPublisher):
    def __init__(self, max_attempts: int = 3, retry_delay_s: float = 0.05):
        self._subs: dict[type, list[Callable]] = defaultdict(list)
        self._queue: queue.Queue = queue.Queue()
        self._max_attempts, self._retry_delay = max_attempts, retry_delay_s
        self.dead_letters: list[tuple[IntegrationEvent, Callable, Exception]] = []
        self._thread = threading.Thread(target=self._run, name="event-bus", daemon=True)
        self._thread.start()

    def subscribe(self, event_type: type, handler: Callable[[IntegrationEvent], None]) -> None:
        self._subs[event_type].append(handler)

    def publish(self, event: IntegrationEvent) -> None:
        self._queue.put(event)

    def wait_idle(self, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while self._queue.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.005)
        return not self._queue.unfinished_tasks

    def stop(self) -> None:
        self._queue.put(_STOP)
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while True:
            event = self._queue.get()
            try:
                if event is _STOP:
                    return
                self._dispatch(event)
            finally:
                self._queue.task_done()

    def _dispatch(self, event: IntegrationEvent) -> None:
        for cls in type(event).__mro__:
            for handler in list(self._subs.get(cls, [])):
                self._deliver(event, handler)

    def _deliver(self, event, handler) -> None:
        for attempt in range(1, self._max_attempts + 1):
            try:
                handler(event)
                return
            except Exception as exc:
                log.warning("Handler failed (attempt %d/%d) for %s: %s",
                            attempt, self._max_attempts, type(event).__name__, exc)
                if attempt == self._max_attempts:
                    self.dead_letters.append((event, handler, exc))
                else:
                    time.sleep(self._retry_delay)
