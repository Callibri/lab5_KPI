from typing import Iterator

from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from boxoffice.modules.core.application.commands.movies import (
    CreateMovieHandler, DeleteMovieHandler, UpdateMovieHandler,
)
from boxoffice.modules.core.application.commands.reports import (
    AddReportHandler, DeleteReportHandler, UpdateReportHandler,
)
from boxoffice.modules.core.application.commands.users import RegisterUserHandler
from boxoffice.modules.core.application.ports import TokenService
from boxoffice.modules.core.application.queries.handlers import (
    GetMovieQueryHandler, ListMoviesQueryHandler, ListReportsQueryHandler, LoginQueryHandler,
)
from boxoffice.modules.core.application.registry import Handlers
from boxoffice.modules.core.application.side_effects import SideEffects
from boxoffice.modules.core.contract import CoreApi
from boxoffice.modules.core.domain.factories import MovieFactory, ReportFactory, UserFactory
from boxoffice.modules.core.domain.ports import PasswordHasher
from boxoffice.modules.core.infrastructure.facade import SqlCoreApi
from boxoffice.modules.core.infrastructure.orm_models import Base
from boxoffice.modules.core.infrastructure.read_repositories import (
    SqlCredentialsReadRepository, SqlMovieReadRepository, SqlReportReadRepository,
)
from boxoffice.modules.core.infrastructure.repositories import (
    SqlAlchemyMovieRepository, SqlAlchemyReportRepository, SqlAlchemyUserRepository,
)
from boxoffice.modules.core.presentation.api import install as install_http
from boxoffice.shared.events import EventPublisher


class CoreModule:
    def __init__(self, engine: Engine, session_factory: sessionmaker, publisher: EventPublisher,
                 hasher: PasswordHasher, tokens: TokenService):
        Base.metadata.create_all(engine)
        self._sf, self._hasher, self._tokens = session_factory, hasher, tokens
        self._effects = SideEffects(publisher)
        self.api: CoreApi = SqlCoreApi(session_factory)

    def _build(self, session: Session) -> Handlers:
        users = SqlAlchemyUserRepository(session)
        movies = SqlAlchemyMovieRepository(session)
        reports = SqlAlchemyReportRepository(session)
        movie_factory = MovieFactory(movies)
        fx = self._effects
        return Handlers(
            register_user=RegisterUserHandler(UserFactory(users, self._hasher), users, fx),
            create_movie=CreateMovieHandler(movie_factory, movies, fx),
            update_movie=UpdateMovieHandler(movie_factory, movies, fx),
            delete_movie=DeleteMovieHandler(movies, fx),
            add_report=AddReportHandler(movies, reports, ReportFactory(reports), fx),
            update_report=UpdateReportHandler(reports, fx),
            delete_report=DeleteReportHandler(reports, fx),
            login=LoginQueryHandler(SqlCredentialsReadRepository(session), self._hasher, self._tokens),
            list_movies=ListMoviesQueryHandler(SqlMovieReadRepository(session)),
            get_movie=GetMovieQueryHandler(SqlMovieReadRepository(session)),
            list_reports=ListReportsQueryHandler(SqlReportReadRepository(session)),
        )

    def _scope(self) -> Iterator[Handlers]:
        with self._sf() as session:
            yield self._build(session)

    def install(self, app: FastAPI) -> None:
        install_http(app, self._scope)
