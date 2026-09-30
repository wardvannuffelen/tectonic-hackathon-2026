"""In-memory session store: one Bearer token maps to exactly one customer_id.

Every protected route resolves customer_id through get_current_customer_id()
from the request's own token — never from a body or query parameter supplied
by the client. This is the mechanism that guarantees a customer can never
fetch another customer's data, and it applies identically to the chat tool
layer (see chat/tools.py: tool schemas never carry a customer_id field).
"""
import secrets

from fastapi import Header, HTTPException

from app.data.store import store
from app.models.goal import Goal

# token -> customer_id. Cleared on every restart by design (no persistence).
SESSIONS: dict[str, str] = {}


def create_session(customer_id: str) -> str:
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = customer_id
    return token


def get_current_customer_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Ontbrekende Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Ongeldig Authorization-formaat")

    customer_id = SESSIONS.get(token)
    if customer_id is None:
        raise HTTPException(status_code=401, detail="Ongeldige of verlopen sessie")

    return customer_id


def get_owned_goal(goal_id: str, customer_id: str) -> Goal:
    """Look up a goal and enforce that it belongs to the requesting customer."""
    goal = store.find_goal(goal_id)
    if goal is None or goal.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Geen toegang tot dit doel")
    return goal
