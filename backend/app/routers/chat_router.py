from fastapi import APIRouter, Depends

from app.auth.session import get_current_customer_id
from app.chat.orchestrator import handle_chat
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    customer_id: str = Depends(get_current_customer_id),
) -> ChatResponse:
    return handle_chat(customer_id, body.message, body.history)
