from dataclasses import replace
from datetime import date

from boxoffice.modules.core.application.ports import TokenService
from boxoffice.modules.core.domain.entities import BoxOfficeReport, Movie, User
from boxoffice.modules.core.domain.errors import AuthenticationError
from boxoffice.modules.core.domain.ports import PasswordHasher
from boxoffice.modules.core.domain.repositories import MovieRepository, ReportRepository, UserRepository


class FakeHasher(PasswordHasher):
    def hash(self, raw_password):
        return f"hashed:{raw_password}"

    def verify(self, raw_password, password_hash):
        return password_hash == f"hashed:{raw_password}"


class FakeTokens(TokenService):
    def issue(self, user_id):
        return f"token-{user_id}"

    def verify(self, token):
        if not token.startswith("token-"):
            raise AuthenticationError("bad token")
        return int(token.split("-")[1])


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self.items: dict[int, User] = {}

    def add(self, user):
        saved = replace(user, id=len(self.items) + 1)
        self.items[saved.id] = saved
        return saved

    def get_by_email(self, email):
        return next((u for u in self.items.values() if u.email == email), None)


class InMemoryMovieRepository(MovieRepository):
    def __init__(self):
        self.items: dict[int, Movie] = {}
        self.add_calls = 0

    def add(self, movie):
        self.add_calls += 1
        saved = replace(movie, id=len(self.items) + 1)
        self.items[saved.id] = saved
        return saved

    def get(self, movie_id):
        movie = self.items.get(movie_id)
        return replace(movie) if movie else None

    def update(self, movie):
        self.items[movie.id] = replace(movie)
        return movie

    def delete(self, movie_id):
        self.items.pop(movie_id, None)

    def exists_by_title_and_date(self, title, release_date: date, exclude_id=None):
        return any(m.title == title and m.release_date == release_date and m.id != exclude_id
                   for m in self.items.values())


class InMemoryReportRepository(ReportRepository):
    def __init__(self):
        self.items: dict[int, BoxOfficeReport] = {}

    def add(self, report):
        saved = replace(report, id=len(self.items) + 1)
        self.items[saved.id] = saved
        return saved

    def get(self, report_id):
        report = self.items.get(report_id)
        return replace(report) if report else None

    def update(self, report):
        self.items[report.id] = replace(report)
        return report

    def delete(self, report_id):
        self.items.pop(report_id, None)

    def exists(self, movie_id, report_date, region):
        return any(r.movie_id == movie_id and r.report_date == report_date and r.region == region
                   for r in self.items.values())


class FakePublisher:
    def __init__(self, fail: bool = False):
        self.events, self.fail = [], fail

    def publish(self, event):
        if self.fail:
            raise RuntimeError("bus is down")
        self.events.append(event)
