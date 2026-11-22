from src.dutching import calculate_dutch_stakes
from src.scanner import OddsRule, extract_qualifying_selections, filter_markets_by_leagues


def _sample_markets():
    return [
        {
            "market_id": "1.1001",
            "market_type_code": "OVER_UNDER_15",
            "competition": "English Premier League",
            "event": "Arsenal v Chelsea",
            "runners": [
                {"selection_id": "10", "name": "Under 1.5 Goals", "odds": 4.20},
                {"selection_id": "11", "name": "Over 1.5 Goals", "odds": 1.28},
            ],
        },
        {
            "market_id": "1.1002",
            "market_type_code": "HALF_TIME_FULL_TIME",
            "competition": "Spanish La Liga",
            "event": "Getafe v Sevilla",
            "runners": [
                {"selection_id": "20", "name": "1/X", "odds": 14.50},
                {"selection_id": "21", "name": "2/X", "odds": 16.00},
                {"selection_id": "22", "name": "1/1", "odds": 2.60},
            ],
        },
        {
            "market_id": "1.1003",
            "market_type_code": "OVER_UNDER_15",
            "competition": "Italian Serie A",
            "event": "Inter v Milan",
            "runners": [
                {"selection_id": "30", "name": "Under 1.5 Goals", "odds": 4.18},
            ],
        },
    ]


def test_filter_markets_keeps_only_active_two_leagues():
    markets = _sample_markets()
    filtered = filter_markets_by_leagues(
        markets,
        active_leagues=["English Premier League", "Spanish La Liga"],
    )

    assert len(filtered) == 2
    competitions = {m["competition"] for m in filtered}
    assert competitions == {"English Premier League", "Spanish La Liga"}


def test_extract_qualifying_selections_and_feed_dutching():
    markets = _sample_markets()
    two_league_markets = filter_markets_by_leagues(
        markets,
        active_leagues=["English Premier League", "Spanish La Liga"],
    )

    rules = [
        OddsRule(
            label="Under 1.5 Target",
            min_odds=4.15,
            max_odds=4.25,
            runner_keyword="Under 1.5",
        ),
        OddsRule(
            label="HT/FT Draw Pivot",
            min_odds=12.0,
            max_odds=20.0,
            market_type_code="HALF_TIME_FULL_TIME",
        ),
    ]

    selections = extract_qualifying_selections(two_league_markets, rules)
    assert len(selections) == 3
    assert {s.selection_id for s in selections} == {"10", "20", "21"}

    plan = calculate_dutch_stakes(selections=selections, total_stake=100.0, min_stake_unit=0.01)
    assert plan.implied_prob_sum < 1.0
    assert plan.net_profit > 0
cat << 'EOF' > tests/test_scanner.py
from src.dutching import calculate_dutch_stakes
from src.scanner import OddsRule, extract_qualifying_selections, filter_markets_by_leagues


def _sample_markets():
    return [
        {
            "market_id": "1.1001",
            "market_type_code": "OVER_UNDER_15",
            "competition": "English Premier League",
            "event": "Arsenal v Chelsea",
            "runners": [
                {"selection_id": "10", "name": "Under 1.5 Goals", "odds": 4.20},
                {"selection_id": "11", "name": "Over 1.5 Goals", "odds": 1.28},
            ],
        },
        {
            "market_id": "1.1002",
            "market_type_code": "HALF_TIME_FULL_TIME",
            "competition": "Spanish La Liga",
            "event": "Getafe v Sevilla",
            "runners": [
                {"selection_id": "20", "name": "1/X", "odds": 14.50},
                {"selection_id": "21", "name": "2/X", "odds": 16.00},
                {"selection_id": "22", "name": "1/1", "odds": 2.60},
            ],
        },
        {
            "market_id": "1.1003",
            "market_type_code": "OVER_UNDER_15",
            "competition": "Italian Serie A",
            "event": "Inter v Milan",
            "runners": [
                {"selection_id": "30", "name": "Under 1.5 Goals", "odds": 4.18},
            ],
        },
    ]


def test_filter_markets_keeps_only_active_two_leagues():
    markets = _sample_markets()
    filtered = filter_markets_by_leagues(
        markets,
        active_leagues=["English Premier League", "Spanish La Liga"],
    )

    assert len(filtered) == 2
    competitions = {m["competition"] for m in filtered}
    assert competitions == {"English Premier League", "Spanish La Liga"}


def test_extract_qualifying_selections_and_feed_dutching():
    markets = _sample_markets()
    two_league_markets = filter_markets_by_leagues(
        markets,
        active_leagues=["English Premier League", "Spanish La Liga"],
    )

    rules = [
        OddsRule(
            label="Under 1.5 Target",
            min_odds=4.15,
            max_odds=4.25,
            runner_keyword="Under 1.5",
        ),
        OddsRule(
            label="HT/FT Draw Pivot",
            min_odds=12.0,
            max_odds=20.0,
            market_type_code="HALF_TIME_FULL_TIME",
        ),
    ]

    selections = extract_qualifying_selections(two_league_markets, rules)
    assert len(selections) == 3
    assert {s.selection_id for s in selections} == {"10", "20", "21"}

    plan = calculate_dutch_stakes(selections=selections, total_stake=100.0, min_stake_unit=0.01)
    assert plan.implied_prob_sum < 1.0
    assert plan.net_profit > 0
EOF
