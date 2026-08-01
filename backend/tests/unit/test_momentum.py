"""Tests for the momentum signal and strategy, incl. an end-to-end backtest."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from qtrade.backtest import CostModel, run_backtest
from qtrade.common.types import Bar
from qtrade.signals import MomentumSignal, MomentumStrategy
from qtrade.storage import FixedClock, InMemoryBarStore, StoreMode

UTC = timezone.utc


def _d(day: int) -> datetime:
    return datetime(2026, 1, day, 10, 0, tzinfo=UTC)


def _flat_bar(token: int, day: int, price: str) -> Bar:
    p = Decimal(price)
    return Bar(token=token, ts=_d(day), open=p, high=p, low=p, close=p, volume=100)


def _rising_store(mode=StoreMode.LIVE, clock=None):
    store = InMemoryBarStore(mode=mode, clock=clock)
    # token 1 trends up; token 2 flat
    for day, price in enumerate(["100", "102", "104", "106", "108", "110"], start=1):
        store.upsert_bars([_flat_bar(1, day, price)])
        store.upsert_bars([_flat_bar(2, day, "100")])
    return store


def test_signal_ranks_winner_above_flat():
    store = _rising_store()
    sigs = MomentumSignal(store, lookback_days=5).compute(_d(6), [1, 2])
    by_token = {s.token: s.expected_return for s in sigs}
    assert by_token[1] > 0
    assert by_token[2] == 0.0
    assert by_token[1] > by_token[2]


def test_signal_skips_insufficient_history():
    store = _rising_store()
    # lookback window ending day1 contains a single bar -> excluded
    sigs = MomentumSignal(store, lookback_days=5).compute(_d(1), [1, 2])
    assert sigs == []


def test_strategy_targets_cover_whole_universe():
    store = _rising_store()
    strat = MomentumStrategy(
        store, [1, 2], lookback_days=3, top_n=1, gross_capital=Decimal("10000")
    )
    targets = strat.target_positions(_d(6))
    tokens = {t.token for t in targets}
    assert tokens == {1, 2}  # selected + flattened
    tgt = {t.token: t.target_qty for t in targets}
    assert tgt[1] > 0  # winner bought
    assert tgt[2] == 0  # flat name flattened


def test_lookback_and_top_n_validation():
    store = _rising_store()
    with pytest.raises(ValueError):
        MomentumSignal(store, lookback_days=0)
    with pytest.raises(ValueError):
        MomentumStrategy(store, [1], lookback_days=3, top_n=0, gross_capital=Decimal("1"))


def test_end_to_end_backtest_buys_the_winner():
    clock = FixedClock(_d(1))
    store = _rising_store(mode=StoreMode.BACKTEST, clock=clock)
    strat = MomentumStrategy(
        store, [1, 2], lookback_days=3, top_n=1, gross_capital=Decimal("10000")
    )
    res = run_backtest(
        timeline=[_d(d) for d in range(1, 7)],
        tokens=[1, 2],
        store=store,
        clock=clock,
        strategy=strat,
        cost_model=CostModel(),
        initial_cash=Decimal("10000"),
    )
    # bought the trending name, never the flat one
    assert res.final_positions.get(1, 0) > 0
    assert 2 not in res.final_positions
    assert all(t.token == 1 for t in res.trades)
    # equity grew as the winner rose
    assert res.equity_curve[-1][1] > res.equity_curve[0][1]
