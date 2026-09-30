from fastapi import APIRouter, Depends, Query

from app.analytics.forecasting import forecast_balance
from app.auth.session import get_current_customer_id
from app.data.store import store
from app.models.schemas import ForecastResponse
from app.serialization import forecast_to_out

router = APIRouter(tags=["forecast"])


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    extra_savings_per_month: float = Query(default=0.0, ge=0, le=5000),
    customer_id: str = Depends(get_current_customer_id),
) -> ForecastResponse:
    record = store.get(customer_id)
    result = forecast_balance(
        record.forecast_inputs,
        record.persona.starting_balance,
        extra_monthly_delta=extra_savings_per_month,
    )
    return forecast_to_out(result)
