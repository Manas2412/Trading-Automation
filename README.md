# qtrade — Personal Systematic Trading Platform

A single-account systematic trading platform for Indian markets (NSE / BSE / MCX),
executing through **Zerodha Kite Connect**. It grows from *suggesting* trades to
*compliant auto-execution*, built on a foundation of honest backtesting and strict
risk discipline.

> **Not** high-frequency trading, and **not** a product for others. Personal use only.

## Status

🚧 **Phase 0 — Foundations** (scaffolding in place; design docs in progress).
See the full plan in `Trading_Automation_Roadmap.docx` and `docs/`.

## Why this exists

The goal is a mathematically sound, self-improving system — not a chatbot wrapper.
The decision core (signals, risk, sizing, execution) is deterministic, tested code.
A language model is used only to turn news/filings into *features*, never to place trades.

## Architecture (7 layers)

| Layer | Package | Responsibility |
|---|---|---|
| Data ingestion | `qtrade.data` | Kite historical + live ticks, corporate actions, news |
| Storage | `qtrade.storage` | TimescaleDB + Parquet/DuckDB, point-in-time correct |
| Signals | `qtrade.signals` | Factors, time-series, pairs, GARCH, ML, news features |
| Risk & portfolio | `qtrade.risk` | Sizing, constraints, kill-switch |
| Backtest & sim | `qtrade.backtest` | Event-driven engine, realistic costs, walk-forward |
| Execution | `qtrade.execution` | Order routing, fills, reconciliation |
| Ops | `qtrade.ops` | Dashboards, alerts, scheduling, audit log |

Details: `docs/HLD.md` (high-level) and `docs/LLD.md` (low-level, incl. concurrency/locking).

## Tech stack

Python (research, ML, and execution) · TimescaleDB · React.js frontend (Streamlit interim) ·
Prefect orchestration · static-IP host for compliant execution.

## Roadmap (summary)

0. **Foundations** — data + storage + honest backtester.
1. **Signals** — nightly ranked buy/sell/hold suggestions (manual action first).
2. **Risk & portfolio** — sizing, hard limits, drawdown kill-switch.
3. **Paper trading & validation** — walk-forward + live-paper gates.
4. **Live auto-execution** — small capital; **Stage 1 swing/daily**, then **Stage 2 intraday**.
5. **Self-improvement** — champion/challenger promotion with out-of-sample gates.

## Getting started (dev)

```bash
# Python 3.10+
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # fill in Kite keys + DB URL (never commit .env)
make check                  # ruff + mypy + pytest
```

## Project layout

```
src/qtrade/      core packages (one per architecture layer)
docs/            HLD, LLD, architecture decision records
tests/           unit + integration (integration uses a paper/sim broker)
scripts/         operational scripts (data pulls, EOD reconciliation)
notebooks/       research scratch
config/          environment / strategy configuration
CLAUDE.md        operating rules for AI-assisted development — read it first
```

## Safety & compliance

- Live orders require an explicit guard (`LIVE_TRADING_ENABLED=true` and `QTRADE_ENV=live`).
- Auto-execution flows only through the registered Kite Connect API, from a whitelisted static IP,
  with algo order tagging and conservative request rates, per SEBI's retail algo framework.
- Every decision and order is written to an audit trail.

## Disclaimer

This software is for the author's personal use. It is **not** investment advice. Trading involves
risk of loss. Nothing here is a recommendation to buy or sell any instrument. Use at your own risk,
and comply with all SEBI/exchange/broker rules.
