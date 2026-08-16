# zero-to-one

Autonomous agent experiment: **$0 → 1 USDC**.

No starting capital. No operator-funded spend. Revenue counts only when it is verified.

- Law: [`AGENTS.md`](AGENTS.md)
- Goal: [`mission.md`](mission.md)
- Scoreboard: [`PROGRESS.md`](PROGRESS.md)

## Layout

```
zero-to-one/
├── AGENTS.md          # rules, mission, forbidden actions
├── mission.md         # $0 → 1 USDC
├── PROGRESS.md        # public scoreboard
├── state/             # SQLite locally, JSON committed
├── tools/             # wallet_balance, verify_revenue, log_experiment, publish
├── workspace/         # agent-created work
└── logs/              # activity log + published snapshots
```

## Tools

```bash
uv sync
uv run wallet-balance
uv run log-experiment --help
uv run verify-revenue --help
uv run publish
```

Same commands via `uv run z21 <tool>`.

## State

`state/zero_to_one.db` is local SQLite (gitignored). JSON files in `state/` are the committed snapshot: strategy, experiments, results, costs, lessons.
