"""Signal contracts. See docs/LLD.md sec 3 and skill backtest-honesty.

A SignalModel turns market data (read only up to `asof`) into per-instrument Signals. It never
places orders and never reads the future — the store's backtest guard enforces the latter.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol, runtime_checkable

from qtrade.common.types import Signal
from qtrade.storage.base import DAY


@runtime_checkable
class SignalModel(Protocol):
    def compute(
        self, asof: datetime, universe: Sequence[int], interval: str = DAY
    ) -> list[Signal]: ...


__all__ = ["SignalModel"]
