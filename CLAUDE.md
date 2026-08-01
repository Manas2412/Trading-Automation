# CLAUDE.md — Operating Guide for AI-Assisted Development

This file is read by Claude (and any AI coding assistant) on every task in this repo.
It encodes the architecture, the non-negotiable rules, and the conventions. Follow it.

## 1. What this project is

`qtrade` is a **personal, single-account systematic trading platform** for Indian markets
(NSE/BSE/MCX), executing through **Zerodha Kite Connect**. It progresses from suggesting
trades to compliant auto-execution. It is NOT high-frequency trading and NOT a product sold
to others. Full plan: `Trading_Automation_Roadmap.docx`; design in `docs/HLD.md`, `docs/LLD.md`.

## 2. The non-negotiable rules (safety first — never violate)

1. **The LLM is never in the trigger path.** Signals, sizing, risk, and execution are
   deterministic, tested code. An LLM may only produce *features* (news/sentiment scores)
   upstream of the math. It must never decide size or place an order from free-form text.
2. **Order placement is idempotent and race-free.** Every order carries a client-generated
   idempotency key. A retry, duplicate tick, or restart must never create a duplicate order.
3. **The risk layer cannot be bypassed.** Every order passes through position/exposure/leverage
   checks and the drawdown kill-switch before reaching the broker. No code path skips it.
4. **The kill-switch outranks everything.** A max-drawdown / daily-loss breach halts new orders
   and can flatten positions, overriding any strategy or model.
5. **No real orders without an explicit guard.** Live order placement requires
   `LIVE_TRADING_ENABLED=true` AND `QTRADE_ENV=live`. Tests and dev/paper runs must be
   structurally unable to hit the live orders endpoint — use the paper/sim broker.
6. **The backtester never looks ahead.** A bar's decision may only use data available at that
   bar's close. Costs (brokerage, STT, GST, stamp duty, slippage, impact) are always applied.
7. **Secrets never touch git.** Credentials live in `.env` (git-ignored) / a vault. Never hard-code
   API keys, and never log an access token.
8. **Self-improvement is gated.** No model auto-promotes to live. A challenger must beat the live
   champion out-of-sample before promotion; the kill-switch still outranks it.

## 3. Confirmed tech stack

- **Python** for research, ML, AND execution (broker API round-trip dominates latency; a compiled
  language only after a *measured* hot path, and then prefer Rust — realistically not before
  tick-level intraday).
- **TimescaleDB** (Postgres) for time-series; Parquet + DuckDB for research datasets.
- **React.js** production frontend; **Streamlit** as interim dashboard.
- **Prefect** for orchestration; static-IP VM for the compliant execution host.
- Key libs: pandas/polars, numpy, statsmodels, scikit-learn, lightgbm, cvxpy, kiteconnect,
  sqlalchemy, pydantic, structlog.

## 4. Execution frequency staging

- **Stage 1 (build first): swing/daily** — hold hours-to-days, few orders/day at bar close.
  Latency irrelevant; validate the whole pipeline with real money at low risk.
- **Stage 2 (only after Stage 1 proven): intraday tick-reactive** — many orders/day; latency and
  Kite per-second/daily request budgets matter. Only stage where a compiled hot path may be revisited.

## 5. Repository map

```
src/qtrade/
  common/     config, logging, types, time/calendar helpers, idempotency keys
  data/       ingestion: Kite historical + live WebSocket, corporate actions, news
  storage/    TimescaleDB + Parquet/DuckDB access; point-in-time correctness
  signals/    features + signal families (factors, TS, pairs, GARCH, ML, news)
  risk/       sizing, portfolio construction, hard limits, kill-switch
  backtest/   event-driven engine, cost model, walk-forward, metrics
  execution/  order routing, slicing, fills, reconciliation, broker adapters
  ops/        dashboards, alerts, scheduling, audit log
  llm/        news/sentiment feature generation (upstream only)
docs/         HLD.md, LLD.md, adr/ (architecture decision records)
tests/        unit/ + integration/
```

## 6. Conventions

- **Layout:** `src/` layout, package `qtrade`. Type-hint everything (`mypy` strict-ish).
- **Config:** via `pydantic-settings` reading `.env`; no magic constants scattered in code.
- **Money & prices:** use `Decimal` or integer paise where correctness matters; never bare float for cash.
- **Time:** store/compute in UTC internally; display IST. Use `pandas-market-calendars` for sessions.
- **Logging:** structured (`structlog`); every trading decision and order is logged to the audit trail.
- **Errors:** fail closed. On uncertainty about state (e.g. unknown order status), do NOT re-send —
  reconcile against the broker first.
- **Tooling:** `ruff` (format+lint), `mypy`, `pytest`. Run `make check` before considering work done.

## 7. Testing requirements

- Every signal, risk rule, and execution path has unit tests. Risk limits and the kill-switch have
  explicit tests proving they block violating orders.
- Idempotency has a test proving a duplicated request produces exactly one order.
- Backtester has tests for no-look-ahead and correct cost application.
- Integration tests use a **paper/sim broker**, never live credentials.

## 8. How to work

- Build **phase by phase** per the roadmap (Phase 0 first: data + storage + honest backtester).
- Prefer small, reviewed changes. Update `docs/` and add an ADR when a design decision changes.
- When unsure about a trading-safety trade-off, choose the more conservative option and flag it.
