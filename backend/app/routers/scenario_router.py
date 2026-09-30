from fastapi import APIRouter, Depends

from app.analytics.forecasting import forecast_balance
from app.analytics.scenario import apply_scenario
from app.auth.session import get_current_customer_id
from app.data.store import store
from app.models.schemas import ScenarioRequest, ScenarioResponse
from app.serialization import forecast_to_out

router = APIRouter(tags=["scenario"])


@router.post("/scenario", response_model=ScenarioResponse)
def post_scenario(
    body: ScenarioRequest,
    customer_id: str = Depends(get_current_customer_id),
) -> ScenarioResponse:
    record = store.get(customer_id)
    baseline = forecast_balance(record.forecast_inputs, record.persona.starting_balance)
    scenario = apply_scenario(
        record.forecast_inputs,
        record.persona.starting_balance,
        body.extra_savings_per_month,
    )
    return ScenarioResponse(
        extra_savings_per_month=body.extra_savings_per_month,
        baseline=forecast_to_out(baseline),
        scenario=forecast_to_out(scenario),
    )
