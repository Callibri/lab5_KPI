from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RegionRevenueDto:
    region: str
    revenue_usd: int


@dataclass(frozen=True)
class MovieSummaryDto:
    movie_id: int
    title: str | None
    budget_usd: int | None
    total_revenue_usd: int
    total_tickets: int
    avg_ticket_price_usd: float | None
    roi: float | None
    revenue_by_region: list[RegionRevenueDto]


@dataclass(frozen=True)
class TopMovieDto:
    movie_id: int
    title: str | None
    total_revenue_usd: int
    total_tickets: int
    roi: float | None


class AnalyticsApi(ABC):
    @abstractmethod
    def movie_summary(self, movie_id: int) -> MovieSummaryDto | None: ...

    @abstractmethod
    def top_movies(self, limit: int) -> list[TopMovieDto]: ...

    @abstractmethod
    def revenue_by_region(self) -> list[RegionRevenueDto]: ...


__all__ = ["AnalyticsApi", "MovieSummaryDto", "TopMovieDto", "RegionRevenueDto"]
