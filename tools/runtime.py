"""Shared SQLite + JSON state and activity logging."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state"
LOGS_DIR = ROOT / "logs"
PUBLISHED_DIR = LOGS_DIR / "published"
DB_PATH = STATE_DIR / "zero_to_one.db"
SCHEMA_PATH = STATE_DIR / "schema.sql"
ACTIVITY_LOG = LOGS_DIR / "activity.jsonl"
TARGET_USDC = 1.0

JSON_TABLES = (
    "strategy",
    "experiment",
    "result",
    "cost",
    "lesson",
    "revenue",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def log_activity(tool: str, action: str, payload: dict[str, Any] | None = None, status: str = "ok") -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": now(),
        "tool": tool,
        "action": action,
        "status": status,
        "payload": payload or {},
    }
    with ACTIVITY_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def export_json(conn: sqlite3.Connection) -> None:
    for table in JSON_TABLES:
        rows = rows_to_dicts(conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall())
        path = STATE_DIR / f"{table}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STATE_DIR / "wallet.json").write_text(
        json.dumps(wallet_snapshot(conn), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def wallet_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    verified = conn.execute(
        "SELECT COALESCE(SUM(amount_usdc), 0) FROM revenue WHERE verified = 1"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COALESCE(SUM(amount_usdc), 0) FROM revenue WHERE verified = 0"
    ).fetchone()[0]
    costs = conn.execute("SELECT COALESCE(SUM(amount_usd), 0) FROM cost").fetchone()[0]
    existing: dict[str, Any] = {}
    wallet_path = STATE_DIR / "wallet.json"
    if wallet_path.exists():
        existing = json.loads(wallet_path.read_text(encoding="utf-8"))
    return {
        "balance_usdc": float(verified),
        "pending_usdc": float(pending),
        "costs_usd": float(costs),
        "target_usdc": TARGET_USDC,
        "address": existing.get("address"),
        "chain": existing.get("chain"),
        "updated_at": now(),
    }


def persist(conn: sqlite3.Connection) -> None:
    conn.commit()
    export_json(conn)
