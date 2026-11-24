from dataclasses import dataclass
from datetime import date, datetime

from boxoffice.modules.core.domain.errors import DomainValidationError
from boxoffice.modules.core.domain.value_objects import Email, Money, RegionCode


@dataclass
class Movie:
    title: str
    genre: str
    release_date: date
    budget: Money
    id: int | None = None

    def __post_init__(self):
        self.title = (self.title or "").strip()
        self.genre = (self.genre or "").strip()
        if not self.title or len(self.title) > 200:
            raise DomainValidationError("Title must be 1..200 characters")
        if not self.genre or len(self.genre) > 50:
            raise DomainValidationError("Genre must be 1..50 characters")
        if self.budget.amount_usd <= 0:
            raise DomainValidationError("Budget must be greater than zero")

    def update(self, *, title: str, genre: str, release_date: date, budget: Money) -> None:
        candidate = Movie(title=title, genre=genre, release_date=release_date, budget=budget)
        self.title, self.genre = candidate.title, candidate.genre
        self.release_date, self.budget = candidate.release_date, candidate.budget

    def ensure_accepts_report_for(self, report_date: date, today: date) -> None:
        if report_date > today:
            raise DomainValidationError("Report date cannot be in the future")
        if report_date < self.release_date:
            raise DomainValidationError("Report date cannot be earlier than the movie release date")


@dataclass
class BoxOfficeReport:
    movie_id: int
    report_date: date
    region: RegionCode
    revenue: Money
    tickets_sold: int
    id: int | None = None

    def __post_init__(self):
        if isinstance(self.tickets_sold, bool) or not isinstance(self.tickets_sold, int):
            raise DomainValidationError("Tickets sold must be an integer")
        if self.tickets_sold < 0:
            raise DomainValidationError("Tickets sold cannot be negative")

    def correct(self, *, revenue: Money, tickets_sold: int) -> None:
        candidate = BoxOfficeReport(
            movie_id=self.movie_id,
            report_date=self.report_date,
            region=self.region,
            revenue=revenue,
            tickets_sold=tickets_sold,
        )
        self.revenue, self.tickets_sold = candidate.revenue, candidate.tickets_sold


@dataclass
class User:
    email: Email
    password_hash: str
    id: int | None = None
    created_at: datetime | None = None
