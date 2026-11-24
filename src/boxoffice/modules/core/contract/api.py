from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MovieDto:
    movie_id: int
    title: str
    genre: str
    release_date: date
    budget_usd: int


class CoreApi(ABC):
    @abstractmethod
    def get_movie(self, movie_id: int) -> MovieDto | None: ...
