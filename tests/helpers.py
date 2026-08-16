"""Shared test helpers: isolated SQLite + logs under a temp directory."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import tools.runtime as runtime


class HarnessTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="z21-")
        self.root = Path(self._tmpdir)
        self.state = self.root / "state"
        self.logs = self.root / "logs"
        self.state.mkdir()
        self.logs.mkdir()

        schema_src = Path(__file__).resolve().parents[1] / "state" / "schema.sql"
        shutil.copy(schema_src, self.state / "schema.sql")
        (self.state / "wallet.json").write_text(
            json.dumps(
                {
                    "wallet_balance_usdc": 0.0,
                    "verified_revenue_usdc": 0.0,
                    "pending_revenue_usdc": 0.0,
                    "external_revenue_usdc": 0.0,
                    "earned_capital_spend_usd": 0.0,
                    "operator_funded_spend_usd": 0.0,
                    "experiment_infrastructure_spend_usd": 0.0,
                    "variable_costs_usd": 0.0,
                    "total_costs_usd": 0.0,
                    "net_profit": 0.0,
                    "target_usdc": 1.0,
                    "mission_complete": False,
                    "address": None,
                    "chain": None,
                    "mode": "mock",
                    "updated_at": None,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        self._orig = {
            "ROOT": runtime.ROOT,
            "STATE_DIR": runtime.STATE_DIR,
            "LOGS_DIR": runtime.LOGS_DIR,
            "PUBLISHED_DIR": runtime.PUBLISHED_DIR,
            "DB_PATH": runtime.DB_PATH,
            "SCHEMA_PATH": runtime.SCHEMA_PATH,
            "ACTIVITY_LOG": runtime.ACTIVITY_LOG,
        }
        runtime.ROOT = self.root
        runtime.STATE_DIR = self.state
        runtime.LOGS_DIR = self.logs
        runtime.PUBLISHED_DIR = self.logs / "published"
        runtime.DB_PATH = self.state / "zero_to_one.db"
        runtime.SCHEMA_PATH = self.state / "schema.sql"
        runtime.ACTIVITY_LOG = self.logs / "activity.jsonl"

    def tearDown(self) -> None:
        for key, value in self._orig.items():
            setattr(runtime, key, value)
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def inject(
        self,
        amount: float,
        source_kind: str,
        counterparty: str = "fixture",
        ref: str = "",
    ) -> int:
        from tools import operator_inject_payment

        rc = operator_inject_payment.main(
            [
                "--amount",
                str(amount),
                "--source-kind",
                source_kind,
                "--counterparty",
                counterparty,
                "--ref",
                ref,
            ]
        )
        self.assertEqual(rc, 0)
        from tools.runtime import connect

        with connect() as conn:
            return int(conn.execute("SELECT MAX(id) FROM wallet_tx").fetchone()[0])
