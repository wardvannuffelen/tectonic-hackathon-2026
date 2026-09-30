from dataclasses import dataclass
from datetime import date
from typing import Literal

Category = Literal[
    "salary",
    "rent",
    "subscription",
    "insurance",
    "annual_bill",
    "groceries",
    "eating_out",
    "transport",
    "vacation",
    "irregular",
]


@dataclass(frozen=True)
class Transaction:
    id: str
    customer_id: str
    date: date
    amount: float  # signed: positive = income, negative = expense
    category: Category
    description: str
