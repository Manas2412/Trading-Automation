"""Tests for the in-memory BarStore and the point-in-time / look-ahead guard."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from qtrade.common.types import Bar
from qtrade.storage import (
    FixedClock,
    InMemoryBarStore,
    LookAheadError,
    StoreMode,
)

UTC = timezone.utc


def _bar(day: int, close: str = "100") -> Bar:
    ts = datetime(2026, 1, day, 10, 0, tzinfo=UTC)
    c = Decimal(close)
    return Bar(token=1, ts=ts, open=c, high=c, low=c, close=c, volume=10)


def _d(day: int) -> datetime:
    return datetime(2026, 1, day, 10, 0, tzinfo=UTC)


# ---------- live mode ----------

def test_upsert_and_get_in_order():
    s = InMemoryBarStore()
    s.upsert_bars([_bar(3), _bar(1), _bar(2)])
    got = s.get_bars(1, _d(1), _d(3))
    assert [b.ts.day for b in got] == [1, 2, 3]  # sorted ascending


def test_upsert_is_idempotent_last_wins():
    s = InMemoryBarStore()
    s.upsert_bars([_bar(1, "100")])
    s.upsert_bars([_bar(1, "111")])  # same (token, interval, ts)
    got = s.get_bars(1, _d(1), _d(1))
    assert len(got) == 1 and got[0].close == Decimal("111")


def test_get_bars_inclusive_range():
    s = InMemoryBarStore()
    s.upsert_bars([_bar(1), _bar(2), _bar(3)])
    got = s.get_bars(1, _d(2), _d(2))
    assert [b.ts.day for b in got] == [2]


def test_get_bars_requires_tz_aware():
    s = InMemoryBarStore()
    with pytest.raises(ValueError):
        s.get_bars(1, datetime(2026, 1, 1, 10, 0), _d(3))


def test_get_bars_start_after_end_rejected():
    s = InMemoryBarStore()
    with pytest.raises(ValueError):
        s.get_bars(1, _d(3), _d(1))


def test_latest_ts_live():
    s = InMemoryBarStore()
    assert s.latest_ts(1) is None
    s.upsert_bars([_bar(1), _bar(5)])
    assert s.latest_ts(1) == _d(5)


def test_unknown_token_returns_empty():
    s = InMemoryBarStore()
    s.upsert_bars([_bar(1)])
    assert s.get_bars(999, _d(1), _d(3)) == []


# ---------- backtest mode: point-in-time / no look-ahead ----------

def test_backtest_requires_clock():
    with pytest.raises(ValueError):
        InMemoryBarStore(mode=StoreMode.BACKTEST)


def test_backtest_read_past_clock_raises():
    clock = FixedClock(_d(2))
    s = InMemoryBarStore(mode=StoreMode.BACKTEST, clock=clock)
    s.upsert_bars([_bar(1), _bar(2), _bar(3)])
    with pytest.raises(LookAheadError):
        s.get_bars(1, _d(1), _d(3))  # end (day 3) is beyond clock (day 2)


def test_backtest_read_up_to_clock_ok():
    clock = FixedClock(_d(2))
    s = InMemoryBarStore(mode=StoreMode.BACKTEST, clock=clock)
    s.upsert_bars([_bar(1), _bar(2), _bar(3)])
    got = s.get_bars(1, _d(1), _d(2))
    assert [b.ts.day for b in got] == [1, 2]  # day 3 not visible


def test_backtest_advance_reveals_more():
    clock = FixedClock(_d(1))
    s = InMemoryBarStore(mode=StoreMode.BACKTEST, clock=clock)
    s.upsert_bars([_bar(1), _bar(2), _bar(3)])
    assert [b.ts.day for b in s.get_bars(1, _d(1), _d(1))] == [1]
    clock.advance_to(_d(3))
    assert [b.ts.day for b in s.get_bars(1, _d(1), _d(3))] == [1, 2, 3]


def test_backtest_latest_ts_respects_clock():
    clock = FixedClock(_d(2))
    s = InMemoryBarStore(mode=StoreMode.BACKTEST, clock=clock)
    s.upsert_bars([_bar(1), _bar(2), _bar(3)])
    assert s.latest_ts(1) == _d(2)  # not day 3


def test_clock_cannot_move_backwards():
    clock = FixedClock(_d(3))
    with pytest.raises(ValueError):
        clock.advance_to(_d(1))
