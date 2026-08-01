"""Deterministic idempotency keys for order placement. See docs/LLD.md sec 7.1.

The same trading intent must always map to the same key so that a retry, duplicate
tick, or process restart can never produce a second broker order. The key is derived
purely from the intent — never from wall-clock time or a random value.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from qtrade.common.types import Side

_SEP = "|"


def order_idempotency_key(
    *,
    strategy_id: str,
    token: int,
    side: Side,
    qty: int,
    decision_bar_ts: datetime,
) -> str:
    """Return a stable hex key for an order intent.

    Args are keyword-only to prevent positional mistakes. `decision_bar_ts` must be
    timezone-aware; it is normalized to UTC so equal instants yield equal keys.
    """
    if qty <= 0:
        raise ValueError("qty must be positive")
    if decision_bar_ts.tzinfo is None:
        raise ValueError("decision_bar_ts must be timezone-aware (UTC)")

    ts_utc = decision_bar_ts.astimezone(timezone.utc)
    canonical = _SEP.join(
        [
            "v1",
            strategy_id,
            str(int(token)),
            Side(side).value,
            str(int(qty)),
            ts_utc.isoformat(),
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = ["order_idempotency_key"]
