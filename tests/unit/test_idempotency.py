"""Tests for deterministic idempotency keys (exactly-once foundation)."""

from datetime import datetime, timedelta, timezone

import pytest

from qtrade.common.idempotency import order_idempotency_key
from qtrade.common.types import Side

TS = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)


def _key(**overrides):
    base = dict(strategy_id="mom", token=1, side=Side.BUY, qty=10, decision_bar_ts=TS)
    base.update(overrides)
    return order_idempotency_key(**base)


def test_same_intent_same_key():
    assert _key() == _key()


def test_key_is_sha256_hex():
    k = _key()
    assert len(k) == 64
    int(k, 16)  # parses as hex


def test_different_side_differs():
    assert _key(side=Side.BUY) != _key(side=Side.SELL)


def test_different_qty_differs():
    assert _key(qty=10) != _key(qty=11)


def test_different_token_differs():
    assert _key(token=1) != _key(token=2)


def test_different_bar_ts_differs():
    assert _key(decision_bar_ts=TS) != _key(decision_bar_ts=TS + timedelta(days=1))


def test_equivalent_instant_same_key():
    ist = timezone(timedelta(hours=5, minutes=30))
    same_instant_ist = TS.astimezone(ist)
    assert _key(decision_bar_ts=TS) == _key(decision_bar_ts=same_instant_ist)


def test_naive_ts_rejected():
    with pytest.raises(ValueError):
        _key(decision_bar_ts=datetime(2026, 1, 1, 10, 0))


def test_nonpositive_qty_rejected():
    with pytest.raises(ValueError):
        _key(qty=0)
