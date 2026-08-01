# 0003 — TimescaleDB + Parquet/DuckDB for storage

**Status:** Accepted · 2026-08-01

## Context
Need time-series storage for candles/ticks with point-in-time correctness, plus fast analytical
access for research datasets.

## Decision
**TimescaleDB** (Postgres extension) as the operational time-series + reference store;
**Parquet files + DuckDB** for research datasets queried analytically.

## Consequences
- Familiar SQL/Postgres tooling; hypertables for scale.
- Research reads are cheap and reproducible from immutable Parquet snapshots.
- Single DB on the execution VM; research reads it read-mostly.
