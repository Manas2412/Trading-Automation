"""Transaction cost model for Indian equities. See docs/LLD.md sec 6 and skill backtest-honesty.

A backtest without costs is meaningless: brokerage, STT, exchange txn, SEBI fee, stamp duty, GST,
and slippage all bite. The DEFAULT RATES below are representative of equity *delivery* and MUST be
verified against current SEBI/exchange/broker schedules before any result is trusted (LLD open
item). The structure is correct regardless of the exact constants.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from qtrade.common.types import Side

_BPS = Decimal("10000")


class CostModel(BaseModel):
    """Per-fill charges + slippage. All rates are fractions of turnover unless noted.

    VERIFY these against current rules — they change over time and differ by segment
    (delivery vs intraday, equity vs F&O vs commodity).
    """

    model_config = ConfigDict(frozen=True)

    brokerage_rate: Decimal = Decimal("0")          # Zerodha equity delivery = 0
    brokerage_cap: Decimal = Decimal("20")          # per-order cap when brokerage_rate > 0
    stt_rate: Decimal = Decimal("0.001")            # 0.1% on buy & sell (delivery)
    exchange_txn_rate: Decimal = Decimal("0.0000297")
    sebi_rate: Decimal = Decimal("0.000001")        # ~Rs 10 per crore
    stamp_rate_buy: Decimal = Decimal("0.00015")    # 0.015% on the buy side only
    gst_rate: Decimal = Decimal("0.18")             # 18% on (brokerage + exchange txn)
    slippage_bps: Decimal = Decimal("2")            # price slippage, basis points

    def fill_price(self, side: Side, ref_price: Decimal) -> Decimal:
        """Reference price adjusted against us by slippage (buys up, sells down)."""
        slip = ref_price * self.slippage_bps / _BPS
        return ref_price + slip if side is Side.BUY else ref_price - slip

    def charges(self, side: Side, qty: int, price: Decimal) -> Decimal:
        """Charges for a fill of `qty` @ `price`; slippage is already applied in the price."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        turnover = price * Decimal(qty)

        if self.brokerage_rate > 0:
            brokerage = min(turnover * self.brokerage_rate, self.brokerage_cap)
        else:
            brokerage = Decimal("0")

        stt = turnover * self.stt_rate
        txn = turnover * self.exchange_txn_rate
        sebi = turnover * self.sebi_rate
        stamp = turnover * self.stamp_rate_buy if side is Side.BUY else Decimal("0")
        gst = (brokerage + txn) * self.gst_rate

        return brokerage + stt + txn + sebi + stamp + gst


__all__ = ["CostModel"]
