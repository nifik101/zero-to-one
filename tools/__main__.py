"""Dispatcher: uv run z21 <tool> ...

Agent-facing tool surface only. Operator/test payment injection is a separate
entry point: `uv run operator-inject-payment` (see pyproject.toml).
"""

from __future__ import annotations

import sys

from tools import log_experiment, publish, verify_revenue, wallet_balance

COMMANDS = {
    "wallet-balance": wallet_balance.main,
    "verify-revenue": verify_revenue.main,
    "log-experiment": log_experiment.main,
    "publish": publish.main,
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        names = ", ".join(COMMANDS)
        print(f"usage: z21 {{{names}}}")
        return 0
    command = args[0]
    if command == "operator-inject-payment":
        print(
            "operator-inject-payment is not part of z21; "
            "run: uv run operator-inject-payment ...",
            file=sys.stderr,
        )
        return 2
    if command not in COMMANDS:
        print(f"unknown tool: {command}", file=sys.stderr)
        return 2
    sys.argv = [f"z21 {command}", *args[1:]]
    result = COMMANDS[command]()
    return 0 if result is None else int(result)


if __name__ == "__main__":
    raise SystemExit(main())
