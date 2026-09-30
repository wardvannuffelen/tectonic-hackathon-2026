"""Detect recurring vs. one-off transactions by grouping on (category,
description) and checking how stable the amount and the gap between
occurrences are. Pure stdlib statistics, no ML.
"""
import statistics
from dataclasses import dataclass
from typing import Literal

from app.models.transaction import Transaction

RecurringKind = Literal["fixed", "variable_recurring", "one_off"]


@dataclass(frozen=True)
class RecurringPattern:
    key: str
    category: str
    description: str
    avg_amount: float
    stdev_amount: float
    frequency_days: float
    count: int
    kind: RecurringKind


def detect_recurring(transactions: list[Transaction]) -> list[RecurringPattern]:
    groups: dict[tuple[str, str], list[Transaction]] = {}
    for tx in transactions:
        groups.setdefault((tx.category, tx.description), []).append(tx)

    patterns: list[RecurringPattern] = []
    for (category, description), group in groups.items():
        group.sort(key=lambda t: t.date)
        amounts = [t.amount for t in group]
        avg_amount = statistics.mean(amounts)
        stdev_amount = statistics.pstdev(amounts) if len(amounts) > 1 else 0.0
        cv_amount = abs(stdev_amount / avg_amount) if avg_amount else float("inf")

        if len(group) < 2:
            kind: RecurringKind = "one_off"
            freq_days = 0.0
        else:
            gaps = [(b.date - a.date).days for a, b in zip(group, group[1:])]
            freq_days = statistics.mean(gaps)
            stdev_gap = statistics.pstdev(gaps) if len(gaps) > 1 else 0.0

            if len(group) >= 3 and stdev_gap <= 5 and cv_amount <= 0.10:
                kind = "fixed"
            elif len(group) >= 3 and stdev_gap <= 10 and cv_amount <= 0.30:
                kind = "variable_recurring"
            else:
                kind = "one_off"

        patterns.append(RecurringPattern(
            key=f"{category}:{description}",
            category=category,
            description=description,
            avg_amount=avg_amount,
            stdev_amount=stdev_amount,
            frequency_days=freq_days,
            count=len(group),
            kind=kind,
        ))
    return patterns
