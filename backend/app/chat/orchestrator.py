import logging

from app.chat.claude_client import call_claude_with_tools
from app.chat.fallback import fallback_reply
from app.config import ANTHROPIC_API_KEY
from app.models.schemas import ChatMessageIn, ChatResponse

logger = logging.getLogger(__name__)


def handle_chat(customer_id: str, message: str, history: list[ChatMessageIn]) -> ChatResponse:
    if ANTHROPIC_API_KEY:
        try:
            history_dicts = [{"role": h.role, "content": h.content} for h in history]
            text, used_tools = call_claude_with_tools(customer_id, message, history_dicts)
            return ChatResponse(reply=text, used_tools=used_tools, mode="llm")
        except Exception:
            logger.exception("Claude-aanroep mislukt, val terug op regelgebaseerde chat")

    text, used_tools = fallback_reply(customer_id, message)
    return ChatResponse(reply=text, used_tools=used_tools, mode="fallback")
