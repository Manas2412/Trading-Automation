"""Storage layer contracts: the BarStore port, clocks, and the look-ahead guard.

Point-in-time correctness is a first-class concern (docs/LLD.md sec 4, 6). In BACKTEST mode a
read that reaches beyond the current clock is a look-ahead bug and is rejected outright.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol, runtime_checkable

from qtrade.common.types import Bar

# Supported bar intervals (kept as plain strings to match storage columns).
DAY = "day"
MINUTE = "minute"


class LookAheadError(Exception):
    """Raised when a BACKTEST-mode read would return data after the current clock."""


class StoreMode(str, Enum):
    LIVE = "live"
    BACKTEST = "backtest"


@runtime_checkable
class Clock(Protocol):
    """A source of 'now'. In backtest the event loop advances it deterministically."""

    def now(self) -> datetime: ...


class FixedClock:
    """A settable clock for backtests and tests. Always timezone-aware UTC."""

    def __init__(self, now: datetime) -> None:
        self._now = _require_utc(now)

    def now(self) -> datetime:
        return self._now

    def advance_to(self, ts: datetime) -> None:
        ts = _require_utc(ts)
        if ts < self._now:
            raise ValueError("clock cannot move backwards")
        self._now = ts


def _require_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return ts.astimezone(timezone.utc)


@runtime_checkable
class BarStore(Protocol):
    """Persistence port for OHLCV bars. Implementations must honor point-in-time reads."""

    def upsert_bars(self, bars: Sequence[Bar], interval: str = DAY) -> int: ...

    def get_bars(
        self, token: int, start: datetime, end: datetime, interval: str = DAY
    ) -> list[Bar]: ...

    def latest_ts(self, token: int, interval: str = DAY) -> datetime | None: ...


__all__ = [
    "DAY", "MINUTE", "LookAheadError", "StoreMode", "Clock", "FixedClock", "BarStore",
]
