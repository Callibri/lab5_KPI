from datetime import date

import pytest

from boxoffice.modules.core.application.commands.movies import (
    CreateMovieCommand, CreateMovieHandler, DeleteMovieCommand, DeleteMovieHandler,
    UpdateMovieCommand, UpdateMovieHandler,
)
from boxoffice.modules.core.application.commands.reports import (
    AddReportCommand, AddReportHandler, DeleteReportCommand, DeleteReportHandler,
    UpdateReportCommand, UpdateReportHandler,
)
from boxoffice.modules.core.application.commands.users import RegisterUserCommand, RegisterUserHandler
from boxoffice.modules.core.domain.errors import ConflictError, DomainValidationError, NotFoundError
from boxoffice.modules.core.domain.factories import MovieFactory, ReportFactory, UserFactory
from tests.core.fakes import (
    FakeHasher, InMemoryMovieRepository, InMemoryReportRepository, InMemoryUserRepository,
)

TODAY = date(2024, 6, 1)


@pytest.fixture()
def env():
    movies, reports, users = InMemoryMovieRepository(), InMemoryReportRepository(), InMemoryUserRepository()
    return dict(
        movies=movies, reports=reports, users=users,
        movie_factory=MovieFactory(movies),
        report_factory=ReportFactory(reports, today=lambda: TODAY),
    )


def create_movie(env, title="Dune", release=date(2024, 3, 1), budget=1000) -> int:
    handler = CreateMovieHandler(env["movie_factory"], env["movies"])
    return handler.handle(CreateMovieCommand(title, "Sci-Fi", release, budget))


def add_report(env, movie_id=1, day=date(2024, 3, 5), region="US", revenue=1500, tickets=100) -> int:
    handler = AddReportHandler(env["movies"], env["reports"], env["report_factory"])
    return handler.handle(AddReportCommand(movie_id, day, region, revenue, tickets))


def test_register_returns_only_id_and_stores_hashed_password(env):
    handler = RegisterUserHandler(UserFactory(env["users"], FakeHasher()), env["users"])
    user_id = handler.handle(RegisterUserCommand("A@b.com", "password1"))
    assert user_id == 1
    assert env["users"].items[1].password_hash == "hashed:password1"


def test_register_duplicate_email_conflict(env):
    handler = RegisterUserHandler(UserFactory(env["users"], FakeHasher()), env["users"])
    handler.handle(RegisterUserCommand("a@b.com", "password1"))
    with pytest.raises(ConflictError):
        handler.handle(RegisterUserCommand("A@B.com", "password1"))


def test_create_movie_returns_id_and_persists(env):
    movie_id = create_movie(env)
    assert movie_id == 1 and env["movies"].get(1).title == "Dune"


def test_create_movie_invalid_budget_does_not_touch_repository(env):
    with pytest.raises(DomainValidationError):
        create_movie(env, budget=0)
    assert env["movies"].add_calls == 0


def test_create_duplicate_movie_conflict(env):
    create_movie(env)
    with pytest.raises(ConflictError):
        create_movie(env)
    assert env["movies"].add_calls == 1


def test_update_movie_changes_state_and_returns_nothing(env):
    create_movie(env)
    result = UpdateMovieHandler(env["movie_factory"], env["movies"]).handle(
        UpdateMovieCommand(1, "Dune 2", "Sci-Fi", date(2024, 3, 1), 2000))
    assert result is None
    assert env["movies"].get(1).budget.amount_usd == 2000


def test_update_movie_conflict_and_not_found(env):
    create_movie(env)
    create_movie(env, title="Barbie")
    handler = UpdateMovieHandler(env["movie_factory"], env["movies"])
    with pytest.raises(ConflictError):
        handler.handle(UpdateMovieCommand(2, "Dune", "Sci-Fi", date(2024, 3, 1), 10))
    with pytest.raises(NotFoundError):
        handler.handle(UpdateMovieCommand(99, "X", "Y", date(2024, 1, 1), 1))


def test_delete_movie(env):
    create_movie(env)
    DeleteMovieHandler(env["movies"]).handle(DeleteMovieCommand(1))
    assert env["movies"].get(1) is None
    with pytest.raises(NotFoundError):
        DeleteMovieHandler(env["movies"]).handle(DeleteMovieCommand(1))


def test_add_report_booked_slot_is_conflict(env):
    create_movie(env)
    assert add_report(env) == 1
    with pytest.raises(ConflictError):
        add_report(env)
    assert len(env["reports"].items) == 1
    add_report(env, region="UA")


def test_add_report_domain_errors(env):
    create_movie(env)
    with pytest.raises(DomainValidationError):
        add_report(env, day=date(2024, 2, 1))
    with pytest.raises(DomainValidationError):
        add_report(env, day=date(2024, 7, 1))
    with pytest.raises(DomainValidationError):
        add_report(env, revenue=-1)
    with pytest.raises(NotFoundError):
        add_report(env, movie_id=42)
    assert env["reports"].items == {}


def test_update_and_delete_report(env):
    create_movie(env)
    add_report(env)
    UpdateReportHandler(env["reports"]).handle(UpdateReportCommand(1, 1600, 110))
    assert env["reports"].get(1).revenue.amount_usd == 1600
    with pytest.raises(DomainValidationError):
        UpdateReportHandler(env["reports"]).handle(UpdateReportCommand(1, 5, -1))
    DeleteReportHandler(env["reports"]).handle(DeleteReportCommand(1))
    with pytest.raises(NotFoundError):
        DeleteReportHandler(env["reports"]).handle(DeleteReportCommand(1))
