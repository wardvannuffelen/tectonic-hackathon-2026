from fastapi import APIRouter, Depends

from app.auth.session import get_current_customer_id
from app.data.store import store
from app.models.schemas import TransactionOut, TransactionsResponse

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=TransactionsResponse)
def get_transactions(customer_id: str = Depends(get_current_customer_id)) -> TransactionsResponse:
    record = store.get(customer_id)
    return TransactionsResponse(
        customer_id=customer_id,
        transactions=[
            TransactionOut(
                id=t.id, date=t.date, amount=t.amount,
                category=t.category, description=t.description,
            )
            for t in record.transactions
        ],
    )
