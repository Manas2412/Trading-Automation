"""Tests for backtest performance metrics."""

import math

from qtrade.backtest import max_drawdown, returns_from_equity, sharpe, total_return


def test_total_return():
    assert math.isclose(total_return([100.0, 110.0]), 0.10)
    assert total_return([100.0]) == 0.0  # too short


def test_returns_from_equity():
    r = returns_from_equity([100.0, 110.0, 121.0])
    assert len(r) == 2
    assert math.isclose(r[0], 0.10) and math.isclose(r[1], 0.10)


def test_max_drawdown():
    assert math.isclose(max_drawdown([100.0, 120.0, 90.0, 130.0]), 0.25)  # 120 -> 90
    assert max_drawdown([100.0, 110.0, 120.0]) == 0.0  # monotonic up


def test_sharpe_zero_variance():
    # constant equal returns -> undefined -> 0.0
    assert sharpe([0.1, 0.1, 0.1]) == 0.0


def test_sharpe_positive():
    s = sharpe([0.01, 0.02, -0.005, 0.015, 0.008])
    assert s > 0.0


def test_sharpe_too_short():
    assert sharpe([0.01]) == 0.0
