"""Persistence and resume behavior."""

from __future__ import annotations

import json
import unittest

from tools import log_experiment, mock_wallet, verify_revenue
from tools import runtime
from tools.runtime import connect, wallet_snapshot
from tools.verifier import mission_status
from helpers import HarnessTestCase


class TestPersistenceResume(HarnessTestCase):
    def test_state_survives_reconnect(self) -> None:
        log_experiment.main(
            [
                "strategy",
                "add",
                "--title",
                "digital good",
                "--content",
                "sell a small useful artifact for USDC",
            ]
        )
        log_experiment.main(
            [
                "start",
                "--hypothesis",
                "someone will pay 1 USDC",
                "--method",
                "publish offer on free channel",
                "--success-criteria",
                "verified >= 1",
                "--strategy-id",
                "1",
            ]
        )
        log_experiment.main(
            ["action", "--kind", "publish_offer", "--detail", "posted offer", "--experiment-id", "1"]
        )
        mock_wallet.main(
            [
                "credit",
                "--amount",
                "1.0",
                "--source-kind",
                "third_party",
                "--counterparty",
                "buyer-9",
            ]
        )
        with connect() as conn:
            tx_id = conn.execute("SELECT id FROM wallet_tx").fetchone()[0]
        verify_revenue.main(["--wallet-tx-id", str(tx_id)])

        self.assertTrue(runtime.DB_PATH.exists())
        self.assertTrue(runtime.ACTIVITY_LOG.exists())

        # Simulate a new process: reopen DB and read prior state (no conversation context).
        with connect() as conn:
            experiments = conn.execute("SELECT * FROM experiment").fetchall()
            actions = conn.execute("SELECT * FROM action ORDER BY id").fetchall()
            revenue = conn.execute("SELECT * FROM revenue").fetchall()
            status = mission_status(conn)
            snap = wallet_snapshot(conn)

        self.assertEqual(len(experiments), 1)
        self.assertEqual(experiments[0]["status"], "running")
        self.assertGreaterEqual(len(actions), 2)
        self.assertEqual(len(revenue), 1)
        self.assertEqual(revenue[0]["verified"], 1)
        self.assertTrue(status["mission_complete"])
        self.assertTrue(snap["mission_complete"])

        # JSON mirrors exist for resume/inspection without SQLite tools.
        exp_json = json.loads((self.state / "experiment.json").read_text(encoding="utf-8"))
        self.assertEqual(exp_json[0]["hypothesis"], "someone will pay 1 USDC")
        wallet_json = json.loads((self.state / "wallet.json").read_text(encoding="utf-8"))
        self.assertEqual(wallet_json["balance_usdc"], 1.0)

    def test_activity_log_is_append_only_jsonl(self) -> None:
        log_experiment.main(
            ["start", "--hypothesis", "h1", "--method", "m1", "--success-criteria", "c1"]
        )
        log_experiment.main(
            ["start", "--hypothesis", "h2", "--method", "m2", "--success-criteria", "c2"]
        )
        lines = runtime.ACTIVITY_LOG.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(lines), 2)
        for line in lines:
            event = json.loads(line)
            self.assertIn("ts", event)
            self.assertIn("tool", event)
            self.assertIn("action", event)

    def test_duplicate_claim_rejected(self) -> None:
        mock_wallet.main(
            ["credit", "--amount", "1.0", "--source-kind", "third_party", "--counterparty", "z"]
        )
        with connect() as conn:
            tx_id = conn.execute("SELECT id FROM wallet_tx").fetchone()[0]
        self.assertEqual(verify_revenue.main(["--wallet-tx-id", str(tx_id)]), 0)
        self.assertEqual(verify_revenue.main(["--wallet-tx-id", str(tx_id)]), 2)


class TestAccounting(HarnessTestCase):
    def test_net_profit_subtracts_costs(self) -> None:
        mock_wallet.main(
            ["credit", "--amount", "1.0", "--source-kind", "third_party", "--counterparty", "c"]
        )
        with connect() as conn:
            tx_id = conn.execute("SELECT id FROM wallet_tx").fetchone()[0]
        verify_revenue.main(["--wallet-tx-id", str(tx_id)])
        log_experiment.main(
            ["cost", "--amount", "0.25", "--description", "variable packaging (hypothetical)"]
        )
        with connect() as conn:
            snap = wallet_snapshot(conn)
        self.assertAlmostEqual(snap["external_revenue_usdc"], 1.0)
        self.assertAlmostEqual(snap["variable_costs_usd"], 0.25)
        self.assertAlmostEqual(snap["net_profit"], 0.75)


if __name__ == "__main__":
    unittest.main()
