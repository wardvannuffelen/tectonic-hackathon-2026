"""Dataclass -> Pydantic mapping helpers, shared by the REST routers and the
chat tool dispatch (chat/tools.py) so both paths return identical shapes."""
from app.analytics.savings_sources import SavingsSuggestion
from app.models.forecast import ForecastResult
from app.models.goal import GoalResult
from app.models.schemas import (
    ForecastMonthOut,
    ForecastResponse,
    GoalResultOut,
    SavingsSuggestionOut,
)


def forecast_to_out(result: ForecastResult) -> ForecastResponse:
    return ForecastResponse(
        starting_balance=result.starting_balance,
        months=[
            ForecastMonthOut(
                month_index=m.month_index,
                calendar_month=m.calendar_month,
                net_cashflow=m.net_cashflow,
                balance=m.balance,
                balance_low=m.balance_low,
                balance_high=m.balance_high,
            )
            for m in result.months
        ],
    )


def goal_result_to_out(gr: GoalResult) -> GoalResultOut:
    return GoalResultOut(
        goal_id=gr.goal_id,
        name=gr.name,
        target_amount=gr.target_amount,
        already_saved=gr.already_saved,
        remaining_amount=gr.remaining_amount,
        baseline_monthly_surplus=gr.baseline_monthly_surplus,
        extra_savings_per_month=gr.extra_savings_per_month,
        months_to_reach=gr.months_to_reach,
        reach_date=gr.reach_date,
        required_monthly_for_target_date=gr.required_monthly_for_target_date,
        target_date=gr.target_date,
        status=gr.status,
    )


def savings_suggestion_to_out(s: SavingsSuggestion) -> SavingsSuggestionOut:
    return SavingsSuggestionOut(
        category=s.category,
        label=s.label,
        current_avg_monthly=s.current_avg_monthly,
        suggested_cut=s.suggested_cut,
        new_avg_monthly=s.new_avg_monthly,
    )
