# 0006 — src layout with package `qtrade`

**Status:** Accepted · 2026-08-01

## Context
Want import-safe packaging, clear separation of source from tests/tooling, and one package per
architecture layer.

## Decision
Use a **`src/` layout** with a single installable package **`qtrade`**, sub-packages mapping to the
seven layers (`data`, `storage`, `signals`, `risk`, `backtest`, `execution`, `ops`) plus `common` and `llm`.

## Consequences
- `pip install -e .` for development; tests run against the installed package.
- Clear module boundaries that mirror the HLD.
