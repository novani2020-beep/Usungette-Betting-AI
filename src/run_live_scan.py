from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import signal
import time
from typing import Any, Dict, List, Optional

from src.brokers.betfair_client import BetfairExchangeClient
from src.config import BotConfig
from src.cycle_manager import CycleLedger
from src.dutching import SelectionInput, calculate_dutch_stakes
from src.scanner import OddsRule, extract_qualifying_selections, filter_markets_by_leagues

WAT = ZoneInfo("Africa/Lagos")


def _timestamp() -> str:
    now_utc = datetime.now(timezone.utc)
    now_wat = now_utc.astimezone(WAT)
    return f"{now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} ({now_wat.strftime('%H:%M:%S WAT')})"


def log(message: str) -> None:
    print(f"[{_timestamp()}] {message}", flush=True)


def default_odds_rules() -> List[OddsRule]:
    """Target odds rules for initial live-data scanning in dry-run mode."""
    return [
        OddsRule(
            label="Under 1.5 Target",
            min_odds=4.10,
            max_odds=4.35,
            runner_keyword="Under 1.5",
        ),
        OddsRule(
            label="HT/FT Draw Pivot",
            min_odds=11.0,
            max_odds=22.0,
            market_type_code="HALF_TIME_FULL_TIME",
        ),
    ]


def run_single_scan_pass(
    config: BotConfig,
    ledger: CycleLedger,
    client: BetfairExchangeClient,
    rules: List[OddsRule],
    market_type_codes: List[str],
    max_markets: int = 30,
) -> Dict[str, Any]:
    """Executes one 2-league scan pass and returns a summary dictionary."""
    active_leagues = ledger.next_two_leagues()
    log(
        f"Batch start -> Leagues: {active_leagues} | "
        f"Base Capital: {ledger.base_capital:.2f} | DRY_RUN={config.dry_run}"
    )

    try:
        raw_markets = client.fetch_football_markets(
            market_type_codes=market_type_codes,
            max_results=max_markets,
        )
    except Exception as exc:
        # Release active batch lock so future cycles are not stuck if fetch fails
        ledger.active_leagues = []
        raise RuntimeError(f"Market fetch failed for {active_leagues}: {exc}") from exc
    finally:
        try:
            client.logout()
        except Exception:
            pass

    league_markets = filter_markets_by_leagues(raw_markets, active_leagues=active_leagues)
    log(
        f"Markets fetched: {len(raw_markets)} -> "
        f"Matched active leagues: {len(league_markets)}"
    )

    qualifying: List[SelectionInput] = extract_qualifying_selections(league_markets, rules)
    log(f"Qualifying selections inside odds bands: {len(qualifying)}")

    # Release batch lock after scan pass in dry-run mode so subsequent intervals can rotate
    ledger.active_leagues = []

    if not qualifying:
        log("No qualifying selections found in this pass. No orders placed.")
        return {"status": "NO_MATCHES", "leagues": active_leagues, "legs": 0}

    for sel in qualifying:
        log(f"  * [{sel.selection_id}] {sel.label} @ {sel.odds:.2f}")

    try:
        plan = calculate_dutch_stakes(
            selections=qualifying,
            total_stake=ledger.base_capital,
            min_stake_unit=config.min_stake_unit,
        )
    except ValueError as exc:
        log(f"Skipping Dutching allocation due to edge/input check: {exc}")
        return {"status": "SKIPPED_EDGE", "leagues": active_leagues, "legs": len(qualifying)}

    log(
        f"Dutch Plan -> Implied Sum: {plan.implied_prob_sum:.4f} | "
        f"Total Stake: {plan.total_stake:.2f} | Expected Return: {plan.expected_return:.2f} | "
        f"Net Profit: {plan.net_profit:.2f}"
    )

    orders = [
        {
            "selection_id": item["selection_id"],
            "price": item["odds"],
            "size": item["stake"],
        }
        for item in plan.allocations
    ]

    dry_result = client.place_dutch_orders(
        market_id="MULTI_MARKET_SCAN",
        orders=orders,
    )
    log(f"Order execution status: {dry_result['status']} ({len(orders)} legs simulated)")
    return {
        "status": dry_result["status"],
        "leagues": active_leagues,
        "legs": len(orders),
        "net_profit": plan.net_profit,
    }


def run_live_scan(
    league_queue: Optional[List[str]] = None,
    market_type_codes: Optional[List[str]] = None,
    max_markets: int = 30,
    interval_seconds: int = 60,
    max_iterations: Optional[int] = 1,
    sleep_fn=time.sleep,
) -> None:
    """
    Runs repeated live scans in dry-run mode.
    - max_iterations=1 (default) runs a single pass and exits cleanly.
    - max_iterations=None loops continuously until interrupted (Ctrl+C / SIGTERM).
    """
    config = BotConfig.from_env()
    if not config.dry_run:
        raise RuntimeError(
            "Safety block: BOT_DRY_RUN must be 'true' when running src/run_live_scan.py."
        )

    if interval_seconds < 1:
        raise ValueError("interval_seconds must be at least 1.")

    leagues = league_queue or [
        "English Premier League",
        "Spanish La Liga",
        "Italian Serie A",
        "German Bundesliga",
    ]
    codes = market_type_codes or ["OVER_UNDER_15", "HALF_TIME_FULL_TIME"]
    rules = default_odds_rules()

    ledger = CycleLedger(
        base_capital=config.base_capital,
        total_balance=config.base_capital * 2,
        league_queue=leagues,
    )
    client = BetfairExchangeClient(config=config)

    stop_requested = False

    def _handle_stop(signum: int, frame: Any) -> None:
        nonlocal stop_requested
        stop_requested = True
        log(f"Received stop signal ({signum}). Finishing cleanly...")

    previous_sigint = signal.getsignal(signal.SIGINT)
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    iteration = 0
    try:
        while not stop_requested:
            if max_iterations is not None and iteration >= max_iterations:
                break

            iteration += 1
            log(f"--- Scan Iteration #{iteration} ---")
            try:
                run_single_scan_pass(
                    config=config,
                    ledger=ledger,
                    client=client,
                    rules=rules,
                    market_type_codes=codes,
                    max_markets=max_markets,
                )
            except Exception as exc:
                log(f"ERROR during iteration #{iteration}: {exc}")

            if stop_requested:
                break
            if max_iterations is not None and iteration >= max_iterations:
                break

            log(f"Sleeping {interval_seconds}s before next scan...")
            sleep_fn(interval_seconds)
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)
        log("Live scanner stopped cleanly.")


if __name__ == "__main__":
    # Set max_iterations=None when you want continuous polling every interval_seconds
    run_live_scan(interval_seconds=60, max_iterations=1)
