from dataclasses import dataclass
from datetime import date

from boxoffice.modules.core.contract.events import ReportAdded, ReportCorrected, ReportDeleted
from boxoffice.modules.core.application.side_effects import SideEffects
from boxoffice.modules.core.domain.errors import NotFoundError
from boxoffice.modules.core.domain.factories import ReportFactory
from boxoffice.modules.core.domain.repositories import MovieRepository, ReportRepository
from boxoffice.modules.core.domain.value_objects import Money


@dataclass(frozen=True)
class AddReportCommand:
    movie_id: int
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int


@dataclass(frozen=True)
class UpdateReportCommand:
    report_id: int
    revenue_usd: int
    tickets_sold: int


@dataclass(frozen=True)
class DeleteReportCommand:
    report_id: int


class AddReportHandler:
    def __init__(self, movies: MovieRepository, reports: ReportRepository, factory: ReportFactory,
                 effects: SideEffects | None = None):
        self._movies, self._reports, self._factory = movies, reports, factory
        self._effects = effects or SideEffects()

    def handle(self, cmd: AddReportCommand) -> int:
        movie = self._movies.get(cmd.movie_id)
        if movie is None:
            raise NotFoundError("Movie not found")
        report = self._reports.add(self._factory.create(
            movie, cmd.report_date, cmd.region, cmd.revenue_usd, cmd.tickets_sold))
        self._effects.emit(ReportAdded(
            report_id=report.id, movie_id=report.movie_id, report_date=report.report_date,
            region=report.region.value, revenue_usd=report.revenue.amount_usd,
            tickets_sold=report.tickets_sold))
        return report.id


class UpdateReportHandler:
    def __init__(self, reports: ReportRepository, effects: SideEffects | None = None):
        self._reports = reports
        self._effects = effects or SideEffects()

    def handle(self, cmd: UpdateReportCommand) -> None:
        report = self._reports.get(cmd.report_id)
        if report is None:
            raise NotFoundError("Report not found")
        prev_revenue, prev_tickets = report.revenue.amount_usd, report.tickets_sold
        report.correct(revenue=Money(cmd.revenue_usd), tickets_sold=cmd.tickets_sold)
        self._reports.update(report)
        self._effects.emit(ReportCorrected(
            report_id=report.id, movie_id=report.movie_id, report_date=report.report_date,
            region=report.region.value, revenue_usd=report.revenue.amount_usd,
            tickets_sold=report.tickets_sold, previous_revenue_usd=prev_revenue,
            previous_tickets_sold=prev_tickets))


class DeleteReportHandler:
    def __init__(self, reports: ReportRepository, effects: SideEffects | None = None):
        self._reports = reports
        self._effects = effects or SideEffects()

    def handle(self, cmd: DeleteReportCommand) -> None:
        report = self._reports.get(cmd.report_id)
        if report is None:
            raise NotFoundError("Report not found")
        self._reports.delete(cmd.report_id)
        self._effects.emit(ReportDeleted(
            report_id=report.id, movie_id=report.movie_id, report_date=report.report_date,
            region=report.region.value, revenue_usd=report.revenue.amount_usd,
            tickets_sold=report.tickets_sold))
