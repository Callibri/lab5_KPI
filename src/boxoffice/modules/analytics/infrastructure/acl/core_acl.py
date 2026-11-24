from boxoffice.modules.analytics.application.commands import (
    ApplyRevenueDelta, ForgetMovie, UpsertMovieProfile,
)
from boxoffice.modules.analytics.application.handlers import AnalyticsCommand
from boxoffice.modules.analytics.application.ports import CoreGateway, MovieProfile
from boxoffice.modules.core.contract import (
    CoreApi, MovieCreated, MovieDeleted, MovieUpdated, ReportAdded, ReportCorrected, ReportDeleted,
)
from boxoffice.shared.events import IntegrationEvent

SUBSCRIBED_EVENTS = (MovieCreated, MovieUpdated, MovieDeleted, ReportAdded, ReportCorrected, ReportDeleted)


class CoreEventTranslator:

    def translate(self, event: IntegrationEvent) -> list[AnalyticsCommand]:
        if isinstance(event, (MovieCreated, MovieUpdated)):
            return [UpsertMovieProfile(event.event_id, event.movie_id, event.title, event.budget_usd)]
        if isinstance(event, MovieDeleted):
            return [ForgetMovie(event.event_id, event.movie_id)]
        if isinstance(event, ReportAdded):
            return [ApplyRevenueDelta(event.event_id, event.movie_id, event.region,
                                      event.revenue_usd, event.tickets_sold)]
        if isinstance(event, ReportCorrected):
            return [ApplyRevenueDelta(event.event_id, event.movie_id, event.region,
                                      event.revenue_usd - event.previous_revenue_usd,
                                      event.tickets_sold - event.previous_tickets_sold)]
        if isinstance(event, ReportDeleted):
            return [ApplyRevenueDelta(event.event_id, event.movie_id, event.region,
                                      -event.revenue_usd, -event.tickets_sold)]
        return []


class CoreGatewayAdapter(CoreGateway):

    def __init__(self, core_api: CoreApi):
        self._core = core_api

    def get_movie_profile(self, movie_id: int) -> MovieProfile | None:
        dto = self._core.get_movie(movie_id)
        return MovieProfile(dto.title, dto.budget_usd) if dto else None
