"""Canonical, broker-agnostic domain models for qtrade.

These are immutable value objects shared by every layer (research and live).
Money uses Decimal; time is timezone-aware UTC. See docs/LLD.md sec 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    FUT = "FUT"
    OPT = "OPT"
    COMMODITY = "COMMODITY"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderState(str, Enum):
    NEW = "NEW"
    SENT = "SENT"
    ACK = "ACK"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


def _aware_utc(value: datetime) -> datetime:
    """Require timezone-aware datetimes; normalize to UTC."""
    if not isinstance(value, datetime):
        raise TypeError("expected a datetime")
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return value.astimezone(timezone.utc)


# Reusable: a UTC-normalized, tz-aware datetime.
UtcDatetime = Annotated[datetime, BeforeValidator(_aware_utc)]


class _Frozen(BaseModel):
    """Base: immutable, forbids unknown fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Instrument(_Frozen):
    symbol: str
    exchange: Exchange
    asset_class: AssetClass
    instrument_token: int = Field(gt=0)
    lot_size: int = Field(default=1, gt=0)
    tick_size: Decimal = Field(gt=Decimal("0"))


class Bar(_Frozen):
    """OHLCV bar, adjusted. `ts` is the bar-close time (UTC)."""

    token: int = Field(gt=0)
    ts: UtcDatetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_ohlc(self) -> Bar:
        if not (self.low <= self.open <= self.high and self.low <= self.close <= self.high):
            raise ValueError("OHLC inconsistent: require low <= open/close <= high")
        return self


class Tick(_Frozen):
    token: int = Field(gt=0)
    ts: UtcDatetime
    last_price: Decimal
    volume: int = Field(default=0, ge=0)


class Signal(_Frozen):
    token: int = Field(gt=0)
    ts: UtcDatetime
    expected_return: float
    confidence: float = Field(ge=0.0, le=1.0)
    horizon_days: float = Field(gt=0.0)
    rationale: str = ""


class TargetPosition(_Frozen):
    token: int = Field(gt=0)
    target_qty: int  # signed: +long / -short


class OrderRequest(_Frozen):
    token: int = Field(gt=0)
    side: Side
    qty: int = Field(gt=0)
    order_type: OrderType
    strategy_id: str
    idempotency_key: str
    limit_price: Decimal | None = None

    @model_validator(mode="after")
    def _check_limit(self) -> OrderRequest:
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            raise ValueError("LIMIT order requires a limit_price")
        if self.order_type is OrderType.MARKET and self.limit_price is not None:
            raise ValueError("MARKET order must not carry a limit_price")
        return self


class Order(_Frozen):
    idempotency_key: str
    request: OrderRequest
    state: OrderState
    created_at: UtcDatetime
    updated_at: UtcDatetime
    broker_order_id: str | None = None
    filled_qty: int = Field(default=0, ge=0)
    avg_price: Decimal | None = None


class Fill(_Frozen):
    broker_order_id: str
    token: int = Field(gt=0)
    side: Side
    qty: int = Field(gt=0)
    price: Decimal = Field(gt=Decimal("0"))
    ts: UtcDatetime
    fee: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class Position(_Frozen):
    token: int = Field(gt=0)
    qty: int  # signed
    avg_price: Decimal = Field(ge=Decimal("0"))
    realized_pnl: Decimal = Decimal("0")


__all__ = [
    "Exchange", "Side", "AssetClass", "OrderType", "OrderState",
    "UtcDatetime", "Instrument", "Bar", "Tick", "Signal", "TargetPosition",
    "OrderRequest", "Order", "Fill", "Position",
]
