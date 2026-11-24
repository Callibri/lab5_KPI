from datetime import date

from fastapi import APIRouter, Depends, Query, Response

from boxoffice.modules.core.application.commands.movies import CreateMovieCommand, DeleteMovieCommand, UpdateMovieCommand
from boxoffice.modules.core.application.commands.reports import AddReportCommand, DeleteReportCommand, UpdateReportCommand
from boxoffice.modules.core.application.commands.users import RegisterUserCommand
from boxoffice.modules.core.application.queries.handlers import (
    GetMovieQuery, ListMoviesQuery, ListReportsQuery, LoginQuery,
)
from boxoffice.modules.core.application.registry import Handlers
from boxoffice.modules.core.presentation.dependencies import get_handlers, require_user
from boxoffice.modules.core.presentation.schemas import (
    CreatedResponse, LoginRequest, MovieRequest, RegisterRequest, ReportRequest,
    ReportUpdateRequest, TokenResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
movies_router = APIRouter(prefix="/movies", tags=["movies"], dependencies=[Depends(require_user)])
reports_router = APIRouter(tags=["reports"], dependencies=[Depends(require_user)])


@auth_router.post("/register", status_code=201, response_model=CreatedResponse)
def register(body: RegisterRequest, h: Handlers = Depends(get_handlers)):
    return CreatedResponse(id=h.register_user.handle(RegisterUserCommand(body.email, body.password)))


@auth_router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, h: Handlers = Depends(get_handlers)):
    return TokenResponse(access_token=h.login.handle(LoginQuery(body.email, body.password)))


@movies_router.post("", status_code=201, response_model=CreatedResponse)
def create_movie(body: MovieRequest, h: Handlers = Depends(get_handlers)):
    cmd = CreateMovieCommand(body.title, body.genre, body.release_date, body.budget_usd)
    return CreatedResponse(id=h.create_movie.handle(cmd))


@movies_router.put("/{movie_id}", status_code=204)
def update_movie(movie_id: int, body: MovieRequest, h: Handlers = Depends(get_handlers)):
    h.update_movie.handle(UpdateMovieCommand(movie_id, body.title, body.genre, body.release_date, body.budget_usd))
    return Response(status_code=204)


@movies_router.delete("/{movie_id}", status_code=204)
def delete_movie(movie_id: int, h: Handlers = Depends(get_handlers)):
    h.delete_movie.handle(DeleteMovieCommand(movie_id))
    return Response(status_code=204)


@movies_router.get("")
def list_movies(
    genre: str | None = None,
    year: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    h: Handlers = Depends(get_handlers),
):
    return h.list_movies.handle(ListMoviesQuery(genre, year, limit, offset))


@movies_router.get("/{movie_id}")
def get_movie(movie_id: int, h: Handlers = Depends(get_handlers)):
    return h.get_movie.handle(GetMovieQuery(movie_id))


@reports_router.post("/movies/{movie_id}/reports", status_code=201, response_model=CreatedResponse)
def add_report(movie_id: int, body: ReportRequest, h: Handlers = Depends(get_handlers)):
    cmd = AddReportCommand(movie_id, body.report_date, body.region, body.revenue_usd, body.tickets_sold)
    return CreatedResponse(id=h.add_report.handle(cmd))


@reports_router.put("/reports/{report_id}", status_code=204)
def update_report(report_id: int, body: ReportUpdateRequest, h: Handlers = Depends(get_handlers)):
    h.update_report.handle(UpdateReportCommand(report_id, body.revenue_usd, body.tickets_sold))
    return Response(status_code=204)


@reports_router.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: int, h: Handlers = Depends(get_handlers)):
    h.delete_report.handle(DeleteReportCommand(report_id))
    return Response(status_code=204)


@reports_router.get("/movies/{movie_id}/reports")
def list_reports(
    movie_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    region: str | None = None,
    h: Handlers = Depends(get_handlers),
):
    return h.list_reports.handle(ListReportsQuery(movie_id, date_from, date_to, region))
