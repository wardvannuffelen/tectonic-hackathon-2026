"""Tool schemas exposed to Claude, and their server-side dispatch.

Security-critical property: none of these schemas has a customer_id field, so
the model can never supply one. Every dispatch function below takes
customer_id as a separate, server-injected argument (see claude_client.py and
fallback.py) — never something read from the model's tool input.
"""
from app.analytics.forecasting import forecast_balance
from app.analytics.goals import compute_goal_progress
from app.analytics.savings_sources import suggest_savings
from app.data.store import store

TOOLS = [
    {
        "name": "get_forecast",
        "description": (
            "Get the customer's baseline 12-month account balance forecast, "
            "based on their historical transactions."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "apply_scenario",
        "description": (
            "Recompute the 12-month balance forecast assuming the customer saves "
            "an extra fixed amount per month starting now."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "extra_savings_per_month": {
                    "type": "number", "minimum": 0,
                    "description": "Extra amount saved per month, in euros.",
                },
            },
            "required": ["extra_savings_per_month"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_goals",
        "description": "List the customer's savings goals and their current progress.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "simulate_goal",
        "description": (
            "Compute how many months it takes to reach a named savings goal, given "
            "extra monthly savings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_name": {
                    "type": "string",
                    "description": "The goal's name, e.g. 'Huurwaarborg'.",
                },
                "extra_savings_per_month": {"type": "number", "minimum": 0},
            },
            "required": ["goal_name", "extra_savings_per_month"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_savings_sources",
        "description": (
            "Suggest which spending categories the customer could realistically cut "
            "to reach a target extra amount of monthly savings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_extra_savings": {"type": "number", "minimum": 0},
            },
            "required": ["target_extra_savings"],
            "additionalProperties": False,
        },
    },
]


def _tool_get_forecast(customer_id: str) -> dict:
    record = store.get(customer_id)
    result = forecast_balance(record.forecast_inputs, record.persona.starting_balance)
    return {
        "starting_balance": result.starting_balance,
        "months": [
            {"month_index": m.month_index, "balance": m.balance,
             "balance_low": m.balance_low, "balance_high": m.balance_high}
            for m in result.months
        ],
    }


def _tool_apply_scenario(customer_id: str, extra_savings_per_month: float) -> dict:
    record = store.get(customer_id)
    result = forecast_balance(
        record.forecast_inputs, record.persona.starting_balance,
        extra_monthly_delta=extra_savings_per_month,
    )
    return {
        "extra_savings_per_month": extra_savings_per_month,
        "ending_balance": result.months[-1].balance if result.months else record.persona.starting_balance,
        "months": [{"month_index": m.month_index, "balance": m.balance} for m in result.months],
    }


def _tool_get_goals(customer_id: str) -> dict:
    record = store.get(customer_id)
    forecast = forecast_balance(record.forecast_inputs, record.persona.starting_balance)
    goals = []
    for goal in record.goals:
        gr = compute_goal_progress(goal, forecast)
        goals.append({
            "name": gr.name, "target_amount": gr.target_amount,
            "already_saved": gr.already_saved, "remaining_amount": gr.remaining_amount,
            "months_to_reach": gr.months_to_reach, "reach_date": str(gr.reach_date) if gr.reach_date else None,
            "status": gr.status,
        })
    return {"goals": goals}


def _tool_simulate_goal(customer_id: str, goal_name: str, extra_savings_per_month: float) -> dict:
    record = store.get(customer_id)
    goal = next((g for g in record.goals if g.name.lower() == goal_name.lower()), None)
    if goal is None:
        return {"error": f"Onbekend doel: {goal_name}", "known_goals": [g.name for g in record.goals]}
    forecast = forecast_balance(record.forecast_inputs, record.persona.starting_balance)
    gr = compute_goal_progress(goal, forecast, extra_savings_per_month)
    return {
        "name": gr.name, "remaining_amount": gr.remaining_amount,
        "extra_savings_per_month": extra_savings_per_month,
        "months_to_reach": gr.months_to_reach,
        "reach_date": str(gr.reach_date) if gr.reach_date else None,
        "status": gr.status,
    }


def _tool_get_savings_sources(customer_id: str, target_extra_savings: float) -> dict:
    record = store.get(customer_id)
    suggestions, shortfall = suggest_savings(record.transactions, target_extra_savings)
    return {
        "target_extra_savings": target_extra_savings,
        "shortfall": shortfall,
        "suggestions": [
            {"label": s.label, "current_avg_monthly": s.current_avg_monthly,
             "suggested_cut": s.suggested_cut, "new_avg_monthly": s.new_avg_monthly}
            for s in suggestions
        ],
    }


TOOL_DISPATCH = {
    "get_forecast": _tool_get_forecast,
    "apply_scenario": _tool_apply_scenario,
    "get_goals": _tool_get_goals,
    "simulate_goal": _tool_simulate_goal,
    "get_savings_sources": _tool_get_savings_sources,
}
