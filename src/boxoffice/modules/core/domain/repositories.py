from abc import ABC, abstractmethod
from datetime import date

from boxoffice.modules.core.domain.entities import BoxOfficeReport, Movie, User
from boxoffice.modules.core.domain.value_objects import Email, RegionCode


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None: ...


class MovieRepository(ABC):
    @abstractmethod
    def add(self, movie: Movie) -> Movie: ...

    @abstractmethod
    def get(self, movie_id: int) -> Movie | None: ...

    @abstractmethod
    def update(self, movie: Movie) -> Movie: ...

    @abstractmethod
    def delete(self, movie_id: int) -> None: ...

    @abstractmethod
    def exists_by_title_and_date(
        self, title: str, release_date: date, exclude_id: int | None = None
    ) -> bool: ...


class ReportRepository(ABC):
    @abstractmethod
    def add(self, report: BoxOfficeReport) -> BoxOfficeReport: ...

    @abstractmethod
    def get(self, report_id: int) -> BoxOfficeReport | None: ...

    @abstractmethod
    def update(self, report: BoxOfficeReport) -> BoxOfficeReport: ...

    @abstractmethod
    def delete(self, report_id: int) -> None: ...

    @abstractmethod
    def exists(self, movie_id: int, report_date: date, region: RegionCode) -> bool: ...
