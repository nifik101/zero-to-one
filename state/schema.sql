-- zero-to-one V0 state schema
-- SQLite is the source of truth locally; JSON snapshots are committed mirrors.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS strategy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'abandoned', 'completed'))
);

CREATE TABLE IF NOT EXISTS experiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    strategy_id INTEGER REFERENCES strategy(id),
    hypothesis TEXT NOT NULL,
    method TEXT NOT NULL,
    success_criteria TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned', 'running', 'completed', 'failed', 'aborted'))
);

-- Append-only style action log (rows are never updated by tools).
CREATE TABLE IF NOT EXISTS action (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    experiment_id INTEGER REFERENCES experiment(id),
    kind TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    experiment_id INTEGER NOT NULL REFERENCES experiment(id),
    outcome TEXT NOT NULL,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    success INTEGER NOT NULL DEFAULT 0 CHECK (success IN (0, 1))
);

CREATE TABLE IF NOT EXISTS cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    experiment_id INTEGER REFERENCES experiment(id),
    amount_usd REAL NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    experiment_id INTEGER REFERENCES experiment(id),
    lesson TEXT NOT NULL
);

-- Simulated inbound wallet credits only (no outbound / chain integration in V0).
CREATE TABLE IF NOT EXISTS wallet_tx (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'in'
        CHECK (direction = 'in'),
    amount_usdc REAL NOT NULL,
    source_kind TEXT NOT NULL,
    counterparty TEXT NOT NULL DEFAULT '',
    memo TEXT NOT NULL DEFAULT '',
    external_ref TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    amount_usdc REAL NOT NULL,
    source_kind TEXT NOT NULL,
    counterparty TEXT NOT NULL DEFAULT '',
    proof_type TEXT NOT NULL,
    proof TEXT NOT NULL,
    wallet_tx_id INTEGER REFERENCES wallet_tx(id),
    verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
    rejection_reason TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);
