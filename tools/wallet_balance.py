"""Show verified / pending USDC, accounting, and mission status."""

from __future__ import annotations

import argparse
import json

from tools.runtime import connect, log_activity, wallet_snapshot
from tools.verifier import mission_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wallet-balance", description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    with connect() as conn:
        snap = wallet_snapshot(conn)
        mission = mission_status(conn)

    log_activity("wallet_balance", "read", {**snap, "mission": mission})

    if args.json:
        print(json.dumps({**snap, "mission": mission}, ensure_ascii=False, indent=2))
        return 0

    print(f"verified      {snap['balance_usdc']:.2f} USDC")
    print(f"pending       {snap['pending_usdc']:.2f} USDC")
    print(f"ext revenue   {snap['external_revenue_usdc']:.2f} USDC")
    print(f"var costs     {snap['variable_costs_usd']:.2f} USD")
    print(f"net profit    {snap['net_profit']:.2f}")
    print(f"target        {snap['target_usdc']:.2f} USDC")
    print(f"remaining     {mission['remaining_usdc']:.2f} USDC")
    print(f"mission       {'COMPLETE' if mission['mission_complete'] else 'incomplete'}")
    print(f"wallet mode   {snap['mode']}")
    if snap["address"]:
        print(f"address       {snap['address']} ({snap['chain'] or 'unknown chain'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
