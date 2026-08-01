"""Typed application configuration (reads .env). See docs/LLD.md sec 9.

Central rule enforced here: real orders require env == "live" AND live_trading_enabled.
Nothing else in the system decides that.
"""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Env = Literal["dev", "paper", "live"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # runtime
    qtrade_env: Env = "dev"
    log_level: str = "INFO"

    # safety guards
    live_trading_enabled: bool = False
    max_daily_loss_pct: float = 2.0
    max_position_pct: float = 10.0
    max_gross_leverage: float = 1.0

    # database (optional until the storage layer is wired)
    database_url: str | None = None

    # Zerodha Kite Connect (optional until data/execution layers)
    kite_api_key: str | None = None
    kite_api_secret: SecretStr | None = None

    # AWS Bedrock — LLM feature layer (Phase 1). Feature-only, never a trade trigger.
    aws_region: str = "ap-south-1"
    aws_profile: str | None = None
    bedrock_model_id: str | None = None
    bedrock_enabled: bool = False

    @property
    def live_trading_allowed(self) -> bool:
        """The single source of truth for whether real orders may be placed."""
        return self.qtrade_env == "live" and self.live_trading_enabled

    def require_live(self) -> None:
        """Raise unless live trading is fully enabled. Call before any real order path."""
        if not self.live_trading_allowed:
            raise RuntimeError(
                "Live trading is not enabled: require qtrade_env='live' and "
                f"live_trading_enabled=true (got env={self.qtrade_env!r}, "
                f"enabled={self.live_trading_enabled})."
            )


def load_settings() -> Settings:
    """Load settings from environment / .env."""
    return Settings()


__all__ = ["Settings", "Env", "load_settings"]
