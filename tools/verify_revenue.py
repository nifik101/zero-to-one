"""Submit revenue claims for independent verification.

The agent cannot mark revenue verified. Qualification is decided by
`tools.verifier` against mission rules and a backing mock wallet credit.
"""

from __future__ import annotations

import argparse
import json
import sys

from tools.runtime import connect, log_activity, now, persist, record_action, wallet_snapshot
from tools.verifier import evaluate_claim


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify-revenue", description=__doc__)
    parser.add_argument(
        "--wallet-tx-id",
        required=True,
        type=int,
        help="id of a mock inbound wallet credit to claim as revenue",
    )
    parser.add_argument("--notes", default="")
    args = parser.parse_args(argv)

    with connect() as conn:
        tx = conn.execute(
            "SELECT * FROM wallet_tx WHERE id = ?",
            (args.wallet_tx_id,),
        ).fetchone()
        if tx is None:
            print(f"wallet_tx {args.wallet_tx_id} not found", file=sys.stderr)
            log_activity(
                "verify_revenue",
                "reject",
                {"reason": "missing_wallet_tx", "wallet_tx_id": args.wallet_tx_id},
                status="error",
            )
            return 2

        tx_dict = dict(tx)
        existing = conn.execute(
            "SELECT id FROM revenue WHERE wallet_tx_id = ?",
            (args.wallet_tx_id,),
        ).fetchone()
        if existing is not None:
            print(
                f"wallet_tx {args.wallet_tx_id} already claimed as revenue id {existing['id']}",
                file=sys.stderr,
            )
            log_activity(
                "verify_revenue",
                "reject",
                {"reason": "already_claimed", "wallet_tx_id": args.wallet_tx_id},
                status="error",
            )
            return 2

        qualifies, reason = evaluate_claim(
            amount_usdc=float(tx_dict["amount_usdc"]),
            source_kind=str(tx_dict["source_kind"]),
            wallet_tx=tx_dict,
        )
        verified = 1 if qualifies else 0
        rejection = "" if qualifies else reason

        cur = conn.execute(
            """
            INSERT INTO revenue (
                created_at, amount_usdc, source_kind, counterparty,
                proof_type, proof, wallet_tx_id, verified, rejection_reason, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                float(tx_dict["amount_usdc"]),
                str(tx_dict["source_kind"]),
                str(tx_dict["counterparty"]),
                "mock_wallet_tx",
                f"wallet_tx:{args.wallet_tx_id}",
                args.wallet_tx_id,
                verified,
                rejection,
                args.notes,
            ),
        )
        revenue_id = int(cur.lastrowid)
        record_action(
            conn,
            "verify_revenue",
            detail=reason,
            payload={
                "revenue_id": revenue_id,
                "wallet_tx_id": args.wallet_tx_id,
                "verified": bool(verified),
                "reason": reason,
            },
        )
        persist(conn)
        snap = wallet_snapshot(conn)

    payload = {
        "id": revenue_id,
        "amount_usdc": float(tx_dict["amount_usdc"]),
        "source_kind": str(tx_dict["source_kind"]),
        "verified": bool(verified),
        "rejection_reason": rejection,
        "wallet_tx_id": args.wallet_tx_id,
        "mission_complete": snap["mission_complete"],
    }
    log_activity("verify_revenue", "evaluate", payload, status="ok" if verified else "rejected")
    print(json.dumps({**payload, "wallet": snap}, ensure_ascii=False, indent=2))
    if not verified:
        print(f"rejected — does not count toward mission ({rejection})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
