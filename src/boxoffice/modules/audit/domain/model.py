from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AuditRecord:
    event_id: str
    action: str
    subject_type: str
    subject_id: int
    occurred_at: datetime
    details: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id or not self.action or not self.subject_type:
            raise ValueError("Audit record requires event_id, action and subject_type")
