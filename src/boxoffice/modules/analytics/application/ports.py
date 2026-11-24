from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ContextManager

from boxoffice.modules.analytics.contract import MovieSummaryDto, RegionRevenueDto, TopMovieDto
from boxoffice.modules.analytics.domain.model import MovieStats


@dataclass(frozen=True)
class MovieProfile:

    title: str
    budget_usd: int


class AnalyticsStore(ABC):
    @abstractmethod
    def is_processed(self, event_id: str) -> bool: ...

    @abstractmethod
    def mark_processed(self, event_id: str) -> None: ...

    @abstractmethod
    def get_stats(self, movie_id: int) -> MovieStats | None: ...

    @abstractmethod
    def save_stats(self, stats: MovieStats) -> None: ...

    @abstractmethod
    def delete_stats(self, movie_id: int) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...


StoreFactory = "Callable[[], ContextManager[AnalyticsStore]]"


class CoreGateway(ABC):

    @abstractmethod
    def get_movie_profile(self, movie_id: int) -> MovieProfile | None: ...


class AnalyticsReadRepository(ABC):
    @abstractmethod
    def movie_summary(self, movie_id: int) -> MovieSummaryDto | None: ...

    @abstractmethod
    def top_movies(self, limit: int) -> list[TopMovieDto]: ...

    @abstractmethod
    def revenue_by_region(self) -> list[RegionRevenueDto]: ...
