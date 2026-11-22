from types import SimpleNamespace
from src.brokers.betfair_client import BetfairExchangeClient
from src.config import BotConfig
from src.scanner import OddsRule, extract_qualifying_selections, filter_markets_by_leagues


def _make_config(dry_run: bool = True) -> BotConfig:
    return BotConfig(
        betfair_username="demo_user",
        betfair_password="demo_password",
        betfair_app_key="demo_app_key",
        cert_path="certs",
        dry_run=dry_run,
        base_capital=100.0,
        min_stake_unit=1.0,
    )


def test_fetch_football_markets_attaches_best_back_odds():
    client = BetfairExchangeClient(config=_make_config(dry_run=True))

    fake_catalogue = SimpleNamespace(
        market_id="1.555001",
        market_name="Under/Over 1.5 Goals",
        description=SimpleNamespace(market_type="OVER_UNDER_15"),
        competition=SimpleNamespace(name="English Premier League"),
        event=SimpleNamespace(name="Arsenal v Chelsea"),
        runners=[
            SimpleNamespace(selection_id=101, runner_name="Under 1.5 Goals"),
            SimpleNamespace(selection_id=102, runner_name="Over 1.5 Goals"),
        ],
    )

    fake_market_book = SimpleNamespace(
        market_id="1.555001",
        runners=[
            SimpleNamespace(
                selection_id=101,
                ex=SimpleNamespace(available_to_back=[{"price": 4.20, "size": 25.0}]),
            ),
            SimpleNamespace(
                selection_id=102,
                ex=SimpleNamespace(available_to_back=[{"price": 1.28, "size": 100.0}]),
            ),
        ],
    )

    client.trading.login = lambda: None
    client.trading.betting.list_market_catalogue = lambda **kwargs: [fake_catalogue]
    client.trading.betting.list_market_book = lambda **kwargs: [fake_market_book]

    markets = client.fetch_football_markets(market_type_codes=["OVER_UNDER_15"])
    league_markets = filter_markets_by_leagues(markets, ["English Premier League"])
    qualifying = extract_qualifying_selections(
        league_markets,
        [OddsRule(label="OU 1.5 Target", min_odds=4.15, max_odds=4.25, runner_keyword="Under 1.5")],
    )

    assert len(qualifying) == 1
    assert qualifying[0].selection_id == "101"
    assert qualifying[0].odds == 4.20


def test_place_dutch_orders_respects_dry_run():
    client = BetfairExchangeClient(config=_make_config(dry_run=True))
    result = client.place_dutch_orders(
        market_id="1.555001",
        orders=[{"selection_id": "101", "price": 4.20, "size": 23.81}],
    )
    assert result["status"] == "DRY_RUN"
    assert len(result["orders_simulated"]) == 1
EOFcat << 'EOF' > tests/test_betfair_client.py
from types import SimpleNamespace
from src.brokers.betfair_client import BetfairExchangeClient
from src.config import BotConfig
from src.scanner import OddsRule, extract_qualifying_selections, filter_markets_by_leagues


def _make_config(dry_run: bool = True) -> BotConfig:
    return BotConfig(
        betfair_username="demo_user",
        betfair_password="demo_password",
        betfair_app_key="demo_app_key",
        cert_path="certs",
        dry_run=dry_run,
        base_capital=100.0,
        min_stake_unit=1.0,
    )


