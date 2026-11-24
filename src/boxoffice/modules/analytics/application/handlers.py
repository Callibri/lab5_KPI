from typing import Callable, ContextManager

from boxoffice.modules.analytics.application.commands import (
    ApplyRevenueDelta, ForgetMovie, UpsertMovieProfile,
)
from boxoffice.modules.analytics.application.ports import (
    AnalyticsReadRepository, AnalyticsStore, CoreGateway,
)
from boxoffice.modules.analytics.contract import (
    AnalyticsApi, MovieSummaryDto, RegionRevenueDto, TopMovieDto,
)
from boxoffice.modules.analytics.domain.model import MovieStats

AnalyticsCommand = UpsertMovieProfile | ForgetMovie | ApplyRevenueDelta


class ProjectionHandler:

    def __init__(self, store_factory: Callable[[], ContextManager[AnalyticsStore]], gateway: CoreGateway):
        self._store_factory, self._gateway = store_factory, gateway

    def handle(self, cmd: AnalyticsCommand) -> bool:
        with self._store_factory() as store:
            if store.is_processed(cmd.event_id):
                return False
            if isinstance(cmd, UpsertMovieProfile):
                stats = store.get_stats(cmd.movie_id) or MovieStats(cmd.movie_id)
                stats.set_profile(cmd.title, cmd.budget_usd)
                store.save_stats(stats)
            elif isinstance(cmd, ForgetMovie):
                store.delete_stats(cmd.movie_id)
            elif isinstance(cmd, ApplyRevenueDelta):
                stats = store.get_stats(cmd.movie_id)
                if stats is None:
                    stats = MovieStats(cmd.movie_id)
                    profile = self._gateway.get_movie_profile(cmd.movie_id)
                    if profile is not None:
                        stats.set_profile(profile.title, profile.budget_usd)
                stats.apply_delta(cmd.region, cmd.revenue_delta, cmd.tickets_delta)
                store.save_stats(stats)
            store.mark_processed(cmd.event_id)
            store.commit()
            return True


class AnalyticsFacade(AnalyticsApi):
    def __init__(self, reads: AnalyticsReadRepository):
        self._reads = reads

    def movie_summary(self, movie_id: int) -> MovieSummaryDto | None:
        return self._reads.movie_summary(movie_id)

    def top_movies(self, limit: int) -> list[TopMovieDto]:
        return self._reads.top_movies(limit)

    def revenue_by_region(self) -> list[RegionRevenueDto]:
        return self._reads.revenue_by_region()
