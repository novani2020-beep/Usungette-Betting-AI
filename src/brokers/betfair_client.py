from typing import Any, Dict, List
import betfairlightweight
from betfairlightweight import filters
from src.config import BotConfig


class BetfairExchangeClient:
    """Wrapper around betfairlightweight for market discovery and order placement."""

    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.trading = betfairlightweight.APIClient(
            username=config.betfair_username,
            password=config.betfair_password,
            app_key=config.betfair_app_key,
            certs=config.cert_path,
        )
        self._logged_in = False

    def login(self) -> None:
        if not self._logged_in:
            self.trading.login()
            self._logged_in = True

    def logout(self) -> None:
        if self._logged_in:
            self.trading.logout()
            self._logged_in = False

    def fetch_football_markets(
        self,
        market_type_codes: List[str],
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetches upcoming football markets for given Betfair marketTypeCodes,
        e.g., ['OVER_UNDER_15', 'HALF_TIME_FULL_TIME'].
        """
        self.login()
        market_filter = filters.market_filter(
            event_type_ids=["1"],  # 1 = Soccer / Football
            market_type_codes=market_type_codes,
        )
        books = self.trading.betting.list_market_catalogue(
            filter=market_filter,
            market_projection=["COMPETITION", "EVENT", "RUNNER_DESCRIPTION"],
            max_results=max_results,
        )
        results: List[Dict[str, Any]] = []
        for book in books:
            results.append({
                "market_id": book.market_id,
                "market_name": book.market_name,
                "competition": book.competition.name if book.competition else "Unknown",
                "event": book.event.name if book.event else "Unknown",
                "runners": [
                    {"selection_id": str(r.selection_id), "name": r.runner_name}
                    for r in (book.runners or [])
                ],
            })
        return results

    def place_dutch_orders(
        self,
        market_id: str,
        orders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Places limit orders on Betfair Exchange when dry_run is False.
        Each order dict expects: selection_id (str), price (float), size (float).
        """
        if self.config.dry_run:
            return {
                "status": "DRY_RUN",
                "market_id": market_id,
                "orders_simulated": orders,
            }

        self.login()
        instructions = [
            filters.place_instruction(
                order_type="LIMIT",
                selection_id=str(item["selection_id"]),
                side="BACK",
                limit_order=filters.limit_order(
                    price=float(item["price"]),
                    size=float(item["size"]),
                    persistence_type="LAPSE",
                ),
            )
            for item in orders
        ]
        report = self.trading.betting.place_orders(
            market_id=market_id,
            instructions=instructions,
        )
        return {
            "status": report.status,
            "market_id": report.market_id,
            "instruction_reports": [
                {
                    "status": ir.status,
                    "bet_id": ir.bet_id,
                    "error_code": ir.error_code,
                }
                for ir in (report.instruction_reports or [])
            ],
        }
