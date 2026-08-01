"""Performance metrics computed from an equity curve. See skill backtest-honesty.

Report risk-adjusted numbers, not just returns. All functions take floats and are pure.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

TRADING_DAYS = 252


def returns_from_equity(equity: Sequence[float]) -> list[float]:
    """Simple period-over-period returns from an equity curve."""
    out: list[float] = []
    for prev, cur in zip(equity[:-1], equity[1:], strict=True):
        if prev == 0:
            out.append(0.0)
        else:
            out.append(cur / prev - 1.0)
    return out


def total_return(equity: Sequence[float]) -> float:
    if len(equity) < 2 or equity[0] == 0:
        return 0.0
    return equity[-1] / equity[0] - 1.0


def max_drawdown(equity: Sequence[float]) -> float:
    """Largest peak-to-trough decline as a positive fraction (0.2 == 20%)."""
    peak = -math.inf
    worst = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            dd = (peak - v) / peak
            worst = max(worst, dd)
    return worst


def sharpe(returns: Sequence[float], periods_per_year: int = TRADING_DAYS) -> float:
    """Annualized Sharpe (risk-free = 0). Returns 0.0 if undefined (no variance)."""
    n = len(returns)
    if n < 2:
        return 0.0
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    sd = math.sqrt(var)
    # Treat effectively-constant returns as zero volatility; a Sharpe there is meaningless,
    # and floating-point noise would otherwise yield a huge spurious value.
    if sd < 1e-12:
        return 0.0
    return (mean / sd) * math.sqrt(periods_per_year)


__all__ = ["returns_from_equity", "total_return", "max_drawdown", "sharpe", "TRADING_DAYS"]
