"""Dispatcher: uv run z21 <tool> ..."""

from __future__ import annotations

import sys

from tools import log_experiment, mock_wallet, publish, verify_revenue, wallet_balance

COMMANDS = {
    "wallet-balance": wallet_balance.main,
    "verify-revenue": verify_revenue.main,
    "log-experiment": log_experiment.main,
    "mock-wallet": mock_wallet.main,
    "publish": publish.main,
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        names = ", ".join(COMMANDS)
        print(f"usage: z21 {{{names}}}")
        return 0
    command = args[0]
    if command not in COMMANDS:
        print(f"unknown tool: {command}", file=sys.stderr)
        return 2
    sys.argv = [f"z21 {command}", *args[1:]]
    result = COMMANDS[command]()
    return 0 if result is None else int(result)


if __name__ == "__main__":
    raise SystemExit(main())
