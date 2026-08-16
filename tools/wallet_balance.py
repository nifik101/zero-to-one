"""Show wallet balance, verified/pending revenue, accounting, and mission status.

Read-only observation surface for the agent. Does not inject payments.
"""

from __future__ import annotations

import argparse
import json

from tools.runtime import connect, log_activity, rows_to_dicts, wallet_snapshot
from tools.verifier import mission_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wallet-balance", description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--txs",
        action="store_true",
        help="also list inbound wallet transactions (read-only)",
    )
    args = parser.parse_args(argv)

    with connect() as conn:
        snap = wallet_snapshot(conn)
        mission = mission_status(conn)
        txs = []
        if args.txs or args.json:
            txs = rows_to_dicts(conn.execute("SELECT * FROM wallet_tx ORDER BY id").fetchall())

    log_activity("wallet_balance", "read", {**snap, "mission": mission})

    if args.json:
        print(json.dumps({**snap, "mission": mission, "wallet_txs": txs}, ensure_ascii=False, indent=2))
        return 0

    print(f"wallet        {snap['wallet_balance_usdc']:.2f} USDC")
    print(f"verified rev  {snap['verified_revenue_usdc']:.2f} USDC")
    print(f"pending rev   {snap['pending_revenue_usdc']:.2f} USDC")
    print(f"ext revenue   {snap['external_revenue_usdc']:.2f} USDC")
    print(f"op. spend     {snap['operator_funded_spend_usd']:.2f} USD")
    print(f"earned spend  {snap['earned_capital_spend_usd']:.2f} USD")
    print(f"infra spend   {snap['experiment_infrastructure_spend_usd']:.2f} USD")
    print(f"var costs     {snap['variable_costs_usd']:.2f} USD")
    print(f"net profit    {snap['net_profit']:.2f}")
    print(f"target        {snap['target_usdc']:.2f} USDC")
    print(f"remaining     {mission['remaining_usdc']:.2f} USDC")
    print(f"mission       {'COMPLETE' if mission['mission_complete'] else 'incomplete'}")
    if mission["blockers"]:
        print(f"blockers      {', '.join(mission['blockers'])}")
    print(f"wallet mode   {snap['mode']}")
    if snap["address"]:
        print(f"address       {snap['address']} ({snap['chain'] or 'unknown chain'})")
    if args.txs:
        print(f"wallet txs    {len(txs)}")
        for tx in txs:
            print(
                f"  #{tx['id']} {tx['amount_usdc']} USDC "
                f"{tx['source_kind']} from {tx['counterparty'] or '?'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
