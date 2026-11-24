from sqlalchemy.orm import sessionmaker

from boxoffice.modules.core.contract.api import CoreApi, MovieDto
from boxoffice.modules.core.infrastructure.orm_models import MovieRow


class SqlCoreApi(CoreApi):

    def __init__(self, session_factory: sessionmaker):
        self._sf = session_factory

    def get_movie(self, movie_id: int) -> MovieDto | None:
        with self._sf() as s:
            row = s.get(MovieRow, movie_id)
            if row is None:
                return None
            return MovieDto(row.id, row.title, row.genre, row.release_date, row.budget_usd)
