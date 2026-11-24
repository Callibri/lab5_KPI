from datetime import date

import pytest

from boxoffice.modules.core.domain.entities import BoxOfficeReport, Movie
from boxoffice.modules.core.domain.errors import DomainValidationError
from boxoffice.modules.core.domain.value_objects import Money, RegionCode


def make_movie(**kw):
    data = dict(title="Dune", genre="Sci-Fi", release_date=date(2024, 3, 1), budget=Money(1000))
    return Movie(**{**data, **kw})


@pytest.mark.parametrize("kw", [{"title": " "}, {"genre": ""}, {"budget": Money(0)}])
def test_movie_invariants(kw):
    with pytest.raises(DomainValidationError):
        make_movie(**kw)


def test_movie_update_is_atomic():
    movie = make_movie()
    with pytest.raises(DomainValidationError):
        movie.update(title="New", genre="Drama", release_date=date(2025, 1, 1), budget=Money(0))
    assert movie.title == "Dune"


def test_movie_report_date_rules():
    movie = make_movie()
    today = date(2024, 6, 1)
    movie.ensure_accepts_report_for(date(2024, 3, 5), today)
    with pytest.raises(DomainValidationError):
        movie.ensure_accepts_report_for(date(2024, 2, 1), today)
    with pytest.raises(DomainValidationError):
        movie.ensure_accepts_report_for(date(2024, 7, 1), today)


def test_report_correct_validates():
    report = BoxOfficeReport(1, date(2024, 3, 5), RegionCode("US"), Money(10), 1)
    report.correct(revenue=Money(20), tickets_sold=2)
    assert (report.revenue, report.tickets_sold) == (Money(20), 2)
    with pytest.raises(DomainValidationError):
        report.correct(revenue=Money(5), tickets_sold=-1)
    assert report.tickets_sold == 2
