from dataclasses import dataclass
from datetime import date

from boxoffice.modules.core.contract.events import MovieCreated, MovieDeleted, MovieUpdated
from boxoffice.modules.core.application.side_effects import SideEffects
from boxoffice.modules.core.domain.errors import NotFoundError
from boxoffice.modules.core.domain.factories import MovieFactory
from boxoffice.modules.core.domain.repositories import MovieRepository
from boxoffice.modules.core.domain.value_objects import Money


@dataclass(frozen=True)
class CreateMovieCommand:
    title: str
    genre: str
    release_date: date
    budget_usd: int


@dataclass(frozen=True)
class UpdateMovieCommand:
    movie_id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int


@dataclass(frozen=True)
class DeleteMovieCommand:
    movie_id: int


class CreateMovieHandler:
    def __init__(self, factory: MovieFactory, movies: MovieRepository, effects: SideEffects | None = None):
        self._factory, self._movies = factory, movies
        self._effects = effects or SideEffects()

    def handle(self, cmd: CreateMovieCommand) -> int:
        movie = self._movies.add(
            self._factory.create(cmd.title, cmd.genre, cmd.release_date, cmd.budget_usd)
        )
        self._effects.emit(MovieCreated(
            movie_id=movie.id, title=movie.title, genre=movie.genre,
            release_date=movie.release_date, budget_usd=movie.budget.amount_usd))
        return movie.id


class UpdateMovieHandler:
    def __init__(self, factory: MovieFactory, movies: MovieRepository, effects: SideEffects | None = None):
        self._factory, self._movies = factory, movies
        self._effects = effects or SideEffects()

    def handle(self, cmd: UpdateMovieCommand) -> None:
        movie = self._movies.get(cmd.movie_id)
        if movie is None:
            raise NotFoundError("Movie not found")
        movie.update(title=cmd.title, genre=cmd.genre, release_date=cmd.release_date,
                     budget=Money(cmd.budget_usd))
        self._factory.ensure_unique(movie)
        self._movies.update(movie)
        self._effects.emit(MovieUpdated(
            movie_id=movie.id, title=movie.title, genre=movie.genre,
            release_date=movie.release_date, budget_usd=movie.budget.amount_usd))


class DeleteMovieHandler:
    def __init__(self, movies: MovieRepository, effects: SideEffects | None = None):
        self._movies = movies
        self._effects = effects or SideEffects()

    def handle(self, cmd: DeleteMovieCommand) -> None:
        movie = self._movies.get(cmd.movie_id)
        if movie is None:
            raise NotFoundError("Movie not found")
        self._movies.delete(cmd.movie_id)
        self._effects.emit(MovieDeleted(movie_id=movie.id, title=movie.title))
