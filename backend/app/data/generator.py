"""Synthetic transaction generator. Fully fictional data, seeded for
reproducibility. No real bank data is used or referenced anywhere.
"""
import random
from datetime import date, timedelta

from app.dateutils import add_months, first_of_month
from app.models.persona import Persona
from app.models.transaction import Transaction

MONTHS_OF_HISTORY = 12

SUBSCRIPTIONS = [
    ("Netflix", 13.99, 15),
    ("Spotify", 9.99, 3),
    ("Fitnessclub", 29.99, 5),
    ("Telefoonabonnement", 20.0, 8),
]

GROCERY_STORES = ["Colruyt", "Delhaize", "Aldi", "Lidl", "Carrefour"]
EATERIES = ["Uber Eats", "Broodjeszaak", "Pizzeria", "Restaurant", "Frituur", "Kebab"]


def _tx_id(counter: list[int]) -> str:
    counter[0] += 1
    return f"tx_{counter[0]:05d}"


def generate_transactions(persona: Persona, months: int = MONTHS_OF_HISTORY) -> list[Transaction]:
    rng = random.Random(persona.seed)
    counter = [0]
    txs: list[Transaction] = []

    end_month = first_of_month(date.today())
    start_month = add_months(end_month, -(months - 1))
    month_starts = [add_months(start_month, i) for i in range(months)]

    for m in month_starts:
        cal_month = m.month

        # --- Salary: fixed day, tiny jitter ---
        salary_day = min(25 + rng.choice([-1, 0, 0, 1]), 28)
        txs.append(Transaction(
            _tx_id(counter), persona.customer_id, m.replace(day=salary_day),
            round(persona.net_monthly_salary, 2), "salary", "Loon",
        ))

        # --- Rent: fixed day 1 ---
        txs.append(Transaction(
            _tx_id(counter), persona.customer_id, m.replace(day=1),
            -round(persona.rent_amount, 2), "rent", "Huur appartement",
        ))

        # --- Subscriptions: fixed day, fixed amount (phone has occasional overage) ---
        for name, amount, day in SUBSCRIPTIONS:
            amt = amount
            if name == "Telefoonabonnement" and rng.random() < 0.25:
                amt += rng.uniform(3, 12)  # occasional data overage
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=min(day, 28)),
                -round(amt, 2), "subscription", name,
            ))

        # --- Health insurance: fixed monthly ---
        txs.append(Transaction(
            _tx_id(counter), persona.customer_id, m.replace(day=7),
            -45.0, "insurance", "Hospitalisatieverzekering",
        ))

        # --- Annual home/renters insurance: one lump sum in October ---
        if cal_month == 10:
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=14),
                -320.0, "insurance", "Woonverzekering (jaarlijks)",
            ))

        # --- Annual bill: e.g. yearly public transport top-up, in March ---
        if cal_month == 3:
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=20),
                -220.0, "annual_bill", "Jaarlijkse belastingafrekening",
            ))

        # --- Transport: monthly pass + ad-hoc tickets ---
        txs.append(Transaction(
            _tx_id(counter), persona.customer_id, m.replace(day=2),
            -49.0, "transport", "Buspas maandabonnement",
        ))
        for _ in range(rng.randint(0, 3)):
            day = rng.randint(3, 28)
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=day),
                -round(rng.uniform(8, 20), 2), "transport", "Treinticket",
            ))

        # --- Vacations: seasonal bursts ---
        if cal_month == 7:
            for _ in range(rng.randint(3, 5)):
                day = rng.randint(1, 28)
                txs.append(Transaction(
                    _tx_id(counter), persona.customer_id, m.replace(day=day),
                    -round(rng.uniform(90, 180), 2), "vacation", "Zomervakantie",
                ))
        if cal_month in (2, 11) and rng.random() < 0.9:
            for _ in range(rng.randint(2, 3)):
                day = rng.randint(1, 28)
                txs.append(Transaction(
                    _tx_id(counter), persona.customer_id, m.replace(day=day),
                    -round(rng.uniform(50, 100), 2), "vacation", "Stedentrip",
                ))

        # --- Groceries: ~4-5x/month ---
        for _ in range(rng.randint(4, 5)):
            day = rng.randint(1, 28)
            store = rng.choice(GROCERY_STORES)
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=day),
                -round(rng.uniform(25, 70), 2), "groceries", store,
            ))

        # --- Eating out: weekend-skewed frequency ---
        for _ in range(rng.randint(4, 10)):
            day = _weekend_skewed_day(rng, m)
            place = rng.choice(EATERIES)
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, day,
                -round(rng.uniform(8, 45), 2), "eating_out", place,
            ))

        # --- Irregular expenses: a couple of times a year ---
        if rng.random() < 0.3:
            day = rng.randint(1, 28)
            label, amt = rng.choice([
                ("Fietsherstelling", rng.uniform(50, 120)),
                ("Verjaardagscadeau", rng.uniform(20, 60)),
                ("Kledingaankoop", rng.uniform(40, 150)),
                ("Elektronicaherstelling", rng.uniform(60, 200)),
            ])
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=day),
                -round(amt, 2), "irregular", label,
            ))

        # --- One-off irregular income (e.g. tax refund), tests that the
        # forecaster does not treat it as a recurring baseline ---
        if cal_month == 4:
            txs.append(Transaction(
                _tx_id(counter), persona.customer_id, m.replace(day=18),
                150.0, "irregular", "Belastingteruggave",
            ))

    txs.sort(key=lambda t: t.date)
    return txs


def _weekend_skewed_day(rng: random.Random, month_start: date) -> date:
    """Pick a random day in the month, weighted 3x toward Fri/Sat/Sun."""
    next_month = add_months(month_start, 1)
    days_in_month = (next_month - month_start).days
    candidates = [month_start + timedelta(days=i) for i in range(days_in_month)]
    weights = [3 if d.weekday() in (4, 5, 6) else 1 for d in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]
