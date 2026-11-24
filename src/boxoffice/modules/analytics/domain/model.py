from dataclasses import dataclass, field


class ProjectionInconsistencyError(Exception):
    pass


@dataclass
class MovieStats:
    movie_id: int
    title: str | None = None
    budget_usd: int | None = None
    total_revenue_usd: int = 0
    total_tickets: int = 0
    revenue_by_region: dict[str, int] = field(default_factory=dict)
    tickets_by_region: dict[str, int] = field(default_factory=dict)

    def set_profile(self, title: str, budget_usd: int) -> None:
        self.title, self.budget_usd = title, budget_usd

    def apply_delta(self, region: str, revenue_delta: int, tickets_delta: int) -> None:
        new_rev = self.revenue_by_region.get(region, 0) + revenue_delta
        new_tickets = self.tickets_by_region.get(region, 0) + tickets_delta
        if new_rev < 0 or new_tickets < 0:
            raise ProjectionInconsistencyError(
                f"Negative totals for movie {self.movie_id}, region {region}")
        self.revenue_by_region[region] = new_rev
        self.tickets_by_region[region] = new_tickets
        self.total_revenue_usd += revenue_delta
        self.total_tickets += tickets_delta

    @property
    def avg_ticket_price_usd(self) -> float | None:
        return round(self.total_revenue_usd / self.total_tickets, 2) if self.total_tickets else None

    @property
    def roi(self) -> float | None:
        if not self.budget_usd:
            return None
        return round((self.total_revenue_usd - self.budget_usd) / self.budget_usd, 4)
