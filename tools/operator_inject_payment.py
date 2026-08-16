"""Operator/test harness: inject simulated inbound USDC payments.

NOT an agent tool. The autonomous agent must never invoke this command.
When the project goes live, this injector is replaced by a read-only chain source.
"""

from __future__ import annotations

import argparse
import json
import sys

from tools.runtime import connect, log_activity, now, persist, record_action
from tools.verifier import ALLOWED_SOURCE_KINDS, DISALLOWED_SOURCE_KINDS

KNOWN_SOURCE_KINDS = sorted(ALLOWED_SOURCE_KINDS | DISALLOWED_SOURCE_KINDS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="operator-inject-payment", description=__doc__)
    parser.add_argument("--amount", required=True, type=float)
    parser.add_argument(
        "--source-kind",
        required=True,
        help=f"one of: {', '.join(KNOWN_SOURCE_KINDS)}",
    )
    parser.add_argument("--counterparty", default="")
    parser.add_argument("--memo", default="")
    parser.add_argument("--ref", default="", help="external reference id for the mock tx")
    args = parser.parse_args(argv)

    if args.amount <= 0:
        print("amount must be > 0", file=sys.stderr)
        log_activity(
            "operator_inject_payment",
            "reject",
            {"reason": "non_positive_amount"},
            status="error",
        )
        return 2

    source_kind = args.source_kind.strip().lower()
    if source_kind not in KNOWN_SOURCE_KINDS:
        print(
            f"unknown source kind {source_kind!r}; expected one of {', '.join(KNOWN_SOURCE_KINDS)}",
            file=sys.stderr,
        )
        log_activity(
            "operator_inject_payment",
            "reject",
            {"reason": "unknown_source"},
            status="error",
        )
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
            "operator_inject_payment",
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
        "operator_only": True,
    }
    log_activity("operator_inject_payment", "inject", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(
        "operator injector: credit recorded; agent may run "
        f"verify-revenue --wallet-tx-id {tx_id}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
