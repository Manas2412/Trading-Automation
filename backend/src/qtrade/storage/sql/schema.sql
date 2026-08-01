-- qtrade storage schema (TimescaleDB / PostgreSQL).
-- Apply against a database with the TimescaleDB extension available.
-- Mirrors docs/LLD.md sec 4. Money as NUMERIC; timestamps as TIMESTAMPTZ (UTC).

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ---------- reference ----------
CREATE TABLE IF NOT EXISTS instrument (
    token        BIGINT PRIMARY KEY,
    symbol       TEXT    NOT NULL,
    exchange     TEXT    NOT NULL,
    asset_class  TEXT    NOT NULL,
    lot_size     INT     NOT NULL DEFAULT 1,
    tick_size    NUMERIC NOT NULL,
    active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------- time series (hypertables) ----------
CREATE TABLE IF NOT EXISTS bar (
    token    BIGINT      NOT NULL,
    interval TEXT        NOT NULL,
    ts       TIMESTAMPTZ NOT NULL,
    open     NUMERIC     NOT NULL,
    high     NUMERIC     NOT NULL,
    low      NUMERIC     NOT NULL,
    close    NUMERIC     NOT NULL,
    volume   BIGINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (token, interval, ts)
);
SELECT create_hypertable('bar', 'ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS bar_token_interval_ts_idx ON bar (token, interval, ts DESC);

CREATE TABLE IF NOT EXISTS corporate_action (
    token   BIGINT  NOT NULL,
    ex_date DATE    NOT NULL,
    kind    TEXT    NOT NULL,          -- SPLIT | BONUS | DIVIDEND | ...
    ratio   NUMERIC,
    PRIMARY KEY (token, ex_date, kind)
);

-- LLM news/sentiment FEATURE (upstream only; never a trade trigger)
CREATE TABLE IF NOT EXISTS news_feature (
    id         BIGSERIAL PRIMARY KEY,
    token      BIGINT,
    ts         TIMESTAMPTZ NOT NULL,
    sentiment  NUMERIC,
    event_type TEXT,
    source     TEXT,
    raw_ref    TEXT
);
CREATE INDEX IF NOT EXISTS news_feature_token_ts_idx ON news_feature (token, ts DESC);

-- ---------- trading state ----------
CREATE TABLE IF NOT EXISTS signal (
    token           BIGINT NOT NULL,
    ts              TIMESTAMPTZ NOT NULL,
    strategy_id     TEXT NOT NULL,
    expected_return DOUBLE PRECISION,
    confidence      DOUBLE PRECISION,
    horizon_days    DOUBLE PRECISION,
    rationale       TEXT,
    PRIMARY KEY (token, ts, strategy_id)
);

CREATE TABLE IF NOT EXISTS "order" (
    idempotency_key TEXT PRIMARY KEY,      -- exactly-once guard (LLD sec 7.1)
    broker_order_id TEXT UNIQUE,
    token           BIGINT NOT NULL,
    side            TEXT   NOT NULL,
    qty             INT    NOT NULL,
    order_type      TEXT   NOT NULL,
    limit_price     NUMERIC,
    strategy_id     TEXT   NOT NULL,
    state           TEXT   NOT NULL,
    filled_qty      INT    NOT NULL DEFAULT 0,
    avg_price       NUMERIC,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fill (
    id              BIGSERIAL PRIMARY KEY,
    broker_order_id TEXT REFERENCES "order"(broker_order_id),
    token           BIGINT NOT NULL,
    side            TEXT   NOT NULL,
    qty             INT    NOT NULL,
    price           NUMERIC NOT NULL,
    fee             NUMERIC NOT NULL DEFAULT 0,
    ts              TIMESTAMPTZ NOT NULL
);

-- single source of truth: one row per token, optimistic version lock (LLD sec 7.2)
CREATE TABLE IF NOT EXISTS position (
    token        BIGINT PRIMARY KEY,
    qty          INT     NOT NULL,
    avg_price    NUMERIC NOT NULL,
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    version      BIGINT  NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- singleton (id = 1): the atomic kill-switch (LLD sec 7.4)
CREATE TABLE IF NOT EXISTS risk_state (
    id               INT PRIMARY KEY DEFAULT 1,
    kill_switch      BOOLEAN NOT NULL DEFAULT FALSE,
    reason           TEXT,
    day_start_equity NUMERIC,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT risk_state_singleton CHECK (id = 1)
);
INSERT INTO risk_state (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

-- append-only audit trail (every decision, order, fill)
CREATE TABLE IF NOT EXISTS audit_log (
    id      BIGSERIAL PRIMARY KEY,
    ts      TIMESTAMPTZ NOT NULL DEFAULT now(),
    kind    TEXT NOT NULL,
    payload JSONB NOT NULL
);
