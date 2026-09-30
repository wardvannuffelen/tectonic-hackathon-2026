"""Proves the core security requirement (build step 8): a customer's session
can never read another customer's data, and a client can never impersonate a
customer_id — it is always resolved server-side from the session token.
"""
import os

os.environ["DEMO_MODE"] = "true"  # must be set before app.config is imported

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_login_always_returns_lotte():
    with TestClient(app) as client:
        response = client.post("/api/login")
        assert response.status_code == 200
        assert response.json()["customer_id"] == "cust_lotte"


def test_no_token_is_rejected():
    with TestClient(app) as client:
        response = client.get("/api/transactions")
        assert response.status_code == 401


def test_garbage_token_is_rejected():
    with TestClient(app) as client:
        response = client.get(
            "/api/transactions", headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401


def test_two_customers_see_different_transactions():
    with TestClient(app) as client:
        token_lotte = client.post("/api/login").json()["session_token"]
        token_other = client.post(
            "/api/dev/login-as", json={"customer_id": "cust_other_demo"},
        ).json()["session_token"]

        tx_lotte = client.get(
            "/api/transactions", headers={"Authorization": f"Bearer {token_lotte}"},
        ).json()
        tx_other = client.get(
            "/api/transactions", headers={"Authorization": f"Bearer {token_other}"},
        ).json()

        assert tx_lotte["customer_id"] == "cust_lotte"
        assert tx_other["customer_id"] == "cust_other_demo"
        assert tx_lotte["transactions"] != tx_other["transactions"]


def test_customer_cannot_read_another_customers_goal_by_id():
    """The IDOR case: Lotte knows (or guesses) another customer's goal id and
    tries to fetch/simulate it directly — must be refused with 403, not 404
    or a silent cross-customer read."""
    with TestClient(app) as client:
        token_lotte = client.post("/api/login").json()["session_token"]

        # cust_other_demo has no seeded goals, so use one of Lotte's own goal
        # ids while authenticated as a *different* (hidden) customer instead —
        # equally valid proof that ownership, not just existence, is checked.
        token_other = client.post(
            "/api/dev/login-as", json={"customer_id": "cust_other_demo"},
        ).json()["session_token"]

        response = client.post(
            "/api/goals/goal_huurwaarborg/simulate",
            json={"extra_savings_per_month": 0.0},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert response.status_code == 403

        # Lotte herself can reach her own goal.
        own = client.post(
            "/api/goals/goal_huurwaarborg/simulate",
            json={"extra_savings_per_month": 0.0},
            headers={"Authorization": f"Bearer {token_lotte}"},
        )
        assert own.status_code == 200


def test_dev_login_backdoor_disabled_outside_demo_mode(monkeypatch):
    import app.routers.auth_router as auth_router

    monkeypatch.setattr(auth_router, "DEMO_MODE", False)
    with TestClient(app) as client:
        response = client.post("/api/dev/login-as", json={"customer_id": "cust_other_demo"})
        assert response.status_code == 404


def test_chat_tool_schemas_never_expose_customer_id():
    from app.chat.tools import TOOLS

    for tool in TOOLS:
        assert "customer_id" not in tool["input_schema"].get("properties", {})
