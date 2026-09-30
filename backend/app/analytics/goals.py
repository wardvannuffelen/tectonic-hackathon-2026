"""Goal calculator: when is a savings goal reached, and how much per month is
needed? Pure code, no LLM.
"""
import math
import statistics
from datetime import date

from app.dateutils import add_months, month_diff
from app.models.forecast import ForecastResult
from app.models.goal import Goal, GoalResult


def compute_goal_progress(
    goal: Goal,
    forecast: ForecastResult,
    extra_savings_per_month: float = 0.0,
    today: date | None = None,
) -> GoalResult:
    today = today or date.today()
    remaining = round(max(goal.target_amount - goal.already_saved, 0.0), 2)
    baseline_surplus = statistics.mean(m.net_cashflow for m in forecast.months)
    effective = baseline_surplus + extra_savings_per_month

    if remaining <= 0:
        return GoalResult(
            goal_id=goal.id, name=goal.name, target_amount=goal.target_amount,
            already_saved=goal.already_saved, remaining_amount=0.0,
            baseline_monthly_surplus=round(baseline_surplus, 2),
            extra_savings_per_month=extra_savings_per_month,
            months_to_reach=0, reach_date=today,
            required_monthly_for_target_date=None, target_date=goal.target_date,
            status="already_reached",
        )

    if effective <= 0:
        months_to_reach, reach_date, status = None, None, "unreachable"
    else:
        months_to_reach = math.ceil(remaining / effective)
        reach_date = add_months(today, months_to_reach)
        status = "on_track"

    required_for_target_date = None
    if goal.target_date is not None:
        months_available = month_diff(today, goal.target_date)
        if months_available > 0:
            required_for_target_date = round(remaining / months_available, 2)
            if status == "on_track" and months_to_reach is not None:
                status = "on_track" if months_to_reach <= months_available else "needs_more"
            else:
                status = "needs_more"
        # A target date already in the past leaves required_for_target_date
        # unset; months_to_reach/status from above still stand.

    return GoalResult(
        goal_id=goal.id,
        name=goal.name,
        target_amount=goal.target_amount,
        already_saved=goal.already_saved,
        remaining_amount=remaining,
        baseline_monthly_surplus=round(baseline_surplus, 2),
        extra_savings_per_month=extra_savings_per_month,
        months_to_reach=months_to_reach,
        reach_date=reach_date,
        required_monthly_for_target_date=required_for_target_date,
        target_date=goal.target_date,
        status=status,
    )
