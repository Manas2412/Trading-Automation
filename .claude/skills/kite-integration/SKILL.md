---
name: kite-integration
description: Apply when writing or reviewing any Zerodha Kite Connect integration in qtrade — auth/token flow, historical/live data, order placement, or reconciliation. Encodes compliance and rate-budget rules.
---
# Kite Connect Integration

All broker access goes through the `BrokerPort` interface; `KiteBroker` is the only place `kiteconnect`
is imported. Tests and dev/paper use `PaperBroker`.

## Compliance (SEBI retail algo framework)
- Orders only via the registered Kite API — never scraping or headless login.
- Run from the **whitelisted static IP**; apply **algo order tagging**; keep order frequency well under
  algo-registration thresholds in Stage 1.
- Personal use only — no strategy distribution.

## Auth & secrets
- API key/secret from config (`.env`/vault); access token generated via the daily login flow and stored
  locally (git-ignored). NEVER log the access token or hard-code keys.

## Rate & reliability
- Guard every call with the token-bucket limiter (per-second) and the persisted daily counter.
  Near the daily budget, defer non-urgent calls and alert — do not error-loop.
- Wrap the live WebSocket with reconnect + backoff; on reconnect, run reconciliation before acting.
- Map Kite params ↔ canonical models in the adapter only; the rest of the system stays broker-agnostic.

## Reconciliation
- On startup and end-of-run, compare broker orders/positions to the DB. Resolve UNKNOWN orders by
  querying Kite (`get_order`) — never by resending. On mismatch, halt and alert.

## Verify current values (don't assume)
- Kite per-second and daily request/order limits, and charge constants, change over time — confirm
  against current Kite docs before relying on specific numbers.
