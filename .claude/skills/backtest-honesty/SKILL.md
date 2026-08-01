---
name: backtest-honesty
description: Apply whenever building, changing, or reviewing a backtest, signal, or performance claim in qtrade. Guards against the seven ways a backtest lies.
---
# Backtest Honesty

The backtester is priority #1: a strategy is only as trustworthy as the test behind it.

## Before trusting any result, verify
1. **No look-ahead.** At time t, only data with `ts <= t` is used — features, labels, and fills.
   Fills occur at a realistic later point (e.g. next open), never the same bar's close you decided on.
2. **Costs applied.** Every fill charges brokerage, STT, exchange txn, GST, stamp duty, SEBI fee,
   slippage (spread-based), and market impact (size/ADV). Re-check current Indian rate constants.
3. **No survivorship bias.** Universe includes delisted/merged names for the period tested.
4. **Out-of-sample.** Walk-forward or purged/embargoed CV; report OOS, not in-sample, performance.
5. **Multiple-testing correction.** If many variants were tried, apply a deflated Sharpe / correct for trials.
6. **Realistic fills.** No mid-price fills on illiquid names or oversized orders.
7. **Regime coverage.** Tested across bull/bear/high-low-vol, not one lucky window.

## Report, don't hide
- Equity curve, Sharpe/Sortino/Calmar, max drawdown, turnover, hit rate, deflated Sharpe.
- Benchmark vs. buy-and-hold Nifty (and the relevant index per asset class) AFTER costs.
- Any cap/assumption (fill model, universe cutoff) stated explicitly.

## Parity requirement
The backtest cost/fill model and `PaperBroker` must produce identical charges for the same fill.
