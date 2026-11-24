from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AuditEntryDto:
    event_id: str
    action: str
    subject_type: str
    subject_id: int
    occurred_at: datetime
    details: dict = field(default_factory=dict)


class AuditApi(ABC):
    @abstractmethod
    def list_entries(self, limit: int = 50, offset: int = 0, subject_type: str | None = None) -> list[AuditEntryDto]: ...


__all__ = ["AuditApi", "AuditEntryDto"]
