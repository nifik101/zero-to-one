"""Mock wallet: simulated inbound USDC credits only. No real chain access."""

from __future__ import annotations

import argparse
import json
import sys

from tools.runtime import connect, log_activity, now, persist, record_action, rows_to_dicts
from tools.verifier import ALLOWED_SOURCE_KINDS, DISALLOWED_SOURCE_KINDS

KNOWN_SOURCE_KINDS = sorted(ALLOWED_SOURCE_KINDS | DISALLOWED_SOURCE_KINDS)


def cmd_credit(args: argparse.Namespace) -> int:
    if args.amount <= 0:
        print("amount must be > 0", file=sys.stderr)
        log_activity("mock_wallet", "reject", {"reason": "non_positive_amount"}, status="error")
        return 2

    source_kind = args.source_kind.strip().lower()
    if source_kind not in KNOWN_SOURCE_KINDS:
        print(
            f"unknown source kind {source_kind!r}; expected one of {', '.join(KNOWN_SOURCE_KINDS)}",
            file=sys.stderr,
        )
        log_activity("mock_wallet", "reject", {"reason": "unknown_source"}, status="error")
        return 2

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO wallet_tx (
                created_at, direction, amount_usdc, source_kind, counterparty, memo, external_ref
            ) VALUES (?, 'in', ?, ?, ?, ?, ?)
            """,
            (
                now(),
                args.amount,
                source_kind,
                args.counterparty,
                args.memo,
                args.ref,
            ),
        )
        tx_id = int(cur.lastrowid)
        record_action(
            conn,
            "mock_wallet_credit",
            detail=f"inbound {args.amount} USDC from {source_kind}",
            payload={"wallet_tx_id": tx_id, "source_kind": source_kind},
        )
        persist(conn)

    payload = {
        "id": tx_id,
        "direction": "in",
        "amount_usdc": args.amount,
        "source_kind": source_kind,
        "counterparty": args.counterparty,
        "external_ref": args.ref,
    }
    log_activity("mock_wallet", "credit", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(
        "note: credit recorded in mock wallet only; "
        "run verify-revenue --wallet-tx-id "
        f"{tx_id} to submit for independent verification",
        file=sys.stderr,
    )
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    with connect() as conn:
        rows = rows_to_dicts(conn.execute("SELECT * FROM wallet_tx ORDER BY id").fetchall())
    log_activity("mock_wallet", "list", {"count": len(rows)})
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mock-wallet", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    credit = sub.add_parser("credit", help="simulate an inbound USDC credit")
    credit.add_argument("--amount", required=True, type=float)
    credit.add_argument(
        "--source-kind",
        required=True,
        help=f"one of: {', '.join(KNOWN_SOURCE_KINDS)}",
    )
    credit.add_argument("--counterparty", default="")
    credit.add_argument("--memo", default="")
    credit.add_argument("--ref", default="", help="external reference id for the mock tx")

    sub.add_parser("list", help="list mock wallet transactions")

    args = parser.parse_args(argv)
    if args.command == "credit":
        return cmd_credit(args)
    return cmd_list(args)


if __name__ == "__main__":
    raise SystemExit(main())
