from fastapi import APIRouter, Depends, Query

from app.analytics.savings_sources import suggest_savings
from app.auth.session import get_current_customer_id
from app.data.store import store
from app.models.schemas import SavingsSourcesResponse
from app.serialization import savings_suggestion_to_out

router = APIRouter(tags=["savings-sources"])


@router.get("/savings-sources", response_model=SavingsSourcesResponse)
def get_savings_sources(
    target: float = Query(default=200.0, ge=0, le=5000),
    customer_id: str = Depends(get_current_customer_id),
) -> SavingsSourcesResponse:
    record = store.get(customer_id)
    suggestions, shortfall = suggest_savings(record.transactions, target)
    total_covered = round(target - shortfall, 2)
    return SavingsSourcesResponse(
        target_extra_savings=target,
        suggestions=[savings_suggestion_to_out(s) for s in suggestions],
        total_covered=total_covered,
        shortfall=shortfall,
    )
