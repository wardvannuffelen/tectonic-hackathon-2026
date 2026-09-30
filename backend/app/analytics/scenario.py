"""Scenario recompute: "what if I save X extra per month?" Pure code, no LLM
involved — reuses the same forecasting engine as the baseline forecast so the
math can never drift between the two.
"""
from app.analytics.forecasting import forecast_balance
from app.models.forecast import ForecastInputs, ForecastResult


def apply_scenario(
    inputs: ForecastInputs,
    starting_balance: float,
    extra_savings_per_month: float,
    months: int = 12,
) -> ForecastResult:
    return forecast_balance(
        inputs,
        starting_balance,
        months=months,
        extra_monthly_delta=extra_savings_per_month,
    )
