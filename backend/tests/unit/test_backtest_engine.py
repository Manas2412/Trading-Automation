"""Tests for the event-driven backtest engine: correctness and no-look-ahead."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from qtrade.backtest import CostModel, run_backtest
from qtrade.common.types import Bar, Side, TargetPosition
from qtrade.storage import FixedClock, InMemoryBarStore, LookAheadError, StoreMode

UTC = timezone.utc
CM = CostModel()


def _d(day: int) -> datetime:
    return datetime(2026, 1, day, 10, 0, tzinfo=UTC)


def _bar(day: int, o: str, c: str) -> Bar:
    return Bar(
        token=1, ts=_d(day),
        open=Decimal(o), high=Decimal(c if c > o else o),
        low=Decimal(o if o < c else c), close=Decimal(c), volume=100,
    )


def _make_store():
    clock = FixedClock(_d(1))
    store = InMemoryBarStore(mode=StoreMode.BACKTEST, clock=clock)
    store.upsert_bars([_bar(1, "100", "100"), _bar(2, "100", "110"), _bar(3, "110", "121")])
    return store, clock


class _AlwaysHoldTen:
    def target_positions(self, asof):
        return [TargetPosition(token=1, target_qty=10)]


class _PeeksAtFuture:
    """A misbehaving strategy that tries to read beyond `asof`."""

    def __init__(self, store):
        self._store = store

    def target_positions(self, asof):
        # reading to day 3 while clock is at day 1 must be blocked by the store
        self._store.get_bars(1, _d(1), _d(3))
        return []


def test_buy_and_hold_fills_at_next_open():
    store, clock = _make_store()
    res = run_backtest(
        timeline=[_d(1), _d(2), _d(3)], tokens=[1], store=store, clock=clock,
        strategy=_AlwaysHoldTen(), cost_model=CM, initial_cash=Decimal("10000"),
    )
    assert len(res.trades) == 1
    tr = res.trades[0]
    assert tr.side is Side.BUY and tr.qty == 10 and tr.price == Decimal("100.02")
    assert res.final_positions == {1: 10}


def test_cash_and_equity_accounting():
    store, clock = _make_store()
    res = run_backtest(
        timeline=[_d(1), _d(2), _d(3)], tokens=[1], store=store, clock=clock,
        strategy=_AlwaysHoldTen(), cost_model=CM, initial_cash=Decimal("10000"),
    )
    fee = CM.charges(Side.BUY, 10, Decimal("100.02"))
    expected_cash = Decimal("10000") - Decimal("100.02") * 10 - fee
    assert res.final_cash == float(expected_cash)
    # equity curve starts at initial cash and ends higher (price rose 100->121)
    assert res.equity_curve[0][1] == 10000.0
    assert res.equity_curve[-1][1] > res.equity_curve[0][1]
    assert len(res.equity_curve) == 3
    assert res.metrics["n_trades"] == 1.0


def test_no_look_ahead_is_enforced():
    store, clock = _make_store()
    with pytest.raises(LookAheadError):
        run_backtest(
            timeline=[_d(1), _d(2), _d(3)], tokens=[1], store=store, clock=clock,
            strategy=_PeeksAtFuture(store), cost_model=CM, initial_cash=Decimal("10000"),
        )


def test_timeline_must_be_sorted():
    store, clock = _make_store()
    with pytest.raises(ValueError):
        run_backtest(
            timeline=[_d(3), _d(1)], tokens=[1], store=store, clock=clock,
            strategy=_AlwaysHoldTen(), cost_model=CM, initial_cash=Decimal("10000"),
        )


def test_timeline_needs_two_points():
    store, clock = _make_store()
    with pytest.raises(ValueError):
        run_backtest(
            timeline=[_d(1)], tokens=[1], store=store, clock=clock,
            strategy=_AlwaysHoldTen(), cost_model=CM, initial_cash=Decimal("10000"),
        )
