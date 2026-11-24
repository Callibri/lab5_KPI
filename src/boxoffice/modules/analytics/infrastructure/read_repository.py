from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from boxoffice.modules.analytics.application.ports import AnalyticsReadRepository
from boxoffice.modules.analytics.contract import MovieSummaryDto, RegionRevenueDto, TopMovieDto
from boxoffice.modules.analytics.infrastructure.orm import MovieRegionRow, MovieStatsRow


def _roi(revenue: int, budget: int | None) -> float | None:
    return round((revenue - budget) / budget, 4) if budget else None


class SqlAnalyticsReadRepository(AnalyticsReadRepository):

    def __init__(self, session_factory: sessionmaker):
        self._sf = session_factory

    def movie_summary(self, movie_id: int) -> MovieSummaryDto | None:
        with self._sf() as s:
            m = s.get(MovieStatsRow, movie_id)
            if m is None:
                return None
            regions = s.execute(
                select(MovieRegionRow.region, MovieRegionRow.revenue_usd)
                .where(MovieRegionRow.movie_id == movie_id)
                .order_by(MovieRegionRow.revenue_usd.desc(), MovieRegionRow.region)).all()
            avg = round(m.total_revenue_usd / m.total_tickets, 2) if m.total_tickets else None
            return MovieSummaryDto(
                m.movie_id, m.title, m.budget_usd, m.total_revenue_usd, m.total_tickets, avg,
                _roi(m.total_revenue_usd, m.budget_usd),
                [RegionRevenueDto(r, rev) for r, rev in regions])

    def top_movies(self, limit: int) -> list[TopMovieDto]:
        with self._sf() as s:
            rows = s.scalars(
                select(MovieStatsRow)
                .where((MovieStatsRow.total_revenue_usd > 0) | (MovieStatsRow.total_tickets > 0))
                .order_by(MovieStatsRow.total_revenue_usd.desc(), MovieStatsRow.movie_id)
                .limit(limit)).all()
            return [TopMovieDto(m.movie_id, m.title, m.total_revenue_usd, m.total_tickets,
                                _roi(m.total_revenue_usd, m.budget_usd)) for m in rows]

    def revenue_by_region(self) -> list[RegionRevenueDto]:
        with self._sf() as s:
            total = func.sum(MovieRegionRow.revenue_usd)
            rows = s.execute(select(MovieRegionRow.region, total).group_by(MovieRegionRow.region)
                             .order_by(total.desc(), MovieRegionRow.region)).all()
            return [RegionRevenueDto(r, rev) for r, rev in rows if rev > 0]
