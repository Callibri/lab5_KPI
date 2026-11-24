from dataclasses import dataclass

from boxoffice.modules.core.application.commands.movies import CreateMovieHandler, DeleteMovieHandler, UpdateMovieHandler
from boxoffice.modules.core.application.commands.reports import AddReportHandler, DeleteReportHandler, UpdateReportHandler
from boxoffice.modules.core.application.commands.users import RegisterUserHandler
from boxoffice.modules.core.application.queries.handlers import (
    GetMovieQueryHandler, ListMoviesQueryHandler, ListReportsQueryHandler, LoginQueryHandler,
)


@dataclass
class Handlers:
    register_user: RegisterUserHandler
    create_movie: CreateMovieHandler
    update_movie: UpdateMovieHandler
    delete_movie: DeleteMovieHandler
    add_report: AddReportHandler
    update_report: UpdateReportHandler
    delete_report: DeleteReportHandler
    login: LoginQueryHandler
    list_movies: ListMoviesQueryHandler
    get_movie: GetMovieQueryHandler
    list_reports: ListReportsQueryHandler
