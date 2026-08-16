"""Show verified / pending USDC against the 1 USDC target."""

from __future__ import annotations

import argparse
import json

from tools.runtime import connect, log_activity, wallet_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wallet-balance", description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    with connect() as conn:
        snap = wallet_snapshot(conn)

    log_activity("wallet_balance", "read", snap)

    if args.json:
        print(json.dumps(snap, ensure_ascii=False, indent=2))
        return 0

    print(f"verified   {snap['balance_usdc']:.2f} USDC")
    print(f"pending    {snap['pending_usdc']:.2f} USDC")
    print(f"costs      {snap['costs_usd']:.2f} USD")
    print(f"target     {snap['target_usdc']:.2f} USDC")
    remaining = max(snap["target_usdc"] - snap["balance_usdc"], 0.0)
    print(f"remaining  {remaining:.2f} USDC")
    if snap["address"]:
        print(f"address    {snap['address']} ({snap['chain'] or 'unknown chain'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
