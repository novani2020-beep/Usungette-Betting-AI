from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SelectionInput:
    selection_id: str
    label: str
    odds: float


@dataclass
class DutchStakePlan:
    total_stake: float
    expected_return: float
    net_profit: float
    implied_prob_sum: float
    allocations: List[Dict[str, float | str]]


def calculate_dutch_stakes(
    selections: List[SelectionInput],
    total_stake: float,
    min_stake_unit: float = 1.0,
) -> DutchStakePlan:
    """
    Computes equal-payout Dutching stakes across multiple outcomes.
    Raises ValueError if combined implied probability >= 1.0 (guaranteed loss).
    """
    if not selections or total_stake <= 0:
        raise ValueError("Selections must be non-empty and total_stake must be > 0.")

    for s in selections:
        if s.odds <= 1.01:
            raise ValueError(f"Invalid odds {s.odds} for {s.label}.")

    inv_probs = [1.0 / s.odds for s in selections]
    implied_sum = sum(inv_probs)

    if implied_sum >= 1.0:
        raise ValueError(
            f"Negative Dutching edge: implied probability sum is {implied_sum:.4f} (>= 1.0)."
        )

    allocations: List[Dict[str, float | str]] = []
    allocated_total = 0.0

    for i, s in enumerate(selections):
        raw_stake = total_stake * (inv_probs[i] / implied_sum)
        rounded_stake = round(raw_stake / min_stake_unit) * min_stake_unit
        allocated_total += rounded_stake
        allocations.append({
            "selection_id": s.selection_id,
            "label": s.label,
            "odds": s.odds,
            "stake": round(rounded_stake, 2),
            "projected_payout": round(rounded_stake * s.odds, 2),
        })

    min_payout = min(float(item["projected_payout"]) for item in allocations)
    net_profit = round(min_payout - allocated_total, 2)

    return DutchStakePlan(
        total_stake=round(allocated_total, 2),
        expected_return=round(min_payout, 2),
        net_profit=net_profit,
        implied_prob_sum=round(implied_sum, 4),
        allocations=allocations,
    )
