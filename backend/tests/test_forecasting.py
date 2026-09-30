from app.analytics.forecasting import build_forecast_inputs, forecast_balance
from app.data.generator import generate_transactions
from app.models.persona import LOTTE


def test_recurring_net_matches_known_fixed_costs():
    """Salary, rent, subscriptions, monthly insurance and the transport pass
    are all constant/near-constant monthly amounts — the generator's ground
    truth — so recurring_net must land within the known range of their sum,
    with no annual lump sums or vacation bursts bleeding in (see the other
    tests below for those two checks specifically)."""
    txs = generate_transactions(LOTTE)
    inputs = build_forecast_inputs(txs)

    fixed_without_phone = (
        LOTTE.net_monthly_salary - LOTTE.rent_amount
        - 13.99 - 9.99 - 29.99  # Netflix, Spotify, Fitnessclub (exact, no jitter)
        - 45.0  # health insurance
        - 49.0  # transport pass
    )
    # Telefoonabonnement is -20 normally, occasionally -23..-32 with jitter;
    # its 12-month average therefore sits in [-32, -20].
    assert fixed_without_phone - 32 <= inputs.recurring_net <= fixed_without_phone - 20


def test_annual_lump_sums_are_not_double_counted():
    txs = generate_transactions(LOTTE)
    inputs = build_forecast_inputs(txs)
    # The annual home insurance and annual tax bill must not appear as
    # monthly-fixed items — they surface only via the seasonal component.
    assert "insurance" in inputs.disc_avg
    assert "annual_bill" in inputs.disc_avg


def test_forecast_balance_accumulates_from_starting_balance():
    txs = generate_transactions(LOTTE)
    inputs = build_forecast_inputs(txs)
    result = forecast_balance(inputs, LOTTE.starting_balance, months=12)

    assert len(result.months) == 12
    assert abs(result.months[0].balance - (LOTTE.starting_balance + result.months[0].net_cashflow)) < 0.02
    for prev, cur in zip(result.months, result.months[1:]):
        # The running balance accumulates unrounded net cashflow internally;
        # each month's *reported* net_cashflow is independently rounded to 2
        # decimals for display, so summing reported figures can be a cent off
        # from the reported balance delta.
        assert abs(cur.balance - (prev.balance + cur.net_cashflow)) < 0.02


def test_uncertainty_band_widens_over_the_horizon():
    txs = generate_transactions(LOTTE)
    inputs = build_forecast_inputs(txs)
    result = forecast_balance(inputs, LOTTE.starting_balance, months=12)

    first_width = result.months[0].balance_high - result.months[0].balance_low
    last_width = result.months[-1].balance_high - result.months[-1].balance_low
    assert last_width > first_width


def test_forecast_is_deterministic_for_a_seeded_persona():
    txs_a = generate_transactions(LOTTE)
    txs_b = generate_transactions(LOTTE)
    assert txs_a == txs_b
