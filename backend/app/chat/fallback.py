"""Regex-based fallback chat: used whenever no ANTHROPIC_API_KEY is configured,
or the Claude call fails. Calls the exact same TOOL_DISPATCH functions as the
LLM path, so both modes are backed by identical logic — only the phrasing of
the reply differs.
"""
import re

from app.chat.tools import TOOL_DISPATCH
from app.data.store import store

_AMOUNT_RE = r"(\d+(?:[.,]\d+)?)"

_SCENARIO_RE = re.compile(rf"wat als ik.*?{_AMOUNT_RE}\s*euro", re.I)
_GOAL_RE = re.compile(r"wanneer|doel|huurwaarborg|laptop", re.I)
_SAVINGS_RE = re.compile(r"besparen|besparing|waar.*vandaan|bronnen", re.I)
_FORECAST_RE = re.compile(r"saldo|voorspelling|forecast|balans", re.I)


def fallback_reply(customer_id: str, message: str) -> tuple[str, list[str]]:
    scenario_match = _SCENARIO_RE.search(message)
    if scenario_match:
        return _handle_scenario(customer_id, float(scenario_match.group(1).replace(",", ".")))

    if _GOAL_RE.search(message):
        return _handle_goals(customer_id, message)

    if _SAVINGS_RE.search(message):
        amount_match = re.search(_AMOUNT_RE, message)
        target = float(amount_match.group(1).replace(",", ".")) if amount_match else 200.0
        return _handle_savings_sources(customer_id, target)

    if _FORECAST_RE.search(message):
        return _handle_forecast(customer_id)

    return (
        "Ik kon je vraag niet automatisch herkennen (demo-modus zonder AI-verbinding). "
        "Probeer bijvoorbeeld: 'Wat als ik 200 euro extra spaar per maand?', "
        "'Wanneer haal ik mijn huurwaarborg-doel?', of 'Waar kan ik besparen?'",
        [],
    )


def _handle_scenario(customer_id: str, amount: float) -> tuple[str, list[str]]:
    result = TOOL_DISPATCH["apply_scenario"](customer_id, extra_savings_per_month=amount)
    ending = result["ending_balance"]
    return (
        f"Als je elke maand {amount:.0f} euro extra opzij zet, kom je over 12 maanden "
        f"uit op een geschat saldo van ongeveer {ending:.0f} euro (in plaats van je "
        f"huidige verwachte verloop). Bekijk de grafiek voor het volledige verloop.",
        ["apply_scenario"],
    )


def _handle_goals(customer_id: str, message: str) -> tuple[str, list[str]]:
    record = store.get(customer_id)
    matched = next((g for g in record.goals if g.name.lower() in message.lower()), None)
    if matched:
        result = TOOL_DISPATCH["simulate_goal"](
            customer_id, goal_name=matched.name, extra_savings_per_month=0.0,
        )
        if result.get("months_to_reach") is not None:
            return (
                f"Aan je huidige spaartempo haal je '{result['name']}' "
                f"(nog {result['remaining_amount']:.0f} euro nodig) over "
                f"ongeveer {result['months_to_reach']} maanden, rond {result['reach_date']}.",
                ["simulate_goal"],
            )
        return (
            f"Met je huidige spaartempo haal je '{result['name']}' voorlopig niet — "
            "probeer de schuif 'extra sparen' te gebruiken om te zien wat er nodig is.",
            ["simulate_goal"],
        )

    result = TOOL_DISPATCH["get_goals"](customer_id)
    if not result["goals"]:
        return "Je hebt momenteel geen doelen ingesteld.", ["get_goals"]
    lines = [
        f"- {g['name']}: nog {g['remaining_amount']:.0f} euro nodig"
        + (f", over ~{g['months_to_reach']} maanden" if g["months_to_reach"] is not None else "")
        for g in result["goals"]
    ]
    return "Je doelen:\n" + "\n".join(lines), ["get_goals"]


def _handle_savings_sources(customer_id: str, target: float) -> tuple[str, list[str]]:
    result = TOOL_DISPATCH["get_savings_sources"](customer_id, target_extra_savings=target)
    if not result["suggestions"]:
        return "Ik vond geen duidelijke besparingsbronnen in je uitgavenpatroon.", ["get_savings_sources"]
    lines = [
        f"- {s['label']}: nu gemiddeld {s['current_avg_monthly']:.0f} euro/maand, "
        f"bespaar {s['suggested_cut']:.0f} euro/maand"
        for s in result["suggestions"]
    ]
    intro = f"Om {target:.0f} euro per maand extra te sparen, kan je kijken naar:"
    if result["shortfall"] > 0:
        intro += f" (dit dekt {target - result['shortfall']:.0f} van de {target:.0f} euro)"
    return intro + "\n" + "\n".join(lines), ["get_savings_sources"]


def _handle_forecast(customer_id: str) -> tuple[str, list[str]]:
    result = TOOL_DISPATCH["get_forecast"](customer_id)
    last = result["months"][-1]
    return (
        f"Op basis van je huidige patroon verwachten we over 12 maanden een saldo van "
        f"ongeveer {last['balance']:.0f} euro (tussen {last['balance_low']:.0f} en "
        f"{last['balance_high']:.0f} euro).",
        ["get_forecast"],
    )
