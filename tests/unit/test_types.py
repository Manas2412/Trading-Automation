"""Tests for canonical domain models."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from qtrade.common.types import (
    AssetClass,
    Bar,
    Exchange,
    Instrument,
    OrderRequest,
    OrderType,
    Side,
    Signal,
)

UTC_TS = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)


def test_instrument_ok():
    inst = Instrument(
        symbol="INFY",
        exchange=Exchange.NSE,
        asset_class=AssetClass.EQUITY,
        instrument_token=408065,
        tick_size=Decimal("0.05"),
    )
    assert inst.lot_size == 1
    assert inst.exchange is Exchange.NSE


def test_models_are_immutable():
    inst = Instrument(
        symbol="INFY",
        exchange=Exchange.NSE,
        asset_class=AssetClass.EQUITY,
        instrument_token=1,
        tick_size=Decimal("0.05"),
    )
    with pytest.raises(ValidationError):
        inst.symbol = "TCS"  # type: ignore[misc]


def test_bar_requires_tz_aware():
    with pytest.raises(ValidationError):
        Bar(
            token=1,
            ts=datetime(2026, 1, 1, 10, 0),  # naive -> rejected
            open=Decimal("1"), high=Decimal("2"), low=Decimal("1"),
            close=Decimal("1"), volume=10,
        )


def test_bar_ohlc_consistency_enforced():
    with pytest.raises(ValidationError):
        Bar(
            token=1, ts=UTC_TS,
            open=Decimal("5"), high=Decimal("4"),  # high < open -> invalid
            low=Decimal("1"), close=Decimal("3"), volume=10,
        )


def test_bar_ts_normalized_to_utc():
    from datetime import timedelta

    ist = timezone(timedelta(hours=5, minutes=30))
    bar = Bar(
        token=1,
        ts=datetime(2026, 1, 1, 15, 30, tzinfo=ist),
        open=Decimal("1"), high=Decimal("2"), low=Decimal("1"),
        close=Decimal("2"), volume=1,
    )
    assert bar.ts.tzinfo == timezone.utc
    assert bar.ts.hour == 10  # 15:30 IST == 10:00 UTC


def test_signal_confidence_bounds():
    with pytest.raises(ValidationError):
        Signal(token=1, ts=UTC_TS, expected_return=0.01, confidence=1.5, horizon_days=5)
    ok = Signal(token=1, ts=UTC_TS, expected_return=0.01, confidence=0.6, horizon_days=5)
    assert 0.0 <= ok.confidence <= 1.0


def test_order_request_qty_positive():
    with pytest.raises(ValidationError):
        OrderRequest(
            token=1, side=Side.BUY, qty=0, order_type=OrderType.MARKET,
            strategy_id="s1", idempotency_key="k",
        )


def test_limit_order_requires_price():
    with pytest.raises(ValidationError):
        OrderRequest(
            token=1, side=Side.BUY, qty=1, order_type=OrderType.LIMIT,
            strategy_id="s1", idempotency_key="k",  # missing limit_price
        )


def test_market_order_rejects_price():
    with pytest.raises(ValidationError):
        OrderRequest(
            token=1, side=Side.BUY, qty=1, order_type=OrderType.MARKET,
            strategy_id="s1", idempotency_key="k", limit_price=Decimal("100"),
        )


def test_valid_limit_order():
    req = OrderRequest(
        token=1, side=Side.SELL, qty=5, order_type=OrderType.LIMIT,
        strategy_id="s1", idempotency_key="k", limit_price=Decimal("101.5"),
    )
    assert req.limit_price == Decimal("101.5")
