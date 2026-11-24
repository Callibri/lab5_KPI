from datetime import date

import pytest

from boxoffice.modules.core.infrastructure.orm_models import MovieRow, ReportRow


@pytest.fixture()
def seeded(app):
    with app.state.session_factory() as s:
        dune = MovieRow(title="Dune", genre="Sci-Fi", release_date=date(2024, 3, 1), budget_usd=1000)
        barbie = MovieRow(title="Barbie", genre="Comedy", release_date=date(2023, 7, 21), budget_usd=200)
        empty = MovieRow(title="Upcoming", genre="Drama", release_date=date(2024, 1, 1), budget_usd=500)
        s.add_all([dune, barbie, empty])
        s.flush()
        s.add_all([
            ReportRow(movie_id=dune.id, report_date=date(2024, 3, 5), region="US", revenue_usd=1500, tickets_sold=100),
            ReportRow(movie_id=dune.id, report_date=date(2024, 3, 5), region="UA", revenue_usd=500, tickets_sold=50),
            ReportRow(movie_id=dune.id, report_date=date(2024, 3, 6), region="US", revenue_usd=1000, tickets_sold=70),
            ReportRow(movie_id=barbie.id, report_date=date(2023, 7, 22), region="US", revenue_usd=300, tickets_sold=30),
        ])
        s.commit()
        return {"dune": dune.id, "barbie": barbie.id, "empty": empty.id}
