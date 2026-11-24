from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from boxoffice.modules.audit.contract import AuditApi, AuditEntryDto
from boxoffice.modules.audit.domain.model import AuditRecord


@dataclass(frozen=True)
class RecordAudit:

    event_id: str
    action: str
    subject_type: str
    subject_id: int
    occurred_at: datetime
    details: dict = field(default_factory=dict)


class AuditRepository(ABC):
    @abstractmethod
    def add(self, record: AuditRecord) -> bool:
        pass

    @abstractmethod
    def list(self, limit: int, offset: int, subject_type: str | None) -> list[AuditRecord]: ...


class AuditRecorder:
    def __init__(self, repo: AuditRepository):
        self._repo = repo

    def handle(self, cmd: RecordAudit) -> bool:
        return self._repo.add(AuditRecord(cmd.event_id, cmd.action, cmd.subject_type, cmd.subject_id,
                                          cmd.occurred_at, cmd.details))


class AuditFacade(AuditApi):
    def __init__(self, repo: AuditRepository):
        self._repo = repo

    def list_entries(self, limit=50, offset=0, subject_type=None) -> list[AuditEntryDto]:
        return [AuditEntryDto(r.event_id, r.action, r.subject_type, r.subject_id, r.occurred_at, r.details)
                for r in self._repo.list(limit, offset, subject_type)]
