import pytest
from src.dutching import SelectionInput, calculate_dutch_stakes


def test_dutching_equalizes_payouts_for_valid_odds():
    selections = [
        SelectionInput(selection_id="101", label="Under 1.5", odds=4.20),
        SelectionInput(selection_id="102", label="HT/FT 1/X", odds=14.0),
        SelectionInput(selection_id="103", label="HT/FT 2/X", odds=16.0),
    ]
    plan = calculate_dutch_stakes(selections=selections, total_stake=100.0, min_stake_unit=0.01)

    assert plan.implied_prob_sum < 1.0
    assert plan.total_stake == pytest.approx(100.0, abs=0.05)
    assert plan.net_profit > 0

    payouts = [item["projected_payout"] for item in plan.allocations]
    assert max(payouts) - min(payouts) <= 0.10


def test_dutching_rejects_overround_above_or_equal_one():
    selections = [
        SelectionInput(selection_id="201", label="Leg A", odds=1.50),
        SelectionInput(selection_id="202", label="Leg B", odds=2.50),
    ]
    with pytest.raises(ValueError, match="Negative Dutching edge"):
        calculate_dutch_stakes(selections=selections, total_stake=100.0)


def test_dutching_rejects_invalid_stake():
    selections = [SelectionInput(selection_id="301", label="Under 1.5", odds=4.20)]
    with pytest.raises(ValueError):
        calculate_dutch_stakes(selections=selections, total_stake=0.0)
