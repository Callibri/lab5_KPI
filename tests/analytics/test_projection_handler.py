from contextlib import contextmanager

import pytest

from boxoffice.modules.analytics.application.commands import (
    ApplyRevenueDelta, ForgetMovie, UpsertMovieProfile,
)
from boxoffice.modules.analytics.application.handlers import ProjectionHandler
from boxoffice.modules.analytics.application.ports import AnalyticsStore, CoreGateway, MovieProfile
from boxoffice.modules.analytics.domain.model import ProjectionInconsistencyError


class FakeStore(AnalyticsStore):
    def __init__(self):
        self.stats, self.processed, self.commits = {}, set(), 0

    def is_processed(self, event_id): return event_id in self.processed
    def mark_processed(self, event_id): self.processed.add(event_id)
    def get_stats(self, movie_id):
        s = self.stats.get(movie_id)
        return None if s is None else __import__("copy").deepcopy(s)
    def save_stats(self, stats): self.stats[stats.movie_id] = stats
    def delete_stats(self, movie_id): self.stats.pop(movie_id, None)
    def commit(self): self.commits += 1


class FakeGateway(CoreGateway):
    def __init__(self, profile=None):
        self.profile, self.calls = profile, 0

    def get_movie_profile(self, movie_id):
        self.calls += 1
        return self.profile


@pytest.fixture()
def env():
    store, gateway = FakeStore(), FakeGateway()

    @contextmanager
    def factory():
        yield store
    return store, gateway, ProjectionHandler(factory, gateway)


def test_profile_then_deltas_build_projection(env):
    store, _, h = env
    h.handle(UpsertMovieProfile("e1", 1, "Dune", 1000))
    h.handle(ApplyRevenueDelta("e2", 1, "US", 1500, 100))
    h.handle(ApplyRevenueDelta("e3", 1, "UA", 500, 50))
    s = store.stats[1]
    assert (s.title, s.total_revenue_usd, s.roi) == ("Dune", 2000, 1.0)


def test_duplicate_delivery_is_ignored(env):
    store, _, h = env
    h.handle(UpsertMovieProfile("e1", 1, "Dune", 1000))
    assert h.handle(ApplyRevenueDelta("e2", 1, "US", 500, 50)) is True
    assert h.handle(ApplyRevenueDelta("e2", 1, "US", 500, 50)) is False
    assert store.stats[1].total_revenue_usd == 500


def test_out_of_order_event_falls_back_to_core_via_gateway(env):
    store, gateway, h = env
    gateway.profile = MovieProfile("Dune", 1000)
    h.handle(ApplyRevenueDelta("e1", 1, "US", 500, 50))
    assert gateway.calls == 1 and store.stats[1].title == "Dune"


def test_out_of_order_event_without_core_data_keeps_placeholder(env):
    store, _, h = env
    h.handle(ApplyRevenueDelta("e1", 1, "US", 500, 50))
    assert store.stats[1].title is None and store.stats[1].roi is None


def test_forget_movie_removes_projection(env):
    store, _, h = env
    h.handle(UpsertMovieProfile("e1", 1, "Dune", 1000))
    h.handle(ForgetMovie("e2", 1))
    assert 1 not in store.stats


def test_inconsistent_delta_is_not_committed_or_marked_processed(env):
    store, _, h = env
    with pytest.raises(ProjectionInconsistencyError):
        h.handle(ApplyRevenueDelta("e1", 1, "US", -5, 0))
    assert "e1" not in store.processed and store.commits == 0
