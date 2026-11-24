from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MovieListItem:
    id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int
    total_revenue_usd: int


@dataclass(frozen=True)
class MovieDetails:
    id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int
    total_revenue_usd: int
    total_tickets: int
    reports_count: int


@dataclass(frozen=True)
class ReportItem:
    id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int
    avg_ticket_price_usd: float | None


@dataclass(frozen=True)
class UserCredentials:
    user_id: int
    password_hash: str
