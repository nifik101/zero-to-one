"""Shared SQLite + JSON state and activity logging."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.accounting import accounting_snapshot, total_costs_usd
from tools.verifier import TARGET_USDC, mission_status, pending_revenue_usdc, verified_revenue_usdc

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state"
LOGS_DIR = ROOT / "logs"
PUBLISHED_DIR = LOGS_DIR / "published"
DB_PATH = STATE_DIR / "zero_to_one.db"
SCHEMA_PATH = STATE_DIR / "schema.sql"
ACTIVITY_LOG = LOGS_DIR / "activity.jsonl"

JSON_TABLES = (
    "strategy",
    "experiment",
    "action",
    "result",
    "cost",
    "lesson",
    "wallet_tx",
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


def log_activity(
    tool: str,
    action: str,
    payload: dict[str, Any] | None = None,
    status: str = "ok",
) -> None:
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


def record_action(
    conn: sqlite3.Connection,
    kind: str,
    detail: str = "",
    *,
    experiment_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO action (created_at, experiment_id, kind, detail, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            now(),
            experiment_id,
            kind,
            detail,
            json.dumps(payload or {}, ensure_ascii=False),
        ),
    )
    return int(cur.lastrowid)


def wallet_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    verified = verified_revenue_usdc(conn)
    pending = pending_revenue_usdc(conn)
    costs = total_costs_usd(conn)
    acct = accounting_snapshot(conn)
    mission = mission_status(conn)
    existing: dict[str, Any] = {}
    wallet_path = STATE_DIR / "wallet.json"
    if wallet_path.exists():
        existing = json.loads(wallet_path.read_text(encoding="utf-8"))
    return {
        "balance_usdc": verified,
        "pending_usdc": pending,
        "costs_usd": costs,
        "external_revenue_usdc": acct["external_revenue_usdc"],
        "variable_costs_usd": acct["variable_costs_usd"],
        "net_profit": acct["net_profit"],
        "target_usdc": TARGET_USDC,
        "mission_complete": mission["mission_complete"],
        "address": existing.get("address"),
        "chain": existing.get("chain"),
        "mode": "mock",
        "updated_at": now(),
    }


def export_json(conn: sqlite3.Connection) -> None:
    for table in JSON_TABLES:
        rows = rows_to_dicts(conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall())
        path = STATE_DIR / f"{table}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STATE_DIR / "wallet.json").write_text(
        json.dumps(wallet_snapshot(conn), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def persist(conn: sqlite3.Connection) -> None:
    conn.commit()
    export_json(conn)
