from boxoffice.modules.core.domain.entities import BoxOfficeReport, Movie, User
from boxoffice.modules.core.domain.value_objects import Email, Money, RegionCode
from boxoffice.modules.core.infrastructure.orm_models import MovieRow, ReportRow, UserRow


def movie_to_domain(row: MovieRow) -> Movie:
    return Movie(
        id=row.id,
        title=row.title,
        genre=row.genre,
        release_date=row.release_date,
        budget=Money(row.budget_usd),
    )


def apply_movie(row: MovieRow, movie: Movie) -> None:
    row.title, row.genre = movie.title, movie.genre
    row.release_date, row.budget_usd = movie.release_date, movie.budget.amount_usd


def report_to_domain(row: ReportRow) -> BoxOfficeReport:
    return BoxOfficeReport(
        id=row.id,
        movie_id=row.movie_id,
        report_date=row.report_date,
        region=RegionCode(row.region),
        revenue=Money(row.revenue_usd),
        tickets_sold=row.tickets_sold,
    )


def apply_report(row: ReportRow, report: BoxOfficeReport) -> None:
    row.movie_id, row.report_date = report.movie_id, report.report_date
    row.region, row.revenue_usd = report.region.value, report.revenue.amount_usd
    row.tickets_sold = report.tickets_sold


def user_to_domain(row: UserRow) -> User:
    return User(
        id=row.id, email=Email(row.email), password_hash=row.password_hash, created_at=row.created_at
    )
