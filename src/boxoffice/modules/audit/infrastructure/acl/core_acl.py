from dataclasses import asdict

from boxoffice.modules.audit.application.handlers import AuditRecorder, RecordAudit
from boxoffice.modules.core.contract import (
    MovieCreated, MovieDeleted, MovieUpdated, ReportAdded, ReportCorrected, ReportDeleted,
    UserRegistered,
)
from boxoffice.shared.events import IntegrationEvent

_MAP = {
    UserRegistered: ("user.registered", "user", "user_id"),
    MovieCreated: ("movie.created", "movie", "movie_id"),
    MovieUpdated: ("movie.updated", "movie", "movie_id"),
    MovieDeleted: ("movie.deleted", "movie", "movie_id"),
    ReportAdded: ("report.added", "report", "report_id"),
    ReportCorrected: ("report.corrected", "report", "report_id"),
    ReportDeleted: ("report.deleted", "report", "report_id"),
}
SUBSCRIBED_EVENTS = tuple(_MAP)


class CoreEventTranslator:
    def translate(self, event: IntegrationEvent) -> RecordAudit | None:
        mapping = _MAP.get(type(event))
        if mapping is None:
            return None
        action, subject_type, id_field = mapping
        data = asdict(event)
        details = {k: v for k, v in data.items() if k not in ("event_id", "occurred_at", id_field)}
        return RecordAudit(event.event_id, action, subject_type, data[id_field], event.occurred_at, details)


class CoreEventsSubscriber:
    def __init__(self, translator: CoreEventTranslator, recorder: AuditRecorder):
        self._translator, self._recorder = translator, recorder

    def __call__(self, event: IntegrationEvent) -> None:
        command = self._translator.translate(event)
        if command is not None:
            self._recorder.handle(command)
