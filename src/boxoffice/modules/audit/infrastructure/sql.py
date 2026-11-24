import json
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from boxoffice.modules.audit.application.handlers import AuditRepository
from boxoffice.modules.audit.domain.model import AuditRecord


class AuditBase(DeclarativeBase):
    pass


class AuditRow(AuditBase):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    subject_type: Mapped[str] = mapped_column(String(20), index=True)
    subject_id: Mapped[int] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    details_json: Mapped[str] = mapped_column(Text)


class SqlAuditRepository(AuditRepository):
    def __init__(self, session_factory: sessionmaker):
        self._sf = session_factory

    def add(self, record: AuditRecord) -> bool:
        with self._sf() as s:
            s.add(AuditRow(event_id=record.event_id, action=record.action, subject_type=record.subject_type,
                           subject_id=record.subject_id, occurred_at=record.occurred_at.replace(tzinfo=None),
                           details_json=json.dumps(record.details, default=str, ensure_ascii=False)))
            try:
                s.commit()
                return True
            except IntegrityError:
                s.rollback()
                return False

    def list(self, limit, offset, subject_type) -> list[AuditRecord]:
        with self._sf() as s:
            q = select(AuditRow).order_by(AuditRow.id)
            if subject_type:
                q = q.where(AuditRow.subject_type == subject_type)
            return [AuditRecord(r.event_id, r.action, r.subject_type, r.subject_id, r.occurred_at,
                                json.loads(r.details_json)) for r in s.scalars(q.limit(limit).offset(offset))]
