# 0005 — LLM restricted to feature generation (never in the trigger path)

**Status:** Accepted · 2026-08-01

## Context
The system must be mathematically sound, not a chatbot wrapper. LLM output is useful for parsing
news/filings but is non-deterministic and unsuitable for decisions.

## Decision
The LLM produces only **features** (calibrated sentiment/event scores) stored upstream of the math.
Signals, sizing, risk, and execution are deterministic, tested code. No model may size a position or
place an order from free-form text.

## Consequences
- Decisions are reproducible and testable.
- News features are backtested like any other factor and discarded if they add no edge.
