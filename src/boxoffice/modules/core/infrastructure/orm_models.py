from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class MovieRow(Base):
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("title", "release_date", name="uq_movie_title_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str] = mapped_column(String(50))
    release_date: Mapped[date] = mapped_column(Date)
    budget_usd: Mapped[int] = mapped_column(Integer)

    reports: Mapped[list["ReportRow"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )


class ReportRow(Base):
    __tablename__ = "box_office_reports"
    __table_args__ = (
        UniqueConstraint("movie_id", "report_date", "region", name="uq_report_movie_date_region"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    report_date: Mapped[date] = mapped_column(Date)
    region: Mapped[str] = mapped_column(String(2))
    revenue_usd: Mapped[int] = mapped_column(Integer)
    tickets_sold: Mapped[int] = mapped_column(Integer)

    movie: Mapped[MovieRow] = relationship(back_populates="reports")
