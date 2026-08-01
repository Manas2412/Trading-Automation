"""qtrade.backtest — honest event-driven backtesting."""

from qtrade.backtest.costs import CostModel
from qtrade.backtest.engine import BacktestResult, Strategy, Trade, run_backtest
from qtrade.backtest.metrics import (
    max_drawdown,
    returns_from_equity,
    sharpe,
    total_return,
)

__all__ = [
    "CostModel", "BacktestResult", "Strategy", "Trade", "run_backtest",
    "max_drawdown", "returns_from_equity", "sharpe", "total_return",
]
