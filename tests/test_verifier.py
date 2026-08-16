"""Tests for independent revenue verification and mission success."""

from __future__ import annotations

import unittest

from tools import log_experiment, verify_revenue
from tools.runtime import connect, wallet_snapshot
from tools.verifier import evaluate_claim, mission_status
from helpers import HarnessTestCase


class TestInvalidRevenue(HarnessTestCase):
    def test_disallowed_sources_do_not_verify(self) -> None:
        for kind in ("faucet", "self_payment", "giveaway", "circular", "operator"):
            with self.subTest(kind=kind):
                tx_id = self.inject(1.0, kind, counterparty="bad-actor")
                rc = verify_revenue.main(["--wallet-tx-id", str(tx_id)])
                self.assertEqual(rc, 0)
                with connect() as conn:
                    row = conn.execute(
                        "SELECT verified, rejection_reason FROM revenue WHERE wallet_tx_id = ?",
                        (tx_id,),
                    ).fetchone()
                    self.assertEqual(row["verified"], 0)
                    self.assertTrue(row["rejection_reason"].startswith("disallowed_source:"))
                    status = mission_status(conn)
                    self.assertFalse(status["mission_complete"])
                    self.assertEqual(status["verified_usdc"], 0.0)
                    self.assertEqual(status["pending_usdc"], 0.0)

    def test_claim_without_wallet_tx_fails_evaluate(self) -> None:
        ok, reason = evaluate_claim(
            amount_usdc=1.0,
            source_kind="third_party",
            wallet_tx=None,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "missing_wallet_tx")

    def test_agent_cannot_force_verification_via_cli(self) -> None:
        tx_id = self.inject(1.0, "third_party", counterparty="x")
        with self.assertRaises(SystemExit):
            verify_revenue.main(["--wallet-tx-id", str(tx_id), "--mark-verified"])


class TestQualifyingMockRevenue(HarnessTestCase):
    def test_third_party_credit_reaches_mission(self) -> None:
        tx_id = self.inject(
            1.0,
            "third_party",
            counterparty="independent-buyer",
            ref="mock-inv-1",
        )
        rc = verify_revenue.main(["--wallet-tx-id", str(tx_id), "--notes", "paid for digital good"])
        self.assertEqual(rc, 0)

        with connect() as conn:
            row = conn.execute("SELECT * FROM revenue WHERE id = 1").fetchone()
            self.assertEqual(row["verified"], 1)
            self.assertEqual(row["rejection_reason"], "")
            status = mission_status(conn)
            self.assertTrue(status["mission_complete"])
            self.assertGreaterEqual(status["verified_usdc"], 1.0)
            snap = wallet_snapshot(conn)
            self.assertEqual(snap["wallet_balance_usdc"], 1.0)
            self.assertEqual(snap["verified_revenue_usdc"], 1.0)
            self.assertEqual(snap["external_revenue_usdc"], 1.0)
            self.assertEqual(snap["net_profit"], 1.0)

    def test_partial_third_party_does_not_complete_mission(self) -> None:
        tx_id = self.inject(0.4, "third_party", counterparty="a")
        verify_revenue.main(["--wallet-tx-id", str(tx_id)])
        with connect() as conn:
            status = mission_status(conn)
            self.assertFalse(status["mission_complete"])
            self.assertAlmostEqual(status["verified_usdc"], 0.4)
            self.assertAlmostEqual(status["remaining_usdc"], 0.6)
            self.assertIn("verified_revenue_below_target", status["blockers"])

    def test_operator_spend_blocks_mission_despite_verified_revenue(self) -> None:
        tx_id = self.inject(1.0, "third_party", counterparty="buyer")
        verify_revenue.main(["--wallet-tx-id", str(tx_id)])
        log_experiment.main(
            [
                "cost",
                "--amount",
                "100",
                "--funding-source",
                "operator",
                "--description",
                "operator paid for ads",
            ]
        )
        with connect() as conn:
            status = mission_status(conn)
            snap = wallet_snapshot(conn)
            self.assertAlmostEqual(status["verified_usdc"], 1.0)
            self.assertAlmostEqual(status["operator_funded_spend_usd"], 100.0)
            self.assertFalse(status["mission_complete"])
            self.assertIn("operator_funded_spend_nonzero", status["blockers"])
            self.assertAlmostEqual(snap["net_profit"], -99.0)

    def test_wallet_balance_includes_unverified_credits(self) -> None:
        self.inject(5.0, "operator", counterparty="operator-wallet")
        with connect() as conn:
            snap = wallet_snapshot(conn)
            status = mission_status(conn)
        self.assertAlmostEqual(snap["wallet_balance_usdc"], 5.0)
        self.assertAlmostEqual(snap["verified_revenue_usdc"], 0.0)
        self.assertFalse(status["mission_complete"])


class TestExperimentConstraints(HarnessTestCase):
    def test_only_one_running_experiment(self) -> None:
        rc1 = log_experiment.main(
            ["start", "--hypothesis", "h1", "--method", "m1", "--success-criteria", "c1"]
        )
        self.assertEqual(rc1, 0)
        rc2 = log_experiment.main(
            ["start", "--hypothesis", "h2", "--method", "m2", "--success-criteria", "c2"]
        )
        self.assertEqual(rc2, 2)
        with connect() as conn:
            n = conn.execute(
                "SELECT COUNT(*) FROM experiment WHERE status = 'running'"
            ).fetchone()[0]
        self.assertEqual(n, 1)

    def test_only_one_active_strategy(self) -> None:
        log_experiment.main(
            ["strategy", "add", "--title", "first", "--content", "a"]
        )
        log_experiment.main(
            ["strategy", "add", "--title", "second", "--content", "b"]
        )
        with connect() as conn:
            active = conn.execute(
                "SELECT id, title FROM strategy WHERE status = 'active'"
            ).fetchall()
            paused = conn.execute(
                "SELECT id FROM strategy WHERE status = 'paused'"
            ).fetchall()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["title"], "second")
        self.assertEqual(len(paused), 1)


if __name__ == "__main__":
    unittest.main()
