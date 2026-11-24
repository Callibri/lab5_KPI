from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AnalyticsBase(DeclarativeBase):
    pass


class MovieStatsRow(AnalyticsBase):
    __tablename__ = "an_movie_stats"

    movie_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    budget_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_revenue_usd: Mapped[int] = mapped_column(Integer, default=0)
    total_tickets: Mapped[int] = mapped_column(Integer, default=0)


class MovieRegionRow(AnalyticsBase):
    __tablename__ = "an_movie_region"

    movie_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    region: Mapped[str] = mapped_column(String(2), primary_key=True)
    revenue_usd: Mapped[int] = mapped_column(Integer, default=0)
    tickets: Mapped[int] = mapped_column(Integer, default=0)


class ProcessedEventRow(AnalyticsBase):
    __tablename__ = "an_processed_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
