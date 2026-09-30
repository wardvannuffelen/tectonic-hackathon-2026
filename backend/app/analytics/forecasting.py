"""The shared forecasting engine. Deterministic, stdlib-only — no ML, no LLM.

build_forecast_inputs() runs once per customer over their transaction
history. forecast_balance() consumes those inputs to project N months
forward, and is reused unchanged by both the baseline forecast and every
"what if I save X extra per month" scenario (see analytics/scenario.py).
"""
import math
import statistics
from collections import defaultdict

from app.analytics.recurring import detect_recurring
from app.analytics.seasonality import seasonal_index
from app.models.forecast import ForecastInputs, ForecastMonth, ForecastResult
from app.models.transaction import Transaction

# A pattern counts as part of the flat monthly baseline when it recurs on a
# roughly monthly cadence (salary, rent, subscriptions, monthly insurance,
# transport pass, ...) regardless of category — classification is by
# behaviour, not by a hardcoded category list. Annual lump sums (insurance,
# annual_bill) fall through to the seasonal/discretionary bucket below, so
# they surface as a once-a-year spike instead of being double-counted here.
#
# The cadence check needs a *band*, not just an upper bound: a burst of
# several transactions within the same week (e.g. a summer vacation) has a
# small *average gap* too, since detect_recurring() only measures the mean
# gap between consecutive occurrences — it doesn't know the whole burst only
# happens once a year. Requiring the gap to sit near ~30 days excludes bursts
# (gap of a few days) as well as genuinely annual items.
_MONTHLY_RECURRING_KINDS = {"fixed", "variable_recurring"}
_MONTHLY_CADENCE_MIN_DAYS = 20
_MONTHLY_CADENCE_MAX_DAYS = 40

# Uncertainty band width multiplier (z=1.0 gives roughly a 68% band).
_Z = 1.0

MONTHS_OF_HISTORY = 12


def build_forecast_inputs(transactions: list[Transaction]) -> ForecastInputs:
    patterns = detect_recurring(transactions)

    recurring_keys = {
        p.key for p in patterns
        if p.kind in _MONTHLY_RECURRING_KINDS
        and _MONTHLY_CADENCE_MIN_DAYS <= p.frequency_days <= _MONTHLY_CADENCE_MAX_DAYS
    }
    recurring_net = sum(
        p.avg_amount for p in patterns if p.key in recurring_keys
    )

    # Everything not part of the flat monthly baseline is discretionary /
    # seasonal: groceries, eating out, vacations, annual lump sums, etc.
    remaining = [t for t in transactions if f"{t.category}:{t.description}" not in recurring_keys]

    disc_avg: dict[str, float] = defaultdict(float)
    for t in remaining:
        disc_avg[t.category] += t.amount / MONTHS_OF_HISTORY

    # Historical monthly net cashflow (all transactions), for the uncertainty band.
    monthly_net: dict[tuple[int, int], float] = defaultdict(float)
    for t in transactions:
        monthly_net[(t.date.year, t.date.month)] += t.amount
    net_values = list(monthly_net.values())
    sigma = statistics.pstdev(net_values) if len(net_values) > 1 else 0.0

    anchor_month = max(t.date for t in transactions).month

    return ForecastInputs(
        recurring_net=recurring_net,
        disc_avg=dict(disc_avg),
        seasonal_index=seasonal_index(remaining),
        sigma=sigma,
        anchor_month=anchor_month,
    )


def forecast_balance(
    inputs: ForecastInputs,
    starting_balance: float,
    months: int = 12,
    extra_monthly_delta: float = 0.0,
) -> ForecastResult:
    result_months: list[ForecastMonth] = []
    balance = starting_balance

    for m in range(1, months + 1):
        calendar_month = ((inputs.anchor_month - 1 + m) % 12) + 1

        seasonal_component = 0.0
        for category, avg in inputs.disc_avg.items():
            index = inputs.seasonal_index.get(category, {}).get(calendar_month, 1.0)
            seasonal_component += avg * index

        net = inputs.recurring_net + seasonal_component + extra_monthly_delta
        balance += net

        band_width = inputs.sigma * math.sqrt(m)
        result_months.append(ForecastMonth(
            month_index=m,
            calendar_month=calendar_month,
            net_cashflow=round(net, 2),
            balance=round(balance, 2),
            balance_low=round(balance - _Z * band_width, 2),
            balance_high=round(balance + _Z * band_width, 2),
        ))

    return ForecastResult(starting_balance=starting_balance, months=result_months)
