from datetime import date
from typing import Callable

from boxoffice.modules.core.domain.entities import BoxOfficeReport, Movie, User
from boxoffice.modules.core.domain.errors import ConflictError, DomainValidationError
from boxoffice.modules.core.domain.ports import PasswordHasher
from boxoffice.modules.core.domain.repositories import MovieRepository, ReportRepository, UserRepository
from boxoffice.modules.core.domain.value_objects import Email, Money, RegionCode

MIN_PASSWORD_LENGTH = 8


class UserFactory:
    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        self._users = users
        self._hasher = hasher

    def create(self, email: str, raw_password: str) -> User:
        email_vo = Email(email)
        if len(raw_password or "") < MIN_PASSWORD_LENGTH:
            raise DomainValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )
        if self._users.get_by_email(email_vo) is not None:
            raise ConflictError("User with this email already exists")
        return User(email=email_vo, password_hash=self._hasher.hash(raw_password))


class MovieFactory:
    def __init__(self, movies: MovieRepository):
        self._movies = movies

    def create(self, title: str, genre: str, release_date: date, budget_usd: int) -> Movie:
        movie = Movie(
            title=title, genre=genre, release_date=release_date, budget=Money(budget_usd)
        )
        self.ensure_unique(movie)
        return movie

    def ensure_unique(self, movie: Movie) -> None:
        if self._movies.exists_by_title_and_date(
            movie.title, movie.release_date, exclude_id=movie.id
        ):
            raise ConflictError("Movie with this title and release date already exists")


class ReportFactory:
    def __init__(self, reports: ReportRepository, today: Callable[[], date] = date.today):
        self._reports = reports
        self._today = today

    def create(
        self, movie: Movie, report_date: date, region: str, revenue_usd: int, tickets_sold: int
    ) -> BoxOfficeReport:
        movie.ensure_accepts_report_for(report_date, self._today())
        report = BoxOfficeReport(
            movie_id=movie.id,
            report_date=report_date,
            region=RegionCode(region),
            revenue=Money(revenue_usd),
            tickets_sold=tickets_sold,
        )
        if self._reports.exists(movie.id, report_date, report.region):
            raise ConflictError("Report for this movie, date and region already exists")
        return report