def test_fetch_football_markets_attaches_best_back_odds():
    client = BetfairExchangeClient(config=_make_config(dry_run=True))

    fake_catalogue = SimpleNamespace(
        market_id="1.555001",
        market_name="Under/Over 1.5 Goals",
        description=SimpleNamespace(market_type="OVER_UNDER_15"),
        competition=SimpleNamespace(name="English Premier League"),
        event=SimpleNamespace(name="Arsenal v Chelsea"),
        runners=[
            SimpleNamespace(selection_id=101, runner_name="Under 1.5 Goals"),
            SimpleNamespace(selection_id=102, runner_name="Over 1.5 Goals"),
        ],
    )

    fake_market_book = SimpleNamespace(
        market_id="1.555001",
        runners=[
            SimpleNamespace(
                selection_id=101,
                ex=SimpleNamespace(available_to_back=[{"price": 4.20, "size": 25.0}]),
            ),
            SimpleNamespace(
                selection_id=102,
                ex=SimpleNamespace(available_to_back=[{"price": 1.28, "size": 100.0}]),
            ),
        ],
    )

    client.trading.login = lambda: None
    client.trading.betting.list_market_catalogue = lambda **kwargs: [fake_catalogue]
    client.trading.betting.list_market_book = lambda **kwargs: [fake_market_book]

    markets = client.fetch_football_markets(market_type_codes=["OVER_UNDER_15"])
    league_markets = filter_markets_by_leagues(markets, ["English Premier League"])
    qualifying = extract_qualifying_selections(
        league_markets,
        [OddsRule(label="OU 1.5 Target", min_odds=4.15, max_odds=4.25, runner_keyword="Under 1.5")],
    )

    assert len(qualifying) == 1
    assert qualifying[0].selection_id == "101"
    assert qualifying[0].odds == 4.20


def test_place_dutch_orders_respects_dry_run():
    client = BetfairExchangeClient(config=_make_config(dry_run=True))
    result = client.place_dutch_orders(
        market_id="1.555001",
        orders=[{"selection_id": "101", "price": 4.20, "size": 23.81}],
    )
    assert result["status"] == "DRY_RUN"
    assert len(result["orders_simulated"]) == 1
EOFcat << 'EOF' > tests/test_betfair_client.py
from types import SimpleNamespace
from src.brokers.betfair_client import BetfairExchangeClient
from src.config import BotConfig
from src.scanner import OddsRule, extract_qualifying_selections, filter_markets_by_leagues


def _make_config(dry_run: bool = True) -> BotConfig:
    return BotConfig(
        betfair_username="demo_user",
        betfair_password="demo_password",
        betfair_app_key="demo_app_key",
        cert_path="certs",
        dry_run=dry_run,
        base_capital=100.0,
        min_stake_unit=1.0,
    )


def test_fetch_football_markets_attaches_best_back_odds():
    client = BetfairExchangeClient(config=_make_config(dry_run=True))

    fake_catalogue = SimpleNamespace(
        market_id="1.555001",
        market_name="Under/Over 1.5 Goals",
        description=SimpleNamespace(market_type="OVER_UNDER_15"),
        competition=SimpleNamespace(name="English Premier League"),
        event=SimpleNamespace(name="Arsenal v Chelsea"),
        runners=[
            SimpleNamespace(selection_id=101, runner_name="Under 1.5 Goals"),
            SimpleNamespace(selection_id=102, runner_name="Over 1.5 Goals"),
        ],
    )

    fake_market_book = SimpleNamespace(
        market_id="1.555001",
        runners=[
            SimpleNamespace(
                selection_id=101,
                ex=SimpleNamespace(available_to_back=[{"price": 4.20, "size": 25.0}]),
            ),
            SimpleNamespace(
                selection_id=102,
                ex=SimpleNamespace(available_to_back=[{"price": 1.28, "size": 100.0}]),
            ),
        ],
    )

    client.trading.login = lambda: None
    client.trading.betting.list_market_catalogue = lambda **kwargs: [fake_catalogue]
    client.trading.betting.list_market_book = lambda **kwargs: [fake_market_book]

    markets = client.fetch_football_markets(market_type_codes=["OVER_UNDER_15"])
    league_markets = filter_markets_by_leagues(markets, ["English Premier League"])
    qualifying = extract_qualifying_selections(
        league_markets,
        [OddsRule(label="OU 1.5 Target", min_odds=4.15, max_odds=4.25, runner_keyword="Under 1.5")],
    )

    assert len(qualifying) == 1
    assert qualifying[0].selection_id == "101"
    assert qualifying[0].odds == 4.20


def test_place_dutch_orders_respects_dry_run():
    client = BetfairExchangeClient(config=_make_config(dry_run=True))
    result = client.place_dutch_orders(
        market_id="1.555001",
        orders=[{"selection_id": "101", "price": 4.20, "size": 23.81}],
    )
    assert result["status"] == "DRY_RUN"
    assert len(result["orders_simulated"]) == 1
