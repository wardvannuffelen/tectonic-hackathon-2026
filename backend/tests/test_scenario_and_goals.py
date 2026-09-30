from datetime import date

from app.analytics.forecasting import build_forecast_inputs, forecast_balance
from app.analytics.goals import compute_goal_progress
from app.analytics.savings_sources import suggest_savings
from app.analytics.scenario import apply_scenario
from app.data.generator import generate_transactions
from app.models.goal import Goal
from app.models.persona import LOTTE


def _forecast():
    txs = generate_transactions(LOTTE)
    inputs = build_forecast_inputs(txs)
    return txs, inputs, forecast_balance(inputs, LOTTE.starting_balance)


def test_scenario_shifts_balance_by_exact_cumulative_extra_savings():
    _, inputs, baseline = _forecast()
    scenario = apply_scenario(inputs, LOTTE.starting_balance, extra_savings_per_month=200.0)

    for m in range(12):
        expected_shift = 200.0 * (m + 1)
        actual_shift = scenario.months[m].balance - baseline.months[m].balance
        assert abs(actual_shift - expected_shift) < 0.02


def test_goal_already_reached():
    _, _, baseline = _forecast()
    goal = Goal("g", "cust_lotte", "Klein doel", target_amount=100.0, already_saved=150.0)
    result = compute_goal_progress(goal, baseline)
    assert result.status == "already_reached"
    assert result.months_to_reach == 0


def test_goal_unreachable_when_surplus_negative():
    _, _, baseline = _forecast()
    goal = Goal("g", "cust_lotte", "Onmogelijk doel", target_amount=100_000.0)
    # A large negative extra "savings" simulates spending down faster than earning.
    result = compute_goal_progress(goal, baseline, extra_savings_per_month=-100_000.0)
    assert result.status == "unreachable"
    assert result.months_to_reach is None


def test_goal_with_target_date_computes_required_monthly_amount():
    _, _, baseline = _forecast()
    goal = Goal(
        "g", "cust_lotte", "Doel met datum", target_amount=1200.0,
        target_date=date(date.today().year + 1, date.today().month, 1),
    )
    result = compute_goal_progress(goal, baseline)
    assert result.required_monthly_for_target_date is not None
    assert result.required_monthly_for_target_date > 0


def test_extra_savings_speeds_up_goal():
    _, _, baseline = _forecast()
    goal = Goal("g", "cust_lotte", "Huurwaarborg", target_amount=2500.0, already_saved=300.0)
    without_extra = compute_goal_progress(goal, baseline, extra_savings_per_month=0.0)
    with_extra = compute_goal_progress(goal, baseline, extra_savings_per_month=300.0)
    assert with_extra.months_to_reach <= without_extra.months_to_reach


def test_savings_suggestions_never_exceed_category_cap():
    from app.analytics.savings_sources import CATEGORY_POLICY

    txs, _, _ = _forecast()
    suggestions, _ = suggest_savings(txs, target_extra_savings=10_000.0)
    monthly_avg = {
        s.category: s.current_avg_monthly for s in suggestions
    }
    for s in suggestions:
        cap = monthly_avg[s.category] * CATEGORY_POLICY[s.category]["max_cut_fraction"]
        assert s.suggested_cut <= cap + 0.01


def test_savings_suggestions_sum_to_target_when_reachable():
    txs, _, _ = _forecast()
    suggestions, shortfall = suggest_savings(txs, target_extra_savings=50.0)
    total = sum(s.suggested_cut for s in suggestions)
    assert abs(total + shortfall - 50.0) < 0.01
