"""Per-category seasonal index from one year of history.

seasonal_index[category][calendar_month] = that month's total / the category's
average monthly total. With only 12 months of history this is a single sample
per calendar month, not a true multi-year decomposition — good enough for a
POC, but it means a category like "vacation" shows up as a sharp spike in
exactly the month it historically occurred rather than a smoothed curve.
"""
from app.models.transaction import Transaction


def seasonal_index(transactions: list[Transaction]) -> dict[str, dict[int, float]]:
    categories = {t.category for t in transactions}
    index: dict[str, dict[int, float]] = {}

    for category in categories:
        monthly_total: dict[int, float] = {m: 0.0 for m in range(1, 13)}
        for t in transactions:
            if t.category == category:
                monthly_total[t.date.month] += t.amount

        avg = sum(monthly_total.values()) / 12
        index[category] = {
            month: (total / avg) if avg else 1.0
            for month, total in monthly_total.items()
        }

    return index
