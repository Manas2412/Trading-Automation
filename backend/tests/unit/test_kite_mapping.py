"""Tests for the pure Kite candle/tick mappers (no kiteconnect / network needed)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from qtrade.data import MarketDataError, kite_candle_to_bar
from qtrade.data.kite import _kite_tick_to_tick

IST = timezone(timedelta(hours=5, minutes=30))


def test_candle_maps_to_bar():
    candle = {
        "date": datetime(2026, 1, 2, 15, 30, tzinfo=IST),  # 10:00 UTC
        "open": 100.5, "high": 105, "low": 99.25, "close": 104.75, "volume": 12345,
    }
    bar = kite_candle_to_bar(408065, candle)
    assert bar.token == 408065
    assert bar.ts.tzinfo == timezone.utc and bar.ts.hour == 10
    assert bar.open == Decimal("100.5") and bar.close == Decimal("104.75")
    assert bar.volume == 12345


def test_candle_numeric_via_string_no_float_artifact():
    candle = {
        "date": datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
        "open": 0.1, "high": 0.3, "low": 0.1, "close": 0.3, "volume": 1,
    }
    bar = kite_candle_to_bar(1, candle)
    assert bar.close == Decimal("0.3")  # not 0.29999999999999998


def test_tick_maps_with_exchange_timestamp():
    tick = {
        "instrument_token": 1,
        "exchange_timestamp": datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
        "last_price": 250.25,
        "volume_traded": 500,
    }
    out = _kite_tick_to_tick(tick)
    assert out.token == 1 and out.last_price == Decimal("250.25") and out.volume == 500


def test_tick_without_timestamp_raises():
    with pytest.raises(MarketDataError):
        _kite_tick_to_tick({"instrument_token": 1, "last_price": 10})
