from datetime import date

import pytest

from boxoffice.modules.core.domain.errors import ConflictError, DomainValidationError
from boxoffice.modules.core.domain.factories import MovieFactory, ReportFactory, UserFactory
from tests.core.fakes import (
    FakeHasher, InMemoryMovieRepository, InMemoryReportRepository, InMemoryUserRepository,
)

TODAY = date(2024, 6, 1)


def test_user_factory_hashes_password_and_checks_unique_email():
    users = InMemoryUserRepository()
    factory = UserFactory(users, FakeHasher())
    user = factory.create("A@b.com", "password1")
    assert user.email.value == "a@b.com" and user.password_hash == "hashed:password1"
    users.add(user)
    with pytest.raises(ConflictError):
        factory.create("a@b.com", "password1")


def test_user_factory_rejects_bad_input():
    factory = UserFactory(InMemoryUserRepository(), FakeHasher())
    with pytest.raises(DomainValidationError):
        factory.create("bad", "password1")
    with pytest.raises(DomainValidationError):
        factory.create("a@b.com", "short")


def test_movie_factory_unique_title_and_date():
    movies = InMemoryMovieRepository()
    factory = MovieFactory(movies)
    movies.add(factory.create("Dune", "Sci-Fi", date(2024, 3, 1), 1000))
    with pytest.raises(ConflictError):
        factory.create("Dune", "Sci-Fi", date(2024, 3, 1), 500)
    factory.create("Dune", "Sci-Fi", date(2025, 3, 1), 500)


def test_movie_factory_validates_budget():
    with pytest.raises(DomainValidationError):
        MovieFactory(InMemoryMovieRepository()).create("Dune", "Sci-Fi", date(2024, 3, 1), 0)


def _movie_and_factory():
    movies = InMemoryMovieRepository()
    movie = movies.add(MovieFactory(movies).create("Dune", "Sci-Fi", date(2024, 3, 1), 1000))
    reports = InMemoryReportRepository()
    return movie, reports, ReportFactory(reports, today=lambda: TODAY)


def test_report_factory_creates_valid_report():
    movie, _, factory = _movie_and_factory()
    report = factory.create(movie, date(2024, 3, 5), "us", 500, 50)
    assert report.region.value == "US" and report.revenue.amount_usd == 500


def test_report_factory_rejects_future_and_pre_release_dates():
    movie, _, factory = _movie_and_factory()
    with pytest.raises(DomainValidationError):
        factory.create(movie, date(2024, 7, 1), "US", 1, 1)
    with pytest.raises(DomainValidationError):
        factory.create(movie, date(2024, 2, 1), "US", 1, 1)


def test_report_factory_conflict_on_duplicate_slot():
    movie, reports, factory = _movie_and_factory()
    reports.add(factory.create(movie, date(2024, 3, 5), "US", 1, 1))
    with pytest.raises(ConflictError):
        factory.create(movie, date(2024, 3, 5), "US", 2, 2)
    factory.create(movie, date(2024, 3, 5), "UA", 2, 2)
