from dataclasses import dataclass, field


@dataclass(frozen=True)
class ForecastInputs:
    """Precomputed once per customer from historical transactions, then reused
    by both the baseline forecast and every scenario recompute."""

    recurring_net: float
    disc_avg: dict[str, float]
    seasonal_index: dict[str, dict[int, float]]
    sigma: float
    anchor_month: int  # calendar month (1-12) of the last historical month


@dataclass(frozen=True)
class ForecastMonth:
    month_index: int  # 1..N, months into the future
    calendar_month: int  # 1-12
    net_cashflow: float
    balance: float
    balance_low: float
    balance_high: float


@dataclass(frozen=True)
class ForecastResult:
    starting_balance: float
    months: list[ForecastMonth] = field(default_factory=list)
