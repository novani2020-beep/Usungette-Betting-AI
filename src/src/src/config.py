import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    betfair_username: str
    betfair_password: str
    betfair_app_key: str
    cert_path: str
    dry_run: bool = True
    base_capital: float = 100.0
    min_stake_unit: float = 1.0

    @classmethod
    def from_env(cls) -> "BotConfig":
        dry_run_raw = os.getenv("BOT_DRY_RUN", "true").strip().lower()
        dry_run = dry_run_raw in ("1", "true", "yes", "on")

        return cls(
            betfair_username=os.getenv("BETFAIR_USERNAME", "").strip(),
            betfair_password=os.getenv("BETFAIR_PASSWORD", "").strip(),
            betfair_app_key=os.getenv("BETFAIR_APP_KEY", "").strip(),
            cert_path=os.getenv("BETFAIR_CERT_PATH", "certs").strip(),
            dry_run=dry_run,
            base_capital=float(os.getenv("BOT_BASE_CAPITAL", "100.0")),
            min_stake_unit=float(os.getenv("BOT_MIN_STAKE_UNIT", "1.0")),
        )
