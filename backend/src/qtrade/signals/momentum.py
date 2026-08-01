"""Cross-sectional momentum: rank the universe by trailing return, go long the winners.

Momentum is the most robust equity anomaly and a sound first strategy. This is deliberately simple
and honest: the signal reads only data up to `asof`, and the strategy sizes positions with naive
equal-notional weighting as a PLACEHOLDER until the risk engine (Phase 2) provides proper sizing.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from qtrade.common.types import Signal, TargetPosition
from qtrade.storage.base import DAY, BarStore


class MomentumSignal:
    """Trailing-return momentum over `lookback_days`. Higher expected_return == stronger winner."""

    def __init__(self, store: BarStore, lookback_days: int, interval: str = DAY) -> None:
        if lookback_days < 1:
            raise ValueError("lookback_days must be >= 1")
        self._store = store
        self._lookback_days = lookback_days
        self._interval = interval

    def compute(
        self, asof: datetime, universe: Sequence[int], interval: str = DAY
    ) -> list[Signal]:
        start = asof - timedelta(days=self._lookback_days)
        out: list[Signal] = []
        for token in universe:
            bars = self._store.get_bars(token, start, asof, interval)
            if len(bars) < 2:
                continue  # not enough history to measure momentum
            first, last = bars[0], bars[-1]
            if first.close <= 0:
                continue
            score = float(last.close / first.close) - 1.0
            out.append(
                Signal(
                    token=token,
                    ts=asof,
                    expected_return=score,
                    confidence=min(1.0, abs(score)),
                    horizon_days=float(self._lookback_days),
                    rationale=f"momentum {self._lookback_days}d = {score:.4f}",
                )
            )
        return out


class MomentumStrategy:
    """Long the top-N positive-momentum names, equal notional; flatten everything else.

    Returns a target for EVERY token in the universe each rebalance (0 to flatten), so the engine
    sets positions explicitly rather than relying on remembered state.
    """

    def __init__(
        self,
        store: BarStore,
        universe: Sequence[int],
        *,
        lookback_days: int,
        top_n: int,
        gross_capital: Decimal,
        interval: str = DAY,
    ) -> None:
        if top_n < 1:
            raise ValueError("top_n must be >= 1")
        self._store = store
        self._universe = list(universe)
        self._top_n = top_n
        self._gross = Decimal(gross_capital)
        self._interval = interval
        self._signal = MomentumSignal(store, lookback_days, interval)

    def _latest_close(self, asof: datetime, token: int) -> Decimal | None:
        bars = self._store.get_bars(token, asof, asof, self._interval)
        return bars[-1].close if bars else None

    def target_positions(self, asof: datetime) -> list[TargetPosition]:
        signals = self._signal.compute(asof, self._universe, self._interval)
        ranked = sorted(
            (s for s in signals if s.expected_return > 0),
            key=lambda s: s.expected_return,
            reverse=True,
        )[: self._top_n]
        selected = {s.token for s in ranked}

        targets: list[TargetPosition] = []
        if ranked:
            budget = self._gross / Decimal(len(ranked))
            for s in ranked:
                price = self._latest_close(asof, s.token)
                qty = int(budget / price) if price and price > 0 else 0
                targets.append(TargetPosition(token=s.token, target_qty=qty))
        # flatten every non-selected universe name
        for token in self._universe:
            if token not in selected:
                targets.append(TargetPosition(token=token, target_qty=0))
        return targets


__all__ = ["MomentumSignal", "MomentumStrategy"]
