from fastapi import APIRouter, Depends, Query

from app.analytics.forecasting import forecast_balance
from app.analytics.goals import compute_goal_progress
from app.auth.session import get_current_customer_id, get_owned_goal
from app.data.store import store
from app.models.schemas import GoalResultOut, GoalSimulateRequest, GoalsResponse
from app.serialization import goal_result_to_out

router = APIRouter(tags=["goals"])


@router.get("/goals", response_model=GoalsResponse)
def get_goals(
    extra_savings_per_month: float = Query(default=0.0, ge=0, le=5000),
    customer_id: str = Depends(get_current_customer_id),
) -> GoalsResponse:
    record = store.get(customer_id)
    forecast = forecast_balance(record.forecast_inputs, record.persona.starting_balance)
    results = [
        goal_result_to_out(compute_goal_progress(goal, forecast, extra_savings_per_month))
        for goal in record.goals
    ]
    return GoalsResponse(goals=results)


@router.post("/goals/{goal_id}/simulate", response_model=GoalResultOut)
def simulate_goal(
    goal_id: str,
    body: GoalSimulateRequest,
    customer_id: str = Depends(get_current_customer_id),
) -> GoalResultOut:
    goal = get_owned_goal(goal_id, customer_id)
    record = store.get(customer_id)
    forecast = forecast_balance(record.forecast_inputs, record.persona.starting_balance)
    result = compute_goal_progress(goal, forecast, body.extra_savings_per_month)
    return goal_result_to_out(result)
