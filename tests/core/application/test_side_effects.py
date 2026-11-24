import dataclasses
import inspect
import re
from datetime import date

import pytest

from boxoffice.modules.core.contract import events as ev
from boxoffice.modules.core.application.commands.movies import (
    CreateMovieCommand, CreateMovieHandler, DeleteMovieCommand, DeleteMovieHandler,
)
from boxoffice.modules.core.application.commands.reports import (
    AddReportCommand, AddReportHandler, DeleteReportCommand, DeleteReportHandler,
    UpdateReportCommand, UpdateReportHandler,
)
from boxoffice.modules.core.application.commands.users import RegisterUserCommand, RegisterUserHandler
from boxoffice.modules.core.application.side_effects import SideEffects
from boxoffice.modules.core.domain.factories import MovieFactory, ReportFactory, UserFactory
from tests.core.fakes import (
    FakeHasher, FakePublisher, InMemoryMovieRepository, InMemoryReportRepository,
    InMemoryUserRepository,
)

TODAY = date(2024, 6, 1)


def make(effects):
    movies, reports = InMemoryMovieRepository(), InMemoryReportRepository()
    return dict(
        movies=movies, reports=reports,
        create=CreateMovieHandler(MovieFactory(movies), movies, effects),
        delete=DeleteMovieHandler(movies, effects),
        add_report=AddReportHandler(movies, reports, ReportFactory(reports, lambda: TODAY), effects),
        update_report=UpdateReportHandler(reports, effects),
        delete_report=DeleteReportHandler(reports, effects),
    )


def seed_movie_and_report(h):
    h["create"].handle(CreateMovieCommand("Dune", "Sci-Fi", date(2024, 3, 1), 1000))
    return h["add_report"].handle(AddReportCommand(1, date(2024, 3, 5), "us", 500, 50))


def test_async_handler_only_publishes_event():
    bus = FakePublisher()
    h = make(SideEffects(publisher=bus))
    seed_movie_and_report(h)
    assert [type(e).__name__ for e in bus.events] == ["MovieCreated", "ReportAdded"]


def test_async_publish_failure_does_not_break_main_operation():
    h = make(SideEffects(publisher=FakePublisher(fail=True)))
    assert h["create"].handle(CreateMovieCommand("Dune", "Sci-Fi", date(2024, 3, 1), 1000)) == 1


def test_no_failure_when_no_side_effects_configured():
    h = make(SideEffects())
    assert seed_movie_and_report(h) == 1


def test_events_are_named_in_past_tense():
    names = [c.__name__ for _, c in inspect.getmembers(ev, inspect.isclass)
             if issubclass(c, ev.IntegrationEvent) and c is not ev.IntegrationEvent]
    assert len(names) == 7
    assert all(re.search(r"(Created|Updated|Deleted|Added|Corrected|Registered)$", n) for n in names)


def test_events_are_immutable():
    event = ev.MovieCreated(movie_id=1, title="Dune", genre="x", release_date=date(2024, 1, 1), budget_usd=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.title = "Other"


def test_events_have_unique_ids():
    kw = dict(movie_id=1, title="Dune", genre="x", release_date=date(2024, 1, 1), budget_usd=1)
    assert ev.MovieCreated(**kw).event_id != ev.MovieCreated(**kw).event_id


def test_events_carry_enough_context_without_extra_queries():
    bus = FakePublisher()
    h = make(SideEffects(publisher=bus))
    rid = seed_movie_and_report(h)
    h["update_report"].handle(UpdateReportCommand(rid, 700, 70))
    h["delete_report"].handle(DeleteReportCommand(rid))
    h["delete"].handle(DeleteMovieCommand(1))
    added, corrected, deleted_r, deleted_m = bus.events[1:]
    assert (added.region, added.revenue_usd, added.movie_id) == ("US", 500, 1)
    assert (corrected.previous_revenue_usd, corrected.revenue_usd) == (500, 700)
    assert deleted_r.revenue_usd == 700 and deleted_m.title == "Dune"


def test_register_user_emits_event():
    bus, users = FakePublisher(), InMemoryUserRepository()
    RegisterUserHandler(UserFactory(users, FakeHasher()), users, SideEffects(publisher=bus)).handle(
        RegisterUserCommand("A@b.com", "password1"))
    assert isinstance(bus.events[0], ev.UserRegistered) and bus.events[0].email == "a@b.com"
