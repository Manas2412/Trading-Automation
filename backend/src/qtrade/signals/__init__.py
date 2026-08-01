"""qtrade.signals — signal models and strategies."""

from qtrade.signals.base import SignalModel
from qtrade.signals.momentum import MomentumSignal, MomentumStrategy

__all__ = ["SignalModel", "MomentumSignal", "MomentumStrategy"]
