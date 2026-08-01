# 0002 — Zerodha Kite Connect as broker & API

**Status:** Accepted · 2026-08-01

## Context
SEBI's retail algo framework makes the broker the compliance gateway: auto-execution must flow
through a registered API from a whitelisted static IP, with algo tagging and rate limits.

## Decision
Use **Zerodha Kite Connect** (official `kiteconnect` Python client) for auth, historical candles,
live WebSocket ticks, orders, positions, and reconciliation.

## Consequences
- Compliant execution path by construction.
- Must design around Kite's per-second and daily request/order budgets.
- Broker access is abstracted behind an adapter interface so a paper/sim broker can substitute in tests.
