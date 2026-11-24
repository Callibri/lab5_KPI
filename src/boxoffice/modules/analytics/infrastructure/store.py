from contextlib import contextmanager

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from boxoffice.modules.analytics.application.ports import AnalyticsStore
from boxoffice.modules.analytics.domain.model import MovieStats
from boxoffice.modules.analytics.infrastructure.orm import MovieRegionRow, MovieStatsRow, ProcessedEventRow


class SqlAnalyticsStore(AnalyticsStore):
    def __init__(self, session: Session):
        self._s = session

    def is_processed(self, event_id: str) -> bool:
        return self._s.get(ProcessedEventRow, event_id) is not None

    def mark_processed(self, event_id: str) -> None:
        self._s.add(ProcessedEventRow(event_id=event_id))

    def get_stats(self, movie_id: int) -> MovieStats | None:
        row = self._s.get(MovieStatsRow, movie_id)
        if row is None:
            return None
        regions = self._s.scalars(select(MovieRegionRow).where(MovieRegionRow.movie_id == movie_id)).all()
        return MovieStats(
            movie_id=row.movie_id, title=row.title, budget_usd=row.budget_usd,
            total_revenue_usd=row.total_revenue_usd, total_tickets=row.total_tickets,
            revenue_by_region={r.region: r.revenue_usd for r in regions},
            tickets_by_region={r.region: r.tickets for r in regions})

    def save_stats(self, stats: MovieStats) -> None:
        row = self._s.get(MovieStatsRow, stats.movie_id) or MovieStatsRow(movie_id=stats.movie_id)
        row.title, row.budget_usd = stats.title, stats.budget_usd
        row.total_revenue_usd, row.total_tickets = stats.total_revenue_usd, stats.total_tickets
        self._s.add(row)
        self._s.execute(delete(MovieRegionRow).where(MovieRegionRow.movie_id == stats.movie_id))
        self._s.flush()
        for region, revenue in stats.revenue_by_region.items():
            self._s.add(MovieRegionRow(movie_id=stats.movie_id, region=region, revenue_usd=revenue,
                                       tickets=stats.tickets_by_region.get(region, 0)))

    def delete_stats(self, movie_id: int) -> None:
        self._s.execute(delete(MovieRegionRow).where(MovieRegionRow.movie_id == movie_id))
        self._s.execute(delete(MovieStatsRow).where(MovieStatsRow.movie_id == movie_id))

    def commit(self) -> None:
        self._s.commit()


def store_factory(session_factory: sessionmaker):
    @contextmanager
    def factory():
        with session_factory() as session:
            yield SqlAnalyticsStore(session)
    return factory
