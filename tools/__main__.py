"""Dispatcher: uv run z21 <tool> ..."""

from __future__ import annotations

import sys

from tools import log_experiment, operator_inject_payment, publish, verify_revenue, wallet_balance

# Agent-facing tools. operator-inject-payment is operator/test-only (see AGENTS.md).
COMMANDS = {
    "wallet-balance": wallet_balance.main,
    "verify-revenue": verify_revenue.main,
    "log-experiment": log_experiment.main,
    "publish": publish.main,
    "operator-inject-payment": operator_inject_payment.main,
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        names = ", ".join(COMMANDS)
        print(f"usage: z21 {{{names}}}")
        print("note: operator-inject-payment is operator/test harness only — not for the agent")
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
