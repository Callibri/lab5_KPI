from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from boxoffice.modules.core.domain.entities import BoxOfficeReport, Movie, User
from boxoffice.modules.core.domain.repositories import MovieRepository, ReportRepository, UserRepository
from boxoffice.modules.core.domain.value_objects import Email, RegionCode
from boxoffice.modules.core.infrastructure import mappers
from boxoffice.modules.core.infrastructure.orm_models import MovieRow, ReportRow, UserRow


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._s = session

    def add(self, user: User) -> User:
        row = UserRow(email=user.email.value, password_hash=user.password_hash)
        self._s.add(row)
        self._s.commit()
        return mappers.user_to_domain(row)

    def get_by_email(self, email: Email) -> User | None:
        row = self._s.scalar(select(UserRow).where(UserRow.email == email.value))
        return mappers.user_to_domain(row) if row else None


class SqlAlchemyMovieRepository(MovieRepository):
    def __init__(self, session: Session):
        self._s = session

    def add(self, movie: Movie) -> Movie:
        row = MovieRow()
        mappers.apply_movie(row, movie)
        self._s.add(row)
        self._s.commit()
        return mappers.movie_to_domain(row)

    def get(self, movie_id: int) -> Movie | None:
        row = self._s.get(MovieRow, movie_id)
        return mappers.movie_to_domain(row) if row else None

    def update(self, movie: Movie) -> Movie:
        row = self._s.get(MovieRow, movie.id)
        mappers.apply_movie(row, movie)
        self._s.commit()
        return mappers.movie_to_domain(row)

    def delete(self, movie_id: int) -> None:
        row = self._s.get(MovieRow, movie_id)
        if row is not None:
            self._s.delete(row)
            self._s.commit()

    def exists_by_title_and_date(self, title: str, release_date: date, exclude_id=None) -> bool:
        query = select(MovieRow.id).where(
            MovieRow.title == title, MovieRow.release_date == release_date
        )
        if exclude_id is not None:
            query = query.where(MovieRow.id != exclude_id)
        return self._s.scalar(query) is not None


class SqlAlchemyReportRepository(ReportRepository):
    def __init__(self, session: Session):
        self._s = session

    def add(self, report: BoxOfficeReport) -> BoxOfficeReport:
        row = ReportRow()
        mappers.apply_report(row, report)
        self._s.add(row)
        self._s.commit()
        return mappers.report_to_domain(row)

    def get(self, report_id: int) -> BoxOfficeReport | None:
        row = self._s.get(ReportRow, report_id)
        return mappers.report_to_domain(row) if row else None

    def update(self, report: BoxOfficeReport) -> BoxOfficeReport:
        row = self._s.get(ReportRow, report.id)
        mappers.apply_report(row, report)
        self._s.commit()
        return mappers.report_to_domain(row)

    def delete(self, report_id: int) -> None:
        row = self._s.get(ReportRow, report_id)
        if row is not None:
            self._s.delete(row)
            self._s.commit()

    def exists(self, movie_id: int, report_date: date, region: RegionCode) -> bool:
        query = select(ReportRow.id).where(
            ReportRow.movie_id == movie_id,
            ReportRow.report_date == report_date,
            ReportRow.region == region.value,
        )
        return self._s.scalar(query) is not None
