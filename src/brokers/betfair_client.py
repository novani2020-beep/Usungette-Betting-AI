from typing import Any, Dict, List
import betfairlightweight
from betfairlightweight import filters
from src.config import BotConfig


class BetfairExchangeClient:
    """Wrapper around betfairlightweight for market discovery, live prices, and order placement."""

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

    def _extract_best_back_price(self, runner_book: Any) -> float | None:
        """Returns the highest available BACK price from runner order book, or None if unavailable."""
        ex = getattr(runner_book, "ex", None)
        available_to_back = getattr(ex, "available_to_back", None) or []
        if not available_to_back:
            return None

        best_price = None
        for entry in available_to_back:
            price_val = (
                entry.get("price")
                if isinstance(entry, dict)
                else getattr(entry, "price", None)
            )
            if price_val is not None:
                price_float = float(price_val)
                if best_price is None or price_float > best_price:
                    best_price = price_float
        return best_price

    def fetch_football_markets(
        self,
        market_type_codes: List[str],
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetches upcoming football markets for given Betfair marketTypeCodes and
        enriches each runner with live best BACK decimal odds from list_market_book.
        """
        self.login()
        market_filter = filters.market_filter(
            event_type_ids=["1"],  # 1 = Soccer / Football
            market_type_codes=market_type_codes,
        )
        catalogues = self.trading.betting.list_market_catalogue(
            filter=market_filter,
            market_projection=[
                "COMPETITION",
                "EVENT",
                "MARKET_DESCRIPTION",
                "RUNNER_DESCRIPTION",
            ],
            max_results=max_results,
        )
        if not catalogues:
            return []

        market_ids = [c.market_id for c in catalogues if c.market_id]
        price_map: Dict[str, Dict[str, float | None]] = {
            mid: {} for mid in market_ids
        }

        # Betfair list_market_book handles batches cleanly; chunk by 10 to stay well within limits
        chunk_size = 10
        price_projection = filters.price_projection(price_data=["EX_BEST_OFFERS"])
        for start in range(0, len(market_ids), chunk_size):
            batch_ids = market_ids[start : start + chunk_size]
            market_books = self.trading.betting.list_market_book(
                market_ids=batch_ids,
                price_projection=price_projection,
            )
            for mbook in market_books or []:
                mid = str(mbook.market_id)
                for rbook in getattr(mbook, "runners", None) or []:
                    sid = str(getattr(rbook, "selection_id", ""))
                    if sid:
                        price_map.setdefault(mid, {})[sid] = self._extract_best_back_price(rbook)

        results: List[Dict[str, Any]] = []
        for cat in catalogues:
            mid = str(cat.market_id)
            desc = getattr(cat, "description", None)
            market_type_code = (
                getattr(desc, "market_type", None)
                or (market_type_codes[0] if len(market_type_codes) == 1 else "")
            )
            runner_prices = price_map.get(mid, {})

            runners_out: List[Dict[str, Any]] = []
            for r in getattr(cat, "runners", None) or []:
                sid = str(r.selection_id)
                runners_out.append({
                    "selection_id": sid,
                    "name": r.runner_name,
                    "odds": runner_prices.get(sid),
                })

            results.append({
                "market_id": mid,
                "market_name": cat.market_name,
                "market_type_code": str(market_type_code),
                "competition": cat.competition.name if cat.competition else "Unknown",
                "event": cat.event.name if cat.event else "Unknown",
                "runners": runners_out,
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
