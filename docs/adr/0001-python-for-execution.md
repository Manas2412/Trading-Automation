# 0001 — Python for research, ML, and execution

**Status:** Accepted · 2026-08-01

## Context
Instinct says execution should be C++ "because it's fast." At our frequency, orders go through the
Kite Connect API; the round-trip to broker/exchange (tens–hundreds of ms) dominates and is outside
our control. A compiled language would save microseconds invisible behind that round-trip, while
forcing a reimplementation of the official `pykiteconnect` client — more code and more bugs in the
one place bugs cost real money.

## Decision
Use **Python** for research, ML, and execution. Reserve a compiled language (prefer **Rust** over
C++ for memory safety) for a *specific, measured* hot path only — realistically not before Stage 2
tick-level intraday, if ever.

## Consequences
- One language across the stack; the official Kite client is used directly.
- Latency budget spent where it matters (broker round-trip), not on language micro-optimization.
- Revisit only when a profiler shows an in-process bottleneck at Stage 2.
