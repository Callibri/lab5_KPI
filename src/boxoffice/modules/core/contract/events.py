from dataclasses import dataclass
from datetime import date

from boxoffice.shared.events import IntegrationEvent


@dataclass(frozen=True, kw_only=True)
class UserRegistered(IntegrationEvent):
    user_id: int
    email: str


@dataclass(frozen=True, kw_only=True)
class MovieCreated(IntegrationEvent):
    movie_id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int


@dataclass(frozen=True, kw_only=True)
class MovieUpdated(IntegrationEvent):
    movie_id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int


@dataclass(frozen=True, kw_only=True)
class MovieDeleted(IntegrationEvent):
    movie_id: int
    title: str


@dataclass(frozen=True, kw_only=True)
class ReportAdded(IntegrationEvent):
    report_id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int


@dataclass(frozen=True, kw_only=True)
class ReportCorrected(IntegrationEvent):
    report_id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int
    previous_revenue_usd: int
    previous_tickets_sold: int


@dataclass(frozen=True, kw_only=True)
class ReportDeleted(IntegrationEvent):
    report_id: int
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int
