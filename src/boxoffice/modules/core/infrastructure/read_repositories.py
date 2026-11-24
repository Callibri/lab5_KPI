from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from boxoffice.modules.core.application.queries.ports import (
    CredentialsReadRepository, MovieReadRepository, ReportReadRepository,
)
from boxoffice.modules.core.application.queries.read_models import (
    MovieDetails, MovieListItem, ReportItem, UserCredentials,
)
from boxoffice.modules.core.infrastructure.orm_models import MovieRow, ReportRow, UserRow


def _avg_price(revenue: int, tickets: int) -> float | None:
    return round(revenue / tickets, 2) if tickets else None


class SqlMovieReadRepository(MovieReadRepository):
    def __init__(self, session: Session):
        self._s = session

    def list_movies(self, genre, year, limit, offset) -> list[MovieListItem]:
        totals = (
            select(ReportRow.movie_id, func.sum(ReportRow.revenue_usd).label("revenue"))
            .group_by(ReportRow.movie_id)
            .subquery()
        )
        query = (
            select(MovieRow, func.coalesce(totals.c.revenue, 0))
            .outerjoin(totals, totals.c.movie_id == MovieRow.id)
            .order_by(MovieRow.id)
        )
        if genre:
            query = query.where(MovieRow.genre == genre)
        if year:
            query = query.where(extract("year", MovieRow.release_date) == year)
        rows = self._s.execute(query.limit(limit).offset(offset)).all()
        return [
            MovieListItem(m.id, m.title, m.genre, m.release_date, m.budget_usd, revenue)
            for m, revenue in rows
        ]

    def get_details(self, movie_id: int) -> MovieDetails | None:
        m = self._s.get(MovieRow, movie_id)
        if m is None:
            return None
        revenue, tickets, count = self._s.execute(
            select(
                func.coalesce(func.sum(ReportRow.revenue_usd), 0),
                func.coalesce(func.sum(ReportRow.tickets_sold), 0),
                func.count(ReportRow.id),
            ).where(ReportRow.movie_id == movie_id)
        ).one()
        return MovieDetails(m.id, m.title, m.genre, m.release_date, m.budget_usd, revenue, tickets, count)


class SqlReportReadRepository(ReportReadRepository):
    def __init__(self, session: Session):
        self._s = session

    def list_for_movie(self, movie_id, date_from: date | None, date_to: date | None, region: str | None):
        if self._s.get(MovieRow, movie_id) is None:
            return None
        query = select(ReportRow).where(ReportRow.movie_id == movie_id)
        if date_from:
            query = query.where(ReportRow.report_date >= date_from)
        if date_to:
            query = query.where(ReportRow.report_date <= date_to)
        if region:
            query = query.where(ReportRow.region == region.strip().upper())
        rows = self._s.scalars(query.order_by(ReportRow.report_date, ReportRow.region)).all()
        return [
            ReportItem(r.id, r.movie_id, r.report_date, r.region, r.revenue_usd, r.tickets_sold,
                       _avg_price(r.revenue_usd, r.tickets_sold))
            for r in rows
        ]


class SqlCredentialsReadRepository(CredentialsReadRepository):
    def __init__(self, session: Session):
        self._s = session

    def get_credentials(self, email: str) -> UserCredentials | None:
        row = self._s.execute(
            select(UserRow.id, UserRow.password_hash).where(UserRow.email == email)
        ).first()
        return UserCredentials(row[0], row[1]) if row else None
