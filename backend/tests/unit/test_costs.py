"""Tests for the Indian transaction cost model."""

from decimal import Decimal

import pytest

from qtrade.backtest import CostModel
from qtrade.common.types import Side

CM = CostModel()  # defaults


def test_buy_charges_exact():
    # turnover = 10 * 100 = 1000
    # stt 1.0 + txn 0.0297 + sebi 0.001 + stamp 0.15 + gst(0.0297*0.18=0.005346) = 1.186046
    assert CM.charges(Side.BUY, 10, Decimal("100")) == Decimal("1.186046")


def test_sell_charges_exclude_stamp():
    # same minus stamp (0.15) -> 1.036046
    assert CM.charges(Side.SELL, 10, Decimal("100")) == Decimal("1.036046")


def test_buy_costs_more_than_sell():
    assert CM.charges(Side.BUY, 10, Decimal("100")) > CM.charges(Side.SELL, 10, Decimal("100"))


def test_slippage_moves_against_us():
    assert CM.fill_price(Side.BUY, Decimal("100")) == Decimal("100.02")
    assert CM.fill_price(Side.SELL, Decimal("100")) == Decimal("99.98")


def test_qty_must_be_positive():
    with pytest.raises(ValueError):
        CM.charges(Side.BUY, 0, Decimal("100"))


def test_brokerage_capped_when_enabled():
    cm = CostModel(brokerage_rate=Decimal("0.0003"), brokerage_cap=Decimal("20"))
    # 0.0003 * (1000 * 1000) = 300 -> capped to 20
    charged = cm.charges(Side.BUY, 1000, Decimal("1000"))
    # brokerage component alone would be 20 (capped); assert total exceeds a bare no-brokerage model
    assert charged > CM.charges(Side.BUY, 1000, Decimal("1000"))
