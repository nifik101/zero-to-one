"""Tests for independent revenue verification and mission success."""

from __future__ import annotations

import unittest

from tools import mock_wallet, verify_revenue
from tools.runtime import connect, wallet_snapshot
from tools.verifier import evaluate_claim, mission_status
from helpers import HarnessTestCase


class TestInvalidRevenue(HarnessTestCase):
    def test_disallowed_sources_do_not_verify(self) -> None:
        for kind in ("faucet", "self_payment", "giveaway", "circular", "operator"):
            with self.subTest(kind=kind):
                rc = mock_wallet.main(
                    [
                        "credit",
                        "--amount",
                        "1.0",
                        "--source-kind",
                        kind,
                        "--counterparty",
                        "bad-actor",
                    ]
                )
                self.assertEqual(rc, 0)
                with connect() as conn:
                    tx_id = conn.execute("SELECT MAX(id) FROM wallet_tx").fetchone()[0]
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
        # There must be no --mark-verified (or similar) escape hatch.
        mock_wallet.main(
            ["credit", "--amount", "1.0", "--source-kind", "third_party", "--counterparty", "x"]
        )
        with connect() as conn:
            tx_id = conn.execute("SELECT MAX(id) FROM wallet_tx").fetchone()[0]
        with self.assertRaises(SystemExit):
            verify_revenue.main(["--wallet-tx-id", str(tx_id), "--mark-verified"])


class TestQualifyingMockRevenue(HarnessTestCase):
    def test_third_party_credit_reaches_mission(self) -> None:
        rc = mock_wallet.main(
            [
                "credit",
                "--amount",
                "1.0",
                "--source-kind",
                "third_party",
                "--counterparty",
                "independent-buyer",
                "--ref",
                "mock-inv-1",
            ]
        )
        self.assertEqual(rc, 0)
        with connect() as conn:
            tx_id = conn.execute("SELECT id FROM wallet_tx").fetchone()[0]

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
            self.assertEqual(snap["external_revenue_usdc"], 1.0)
            self.assertEqual(snap["net_profit"], 1.0)

    def test_partial_third_party_does_not_complete_mission(self) -> None:
        mock_wallet.main(
            ["credit", "--amount", "0.4", "--source-kind", "third_party", "--counterparty", "a"]
        )
        with connect() as conn:
            tx_id = conn.execute("SELECT id FROM wallet_tx").fetchone()[0]
        verify_revenue.main(["--wallet-tx-id", str(tx_id)])
        with connect() as conn:
            status = mission_status(conn)
            self.assertFalse(status["mission_complete"])
            self.assertAlmostEqual(status["verified_usdc"], 0.4)
            self.assertAlmostEqual(status["remaining_usdc"], 0.6)


if __name__ == "__main__":
    unittest.main()
