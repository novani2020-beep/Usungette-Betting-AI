from types import SimpleNamespace
import src.run_live_scan as scanner_runner
from src.brokers.betfair_client import BetfairExchangeClient
from src.config import BotConfig


def _patch_env_and_client(monkeypatch, market_fetcher):
    cfg = BotConfig(
        betfair_username="test_user",
        betfair_password="test_password",
        betfair_app_key="test_key",
        cert_path="certs",
        dry_run=True,
        base_capital=100.0,
        min_stake_unit=0.01,
    )
    monkeypatch.setattr(BotConfig, "from_env", classmethod(lambda cls: cfg))

    def _fake_init(self, config):
        self.config = config
        self._logged_in = False
        self.trading = SimpleNamespace(
            login=lambda: None,
            logout=lambda: None,
            betting=SimpleNamespace(
                list_market_catalogue=lambda **kwargs: [],
                list_market_book=lambda **kwargs: [],
                place_orders=lambda **kwargs: None,
            ),
        )

    monkeypatch.setattr(BetfairExchangeClient, "__init__", _fake_init)
    monkeypatch.setattr(BetfairExchangeClient, "fetch_football_markets", market_fetcher)


def test_run_live_scan_dry_run_end_to_end(monkeypatch, capsys):
    def _fake_fetch(self, market_type_codes, max_results=20):
        return [
            {
                "market_id": "1.999001",
                "market_name": "Under/Over 1.5 Goals",
                "market_type_code": "OVER_UNDER_15",
                "competition": "English Premier League",
                "event": "Liverpool v Everton",
                "runners": [
                    {"selection_id": "501", "name": "Under 1.5 Goals", "odds": 4.20},
                ],
            }
        ]

    _patch_env_and_client(monkeypatch, _fake_fetch)

    scanner_runner.run_live_scan(
        league_queue=["English Premier League", "Spanish La Liga"],
        market_type_codes=["OVER_UNDER_15"],
        interval_seconds=5,
        max_iterations=1,
        sleep_fn=lambda s: None,
    )

    out = capsys.readouterr().out
    assert "UTC (" in out and "WAT)" in out
    assert "['English Premier League', 'Spanish La Liga']" in out
    assert "Order execution status: DRY_RUN (1 legs simulated)" in out


def test_run_live_scan_recovers_from_error_across_iterations(monkeypatch, capsys):
    calls = {"count": 0}
    slept = []

    def _flaky_fetch(self, market_type_codes, max_results=20):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("Temporary exchange timeout")
        return []

    _patch_env_and_client(monkeypatch, _flaky_fetch)

    scanner_runner.run_live_scan(
        league_queue=["English Premier League", "Spanish La Liga", "Serie A", "Bundesliga"],
        market_type_codes=["OVER_UNDER_15"],
        interval_seconds=15,
        max_iterations=2,
        sleep_fn=lambda s: slept.append(s),
    )

    out = capsys.readouterr().out
    assert calls["count"] == 2
    assert slept == [15]
    assert "ERROR during iteration #1" in out
    assert "Scan Iteration #2" in out
