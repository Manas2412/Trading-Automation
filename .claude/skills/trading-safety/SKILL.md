---
name: trading-safety
description: Apply whenever writing or reviewing code on the order path (qtrade.execution / qtrade.risk) — order placement, sizing, position updates, or the kill-switch. Encodes qtrade's exactly-once and fail-closed invariants.
---
# Trading Safety

Use this checklist for any change that can place, size, or record an order, or touch the kill-switch.

## Invariants (must all hold)
1. **Exactly-once placement.** Derive `idempotency_key` deterministically from
   `(strategy_id, token, side, qty, decision_bar_ts)`. Claim it with
   `INSERT INTO "order" ... ON CONFLICT (idempotency_key) DO NOTHING` BEFORE calling the broker.
   If the row already existed, return the existing order — never resend.
2. **Risk gate first.** Call `RiskEngine.validate(order, ctx)` inside the placement transaction.
   Order: read kill-switch → check limits → claim idempotency row → send. No path skips this.
3. **Kill-switch is atomic and supreme.** Read `risk_state.kill_switch` in the same transaction.
   Tripped → reject. It overrides every strategy/model.
4. **Single-writer positions.** One authoritative writer; optimistic `version` locking; mutate
   `position` + `order`/`fill` in one transaction; per-token `pg_advisory_xact_lock`.
5. **Fail closed.** On timeout/unknown, set `UNKNOWN` and resolve via `get_order` — never blind-resend.
   On DB/broker uncertainty, halt and alert.
6. **Live guard.** Real orders only when `env=="live"` AND `live_trading_enabled`. Otherwise PaperBroker.
7. **Audit everything.** Persist the decision, order, and fill.

## Required tests for the change
- Duplicate intent (incl. across a simulated restart) → exactly one broker order.
- Kill-switch tripped → all `validate` calls reject; a mid-batch trip blocks the remainder.
- Concurrent position update → one wins, other retries, no lost update.
- No live credentials anywhere in tests.

## Red flags — stop and fix
- Broker called before the idempotency row is claimed.
- Any order path that can reach the broker without `validate`.
- Retvalue-ignoring resend on timeout. Bare float for cash. Hard-coded key or logged token.
