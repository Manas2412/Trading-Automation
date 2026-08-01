"""In-memory BarStore — the reference implementation and backtest store.

Pure-Python, dependency-free, fully deterministic. It is both the store the backtester runs
against and the test double for other layers. The Postgres/TimescaleDB implementation (added
when a live DB is available) must match this behavior exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from qtrade.common.types import Bar
from qtrade.storage.base import DAY, BarStore, Clock, LookAheadError, StoreMode


def _require_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return ts.astimezone(timezone.utc)


class InMemoryBarStore(BarStore):
    """Keyed by (token, interval) -> {ts: Bar}. Last write wins on duplicate ts (idempotent upsert).

    In BACKTEST mode a `clock` is required; reads never return bars after `clock.now()`, and a
    request whose window extends past the clock raises LookAheadError.
    """

    def __init__(self, mode: StoreMode = StoreMode.LIVE, clock: Clock | None = None) -> None:
        if mode is StoreMode.BACKTEST and clock is None:
            raise ValueError("BACKTEST mode requires a clock")
        self._mode = mode
        self._clock = clock
        self._data: dict[tuple[int, str], dict[datetime, Bar]] = {}

    def upsert_bars(self, bars: Sequence[Bar], interval: str = DAY) -> int:
        n = 0
        for bar in bars:
            bucket = self._data.setdefault((bar.token, interval), {})
            bucket[bar.ts] = bar  # Bar.ts is already tz-aware UTC
            n += 1
        return n

    def get_bars(
        self, token: int, start: datetime, end: datetime, interval: str = DAY
    ) -> list[Bar]:
        start = _require_utc(start)
        end = _require_utc(end)
        if start > end:
            raise ValueError("start must be <= end")

        horizon = end
        if self._mode is StoreMode.BACKTEST:
            assert self._clock is not None  # guaranteed by __init__
            now = self._clock.now()
            if end > now:
                raise LookAheadError(
                    f"backtest read to {end.isoformat()} exceeds clock {now.isoformat()}"
                )
            horizon = min(end, now)

        bucket = self._data.get((token, interval), {})
        selected = [b for ts, b in bucket.items() if start <= ts <= horizon]
        selected.sort(key=lambda b: b.ts)
        return selected

    def latest_ts(self, token: int, interval: str = DAY) -> datetime | None:
        bucket = self._data.get((token, interval), {})
        if not bucket:
            return None
        keys = bucket.keys()
        if self._mode is StoreMode.BACKTEST:
            assert self._clock is not None
            now = self._clock.now()
            visible = [ts for ts in keys if ts <= now]
            return max(visible) if visible else None
        return max(keys)


__all__ = ["InMemoryBarStore"]
