"""In-memory per-customer data store, built once at process startup.

Deliberately not persisted: a restart regenerates identical (seeded) data, so
there is no risk of stale fixtures drifting from the generator's schema.
"""
from dataclasses import dataclass, field

from app.analytics.forecasting import ForecastInputs, build_forecast_inputs
from app.data.generator import generate_transactions
from app.models.goal import Goal
from app.models.persona import PERSONAS, Persona
from app.models.transaction import Transaction


@dataclass
class CustomerRecord:
    persona: Persona
    transactions: list[Transaction]
    forecast_inputs: ForecastInputs
    goals: list[Goal] = field(default_factory=list)


class CustomerStore:
    def __init__(self) -> None:
        self._customers: dict[str, CustomerRecord] = {}

    def build(self) -> None:
        for persona in PERSONAS.values():
            transactions = generate_transactions(persona)
            forecast_inputs = build_forecast_inputs(transactions)
            goals = _seed_goals(persona)
            self._customers[persona.customer_id] = CustomerRecord(
                persona=persona,
                transactions=transactions,
                forecast_inputs=forecast_inputs,
                goals=goals,
            )

    def get(self, customer_id: str) -> CustomerRecord:
        record = self._customers.get(customer_id)
        if record is None:
            raise KeyError(f"Unknown customer_id: {customer_id}")
        return record

    def find_goal(self, goal_id: str) -> Goal | None:
        for record in self._customers.values():
            for goal in record.goals:
                if goal.id == goal_id:
                    return goal
        return None


def _seed_goals(persona: Persona) -> list[Goal]:
    if persona.customer_id != "cust_lotte":
        return []
    return [
        Goal(
            id="goal_huurwaarborg",
            customer_id=persona.customer_id,
            name="Huurwaarborg",
            target_amount=2500.0,
            already_saved=300.0,
        ),
        Goal(
            id="goal_laptop",
            customer_id=persona.customer_id,
            name="Nieuwe laptop",
            target_amount=1000.0,
            already_saved=0.0,
        ),
    ]


# Single process-wide instance, populated by main.py's startup event.
store = CustomerStore()
