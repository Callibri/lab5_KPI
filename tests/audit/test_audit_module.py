import pytest

from boxoffice.modules.audit.application.handlers import AuditFacade, AuditRecorder, RecordAudit
from boxoffice.modules.audit.infrastructure.acl.core_acl import CoreEventTranslator
from boxoffice.modules.audit.infrastructure.sql import AuditBase, SqlAuditRepository
from boxoffice.modules.core.contract import MovieCreated, ReportAdded, UserRegistered
from boxoffice.shared.db import make_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timezone


@pytest.fixture()
def repo(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'a.db'}")
    AuditBase.metadata.create_all(engine)
    return SqlAuditRepository(sessionmaker(bind=engine, expire_on_commit=False))


def cmd(event_id="e1", subject_type="movie", subject_id=1):
    return RecordAudit(event_id, "movie.created", subject_type, subject_id, datetime.now(timezone.utc), {"t": 1})


def test_record_is_idempotent(repo):
    recorder = AuditRecorder(repo)
    assert recorder.handle(cmd("same")) is True
    assert recorder.handle(cmd("same")) is False
    assert len(AuditFacade(repo).list_entries()) == 1


def test_filter_by_subject(repo):
    recorder = AuditRecorder(repo)
    recorder.handle(cmd("a", "movie"))
    recorder.handle(cmd("b", "report"))
    assert [e.subject_type for e in AuditFacade(repo).list_entries(subject_type="report")] == ["report"]


def test_acl_translates_core_events_to_internal_command():
    t = CoreEventTranslator()
    e = MovieCreated(movie_id=5, title="Dune", genre="g", release_date=date(2024, 1, 1), budget_usd=10)
    c = t.translate(e)
    assert (c.action, c.subject_type, c.subject_id, c.event_id) == ("movie.created", "movie", 5, e.event_id)
    assert c.details["title"] == "Dune" and "movie_id" not in c.details
    r = t.translate(ReportAdded(report_id=3, movie_id=5, report_date=date(2024, 1, 2), region="US",
                                revenue_usd=1, tickets_sold=1))
    assert (r.action, r.subject_id) == ("report.added", 3)
    assert t.translate(UserRegistered(user_id=9, email="a@b.com")).action == "user.registered"
