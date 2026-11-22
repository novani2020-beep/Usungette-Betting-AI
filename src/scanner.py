from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from src.dutching import SelectionInput


@dataclass(frozen=True)
class OddsRule:
    """Target decimal odds window for matching runners or market types."""

    label: str
    min_odds: float
    max_odds: float
    runner_keyword: Optional[str] = None
    market_type_code: Optional[str] = None

    def matches_odds(self, odds: float) -> bool:
        return self.min_odds <= odds <= self.max_odds


def filter_markets_by_leagues(
    markets: List[Dict[str, Any]],
    active_leagues: List[str],
) -> List[Dict[str, Any]]:
    """
    Filters market catalogue/book dictionaries to only those belonging
    to the currently active leagues (case-insensitive exact or substring match).
    """
    if not active_leagues:
        return []

    normalized_targets = [league.strip().lower() for league in active_leagues if league.strip()]
    matched_markets: List[Dict[str, Any]] = []

    for market in markets:
        comp_name = str(market.get("competition", "")).strip().lower()
        if any(target == comp_name or target in comp_name for target in normalized_targets):
            matched_markets.append(market)

    return matched_markets


def extract_qualifying_selections(
    markets: List[Dict[str, Any]],
    odds_rules: List[OddsRule],
) -> List[SelectionInput]:
    """
    Extracts SelectionInput items from markets when a runner's decimal odds
    falls inside a matching OddsRule's [min_odds, max_odds] band.

    Expected runner dict shape:
      {"selection_id": "101", "name": "Under 1.5 Goals", "odds": 4.20}
    Expected market dict shape:
      {"market_id": "1.234", "market_type_code": "OVER_UNDER_15", "event": "Team A v Team B", "runners": [...]}
    """
    selections: List[SelectionInput] = []

    for market in markets:
        market_code = str(market.get("market_type_code", "")).strip().upper()
        event_name = str(market.get("event", "")).strip()
        runners = market.get("runners", [])

        for runner in runners:
            raw_odds = runner.get("odds")
            if raw_odds is None:
                continue
            odds_val = float(raw_odds)
            runner_name = str(runner.get("name", "")).strip()
            selection_id = str(runner.get("selection_id", "")).strip()

            for rule in odds_rules:
                if rule.market_type_code and rule.market_type_code.strip().upper() != market_code:
                    continue

                if rule.runner_keyword:
                    kw = rule.runner_keyword.strip().lower()
                    if kw not in runner_name.lower() and kw not in market_code.lower():
                        continue

                if rule.matches_odds(odds_val):
                    label_prefix = f"{event_name} - " if event_name else ""
                    selections.append(
                        SelectionInput(
                            selection_id=selection_id,
                            label=f"{label_prefix}{runner_name} ({rule.label})",
                            odds=odds_val,
                        )
                    )
                    break

    return selections
