"""Persona definitions for the synthetic bank customers.

LOTTE is the only persona shown in the UI (single customer POV). OTHER_CUSTOMER
exists purely so the security tests/demo script can prove that one customer's
session can never read another customer's data — it is never reachable through
the normal login flow.

To swap in a real persona later, edit LOTTE below; nothing else references
persona fields directly.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    customer_id: str
    name: str
    age: int
    job_title: str
    city: str
    net_monthly_salary: float
    rent_amount: float
    starting_balance: float
    seed: int


LOTTE = Persona(
    customer_id="cust_lotte",
    name="Lotte",
    age=23,
    job_title="Junior Marketeer",
    city="Gent",
    net_monthly_salary=1900.0,
    rent_amount=700.0,
    starting_balance=850.0,
    seed=42,
)

# Hidden persona: only reachable via the DEMO_MODE-gated /api/dev/login-as
# endpoint, used to demonstrate cross-customer isolation.
OTHER_CUSTOMER = Persona(
    customer_id="cust_other_demo",
    name="Karel (demo-only)",
    age=41,
    job_title="Accountant",
    city="Antwerpen",
    net_monthly_salary=2600.0,
    rent_amount=0.0,
    starting_balance=3000.0,
    seed=99,
)

PERSONAS: dict[str, Persona] = {p.customer_id: p for p in (LOTTE, OTHER_CUSTOMER)}

ACTIVE_UI_PERSONA_ID = LOTTE.customer_id
