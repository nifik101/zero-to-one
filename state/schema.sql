-- zero-to-one state schema
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

CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    amount_usdc REAL NOT NULL,
    proof_type TEXT NOT NULL,
    proof TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
    notes TEXT NOT NULL DEFAULT ''
);
