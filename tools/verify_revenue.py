"""Register revenue. Nothing counts as verified without proof."""

from __future__ import annotations

import argparse
import json
import re
import sys

from tools.runtime import connect, log_activity, now, persist, wallet_snapshot

TX_HASH = re.compile(r"^0x[a-fA-F0-9]{64}$")
SOL_SIG = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,88}$")


def proof_looks_valid(proof_type: str, proof: str) -> bool:
    proof = proof.strip()
    if not proof:
        return False
    if proof_type == "tx_hash":
        return bool(TX_HASH.match(proof) or SOL_SIG.match(proof))
    if proof_type == "address_credit":
        return len(proof) >= 8
    return len(proof) >= 8


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verify-revenue", description=__doc__)
    parser.add_argument("--amount", required=True, type=float, help="amount in USDC")
    parser.add_argument("--proof", required=True, help="tx hash, receipt id, or equivalent")
    parser.add_argument(
        "--proof-type",
        default="tx_hash",
        choices=("tx_hash", "address_credit", "other"),
    )
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--mark-verified",
        action="store_true",
        help="operator-attested: proof already checked on-chain/off-platform",
    )
    args = parser.parse_args(argv)

    if args.amount <= 0:
        print("amount must be > 0", file=sys.stderr)
        log_activity("verify_revenue", "reject", {"reason": "non_positive_amount"}, status="error")
        return 2

    looks_ok = proof_looks_valid(args.proof_type, args.proof)
    verified = 1 if (args.mark_verified and looks_ok) else 0
    if args.mark_verified and not looks_ok:
        print("proof does not look valid; refusing to mark verified", file=sys.stderr)
        log_activity(
            "verify_revenue",
            "reject",
            {"reason": "invalid_proof", "proof_type": args.proof_type},
            status="error",
        )
        return 2

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO revenue (created_at, amount_usdc, proof_type, proof, verified, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (now(), args.amount, args.proof_type, args.proof.strip(), verified, args.notes),
        )
        persist(conn)
        snap = wallet_snapshot(conn)
        revenue_id = cur.lastrowid

    payload = {
        "id": revenue_id,
        "amount_usdc": args.amount,
        "verified": bool(verified),
        "proof_type": args.proof_type,
    }
    log_activity("verify_revenue", "record", payload)
    print(json.dumps({**payload, "wallet": snap}, ensure_ascii=False, indent=2))
    if not verified:
        print("recorded as pending — not counted until verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
