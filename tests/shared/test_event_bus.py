import time
from datetime import date

from boxoffice.modules.core.contract import MovieCreated
from boxoffice.shared.event_bus import InProcessEventBus


def movie_event():
    return MovieCreated(movie_id=1, title="Dune", genre="x", release_date=date(2024, 1, 1), budget_usd=1)


def test_publish_returns_before_subscriber_finishes():
    bus, done = InProcessEventBus(), []
    bus.subscribe(MovieCreated, lambda e: (time.sleep(0.3), done.append(e)))
    started = time.perf_counter()
    bus.publish(movie_event())
    assert time.perf_counter() - started < 0.1 and done == []
    assert bus.wait_idle() and len(done) == 1
    bus.stop()


def test_failing_subscriber_is_retried_then_dead_lettered_and_others_still_run():
    bus, ok = InProcessEventBus(max_attempts=3, retry_delay_s=0), []
    calls = []

    def broken(e):
        calls.append(1)
        raise RuntimeError("boom")

    bus.subscribe(MovieCreated, broken)
    bus.subscribe(MovieCreated, ok.append)
    bus.publish(movie_event())
    bus.wait_idle()
    assert len(calls) == 3 and len(bus.dead_letters) == 1 and len(ok) == 1
    bus.stop()


def test_transient_failure_recovers_on_retry():
    bus, state = InProcessEventBus(max_attempts=3, retry_delay_s=0), {"n": 0}

    def flaky(e):
        state["n"] += 1
        if state["n"] < 3:
            raise RuntimeError("temporary")

    bus.subscribe(MovieCreated, flaky)
    bus.publish(movie_event())
    bus.wait_idle()
    assert state["n"] == 3 and bus.dead_letters == []
    bus.stop()


def test_subscribers_by_base_class_receive_all_events():
    from boxoffice.shared.events import IntegrationEvent
    bus, seen = InProcessEventBus(), []
    bus.subscribe(IntegrationEvent, seen.append)
    bus.publish(movie_event())
    bus.wait_idle()
    assert len(seen) == 1
    bus.stop()
