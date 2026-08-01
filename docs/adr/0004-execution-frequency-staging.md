# 0004 — Staged execution frequency (swing/daily → intraday)

**Status:** Accepted · 2026-08-01

## Context
Everything that can go wrong (bad fills, reconciliation drift, runaway loops, broken signals) is far
cheaper to discover at daily frequency than at tick speed.

## Decision
Roll out auto-execution in two separated stages. **Stage 1: swing/daily** (hold hours-to-days, few
orders/day at bar close) validates the whole pipeline with real money at low risk. **Stage 2:
intraday tick-reactive** only after Stage 1 is proven; latency and Kite budgets then matter.

## Consequences
- Prove correctness slow, add speed later and only where measured.
- Stage 2 is the only context in which a compiled hot path (ADR-0001) may be reconsidered.
