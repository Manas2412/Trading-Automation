"""Tests for MockMarketData and the chunked backfill."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from qtrade.common.types import Bar, Tick
from qtrade.data import MockMarketData, backfill_bars
from qtrade.storage import InMemoryBarStore

UTC = timezone.utc


def _d(day: int) -> datetime:
    return datetime(2026, 1, day, 10, 0, tzinfo=UTC)


def _bar(day: int) -> Bar:
    c = Decimal("100")
    return Bar(token=1, ts=_d(day), open=c, high=c, low=c, close=c, volume=10)


def test_historical_filters_range_and_sorts():
    src = MockMarketData()
    src.add_bars([_bar(3), _bar(1), _bar(2)])
    got = src.historical(1, _d(1), _d(2))
    assert [b.ts.day for b in got] == [1, 2]


def test_historical_requires_tz_aware():
    src = MockMarketData()
    with pytest.raises(ValueError):
        src.historical(1, datetime(2026, 1, 1, 10, 0), _d(3))


def test_subscribe_replays_in_time_order_filtered_by_token():
    src = MockMarketData()
    src.add_ticks([
        Tick(token=2, ts=_d(1), last_price=Decimal("10")),
        Tick(token=1, ts=_d(3), last_price=Decimal("30")),
        Tick(token=1, ts=_d(2), last_price=Decimal("20")),
    ])
    seen: list[tuple[int, int]] = []
    src.subscribe([1], lambda t: seen.append((t.token, t.ts.day)))
    assert seen == [(1, 2), (1, 3)]  # token 2 filtered out; ordered by ts


def test_backfill_chunks_cover_full_range():
    src = MockMarketData()
    src.add_bars([_bar(d) for d in range(1, 6)])  # 5 daily bars
    store = InMemoryBarStore()
    written = backfill_bars(
        source=src, store=store, token=1, start=_d(1), end=_d(5), chunk_days=2
    )
    assert written == 5
    assert [b.ts.day for b in store.get_bars(1, _d(1), _d(5))] == [1, 2, 3, 4, 5]


def test_backfill_validates_args():
    src, store = MockMarketData(), InMemoryBarStore()
    with pytest.raises(ValueError):
        backfill_bars(source=src, store=store, token=1, start=_d(5), end=_d(1))
    with pytest.raises(ValueError):
        backfill_bars(source=src, store=store, token=1, start=_d(1), end=_d(5), chunk_days=0)
