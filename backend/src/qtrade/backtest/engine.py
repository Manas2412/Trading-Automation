"""Event-driven backtest engine. See docs/LLD.md sec 6 and skill backtest-honesty.

Design guarantees:
- NO LOOK-AHEAD: the strategy decides at bar `t` (clock at t, so the store refuses future reads),
  and orders fill at the NEXT bar's open. A decision can never use data it wouldn't have had live.
- COSTS ALWAYS APPLIED: every fill is charged via the CostModel (slippage in price + charges).
- DETERMINISTIC: single clock, no randomness — reruns are identical.

Convention: a strategy returns target positions only for tokens it wants to set; a token it omits
is left unchanged. Return target_qty=0 to flatten a position.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from qtrade.backtest.costs import CostModel
from qtrade.backtest.metrics import (
    max_drawdown,
    returns_from_equity,
    sharpe,
    total_return,
)
from qtrade.common.types import Bar, Side, TargetPosition
from qtrade.storage.base import DAY, BarStore, FixedClock


class Strategy(Protocol):
    """Given the current time, return desired target positions using data up to `asof` only."""

    def target_positions(self, asof: datetime) -> list[TargetPosition]: ...


@dataclass(frozen=True)
class Trade:
    ts: datetime
    token: int
    side: Side
    qty: int
    price: Decimal
    fee: Decimal


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: list[tuple[datetime, float]]
    trades: list[Trade]
    metrics: dict[str, float]
    final_positions: dict[int, int]
    final_cash: float


def _bar_at(store: BarStore, token: int, ts: datetime, interval: str) -> Bar | None:
    bars = store.get_bars(token, ts, ts, interval)
    return bars[0] if bars else None


def _validate_timeline(timeline: Sequence[datetime]) -> None:
    if len(timeline) < 2:
        raise ValueError("timeline needs at least 2 points (decide then fill)")
    for ts in timeline:
        if ts.tzinfo is None:
            raise ValueError("timeline datetimes must be timezone-aware")
    if list(timeline) != sorted(timeline):
        raise ValueError("timeline must be sorted ascending")


def run_backtest(
    *,
    timeline: Sequence[datetime],
    tokens: Sequence[int],
    store: BarStore,
    clock: FixedClock,
    strategy: Strategy,
    cost_model: CostModel,
    initial_cash: Decimal,
    interval: str = DAY,
) -> BacktestResult:
    """Run the backtest over `timeline`. `store` must be in backtest mode driven by `clock`."""
    _validate_timeline(timeline)
    if not tokens:
        raise ValueError("tokens must be non-empty")

    cash = Decimal(initial_cash)
    positions: dict[int, int] = {}
    last_price: dict[int, Decimal] = {}
    trades: list[Trade] = []
    equity_curve: list[tuple[datetime, float]] = [(timeline[0], float(cash))]

    for i in range(len(timeline) - 1):
        t = timeline[i]
        t_next = timeline[i + 1]

        # 1) decide at bar t (clock at t -> store forbids reading past t)
        clock.advance_to(t)
        desired = {tp.token: tp.target_qty for tp in strategy.target_positions(t)}

        # 2) fill deltas at the next bar's open
        clock.advance_to(t_next)
        for token in tokens:
            if token not in desired:
                continue
            delta = desired[token] - positions.get(token, 0)
            if delta == 0:
                continue
            bar = _bar_at(store, token, t_next, interval)
            if bar is None:
                continue  # no price available; cannot fill
            side = Side.BUY if delta > 0 else Side.SELL
            qty = abs(delta)
            price = cost_model.fill_price(side, bar.open)
            fee = cost_model.charges(side, qty, price)
            notional = price * Decimal(qty)
            cash = cash - notional - fee if side is Side.BUY else cash + notional - fee
            positions[token] = desired[token]
            trades.append(Trade(t_next, token, side, qty, price, fee))

        # 3) mark-to-market at t_next close
        for token in tokens:
            bar = _bar_at(store, token, t_next, interval)
            if bar is not None:
                last_price[token] = bar.close
        equity = cash + sum(
            Decimal(q) * last_price[tok]
            for tok, q in positions.items()
            if q != 0 and tok in last_price
        )
        equity_curve.append((t_next, float(equity)))

    equity_values = [e for _, e in equity_curve]
    metrics = {
        "total_return": total_return(equity_values),
        "max_drawdown": max_drawdown(equity_values),
        "sharpe": sharpe(returns_from_equity(equity_values)),
        "n_trades": float(len(trades)),
    }
    final_positions = {k: v for k, v in positions.items() if v != 0}
    return BacktestResult(equity_curve, trades, metrics, final_positions, float(cash))


__all__ = ["Strategy", "Trade", "BacktestResult", "run_backtest"]
