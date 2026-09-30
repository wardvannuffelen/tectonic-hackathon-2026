from dataclasses import dataclass
from datetime import date
from typing import Literal

GoalStatus = Literal["already_reached", "on_track", "needs_more", "unreachable"]


@dataclass(frozen=True)
class Goal:
    id: str
    customer_id: str
    name: str
    target_amount: float
    already_saved: float = 0.0
    target_date: date | None = None


@dataclass(frozen=True)
class GoalResult:
    goal_id: str
    name: str
    target_amount: float
    already_saved: float
    remaining_amount: float
    baseline_monthly_surplus: float
    extra_savings_per_month: float
    months_to_reach: int | None
    reach_date: date | None
    required_monthly_for_target_date: float | None
    target_date: date | None
    status: GoalStatus
