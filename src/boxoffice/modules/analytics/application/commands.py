from dataclasses import dataclass


@dataclass(frozen=True)
class UpsertMovieProfile:
    event_id: str
    movie_id: int
    title: str
    budget_usd: int


@dataclass(frozen=True)
class ForgetMovie:
    event_id: str
    movie_id: int


@dataclass(frozen=True)
class ApplyRevenueDelta:

    event_id: str
    movie_id: int
    region: str
    revenue_delta: int
    tickets_delta: int
