from datetime import date

import pytest

from boxoffice.modules.analytics.application.commands import (
    ApplyRevenueDelta, ForgetMovie, UpsertMovieProfile,
)
from boxoffice.modules.analytics.domain.model import MovieStats, ProjectionInconsistencyError
from boxoffice.modules.analytics.infrastructure.acl.core_acl import CoreEventTranslator
from boxoffice.modules.core.contract import (
    MovieCreated, MovieDeleted, MovieUpdated, ReportAdded, ReportCorrected, ReportDeleted,
    UserRegistered,
)


def test_stats_aggregation_and_derived_metrics():
    s = MovieStats(1)
    s.set_profile("Dune", 1000)
    s.apply_delta("US", 1500, 100)
    s.apply_delta("UA", 500, 50)
    assert (s.total_revenue_usd, s.total_tickets) == (2000, 150)
    assert s.avg_ticket_price_usd == 13.33 and s.roi == 1.0


def test_stats_without_profile_has_no_roi():
    s = MovieStats(1)
    s.apply_delta("US", 10, 1)
    assert s.roi is None and s.title is None


def test_negative_totals_are_rejected():
    s = MovieStats(1)
    s.apply_delta("US", 10, 1)
    with pytest.raises(ProjectionInconsistencyError):
        s.apply_delta("US", -20, 0)


def test_acl_translates_movie_events_into_profile_commands():
    t = CoreEventTranslator()
    created = MovieCreated(movie_id=1, title="Dune", genre="Sci-Fi", release_date=date(2024, 1, 1), budget_usd=1000)
    updated = MovieUpdated(movie_id=1, title="Dune 2", genre="Sci-Fi", release_date=date(2024, 1, 1), budget_usd=2000)
    assert t.translate(created) == [UpsertMovieProfile(created.event_id, 1, "Dune", 1000)]
    assert t.translate(updated) == [UpsertMovieProfile(updated.event_id, 1, "Dune 2", 2000)]
    deleted = MovieDeleted(movie_id=1, title="Dune")
    assert t.translate(deleted) == [ForgetMovie(deleted.event_id, 1)]


def test_acl_turns_report_events_into_revenue_deltas():
    t = CoreEventTranslator()
    base = dict(report_id=7, movie_id=1, report_date=date(2024, 3, 5), region="US")
    added = ReportAdded(**base, revenue_usd=500, tickets_sold=50)
    corrected = ReportCorrected(**base, revenue_usd=700, tickets_sold=60, previous_revenue_usd=500, previous_tickets_sold=50)
    deleted = ReportDeleted(**base, revenue_usd=700, tickets_sold=60)
    assert t.translate(added) == [ApplyRevenueDelta(added.event_id, 1, "US", 500, 50)]
    assert t.translate(corrected) == [ApplyRevenueDelta(corrected.event_id, 1, "US", 200, 10)]
    assert t.translate(deleted) == [ApplyRevenueDelta(deleted.event_id, 1, "US", -700, -60)]


def test_acl_ignores_events_it_does_not_care_about():
    assert CoreEventTranslator().translate(UserRegistered(user_id=1, email="a@b.com")) == []
