"""Where could the requested extra monthly savings realistically come from?

Greedy allocation over discretionary spending categories, ranked by realistic
savings potential (average monthly spend * a category-specific max-cut
fraction — essentials like groceries/transport are capped low, "wants" like
eating out are capped high). Pure code, no LLM.
"""
from dataclasses import dataclass

from app.models.transaction import Transaction

CATEGORY_POLICY: dict[str, dict] = {
    "eating_out": {"max_cut_fraction": 0.60, "label": "Uit eten & delivery"},
    "subscription": {"max_cut_fraction": 0.50, "label": "Abonnementen"},
    "vacation": {"max_cut_fraction": 0.30, "label": "Reizen & uitstappen"},
    "irregular": {"max_cut_fraction": 0.40, "label": "Overige/impulsuitgaven"},
    "groceries": {"max_cut_fraction": 0.15, "label": "Boodschappen"},
    "transport": {"max_cut_fraction": 0.10, "label": "Transport"},
}

MONTHS_OF_HISTORY = 12


@dataclass(frozen=True)
class SavingsSuggestion:
    category: str
    label: str
    current_avg_monthly: float
    suggested_cut: float
    new_avg_monthly: float


def suggest_savings(
    transactions: list[Transaction],
    target_extra_savings: float,
) -> tuple[list[SavingsSuggestion], float]:
    """Returns (suggestions, shortfall). shortfall > 0 means the target could
    not be fully covered by realistic cuts to discretionary spending."""
    monthly_avg: dict[str, float] = {}
    for category in CATEGORY_POLICY:
        total = sum(-t.amount for t in transactions if t.category == category)
        monthly_avg[category] = total / MONTHS_OF_HISTORY

    def potential(category: str) -> float:
        return monthly_avg[category] * CATEGORY_POLICY[category]["max_cut_fraction"]

    ranked = sorted(CATEGORY_POLICY, key=potential, reverse=True)

    remaining = target_extra_savings
    suggestions: list[SavingsSuggestion] = []
    for category in ranked:
        if remaining <= 0:
            break
        cap = potential(category)
        cut = min(cap, remaining)
        if cut <= 0:
            continue
        suggestions.append(SavingsSuggestion(
            category=category,
            label=CATEGORY_POLICY[category]["label"],
            current_avg_monthly=round(monthly_avg[category], 2),
            suggested_cut=round(cut, 2),
            new_avg_monthly=round(monthly_avg[category] - cut, 2),
        ))
        remaining -= cut

    return suggestions, round(max(remaining, 0.0), 2)
