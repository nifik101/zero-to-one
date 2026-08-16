# zero-to-one (V0)

Minimal experiment harness for autonomous economic agency.

**Goal (future live runs):** go from **$0 → 1 USDC** of verified external revenue.  
**V0 scope:** infrastructure only — **do not earn real money yet**, and do not touch real wallets or credentials.

- Law: [`AGENTS.md`](AGENTS.md)
- Mission: [`mission.md`](mission.md)
- Scoreboard: [`PROGRESS.md`](PROGRESS.md)

## Architecture

```
zero-to-one/
├── AGENTS.md           # operating law + safety boundaries
├── mission.md          # success / failure definition
├── PROGRESS.md         # published scoreboard
├── state/              # SQLite (local) + JSON snapshots (committed)
│   ├── schema.sql
│   ├── zero_to_one.db  # gitignored
│   └── *.json
├── tools/              # CLI tools (stdlib only)
│   ├── runtime.py      # DB, JSON export, activity log
│   ├── verifier.py     # independent qualification + mission check
│   ├── accounting.py   # revenue, costs, net profit
│   ├── mock_wallet.py  # simulated inbound credits
│   ├── verify_revenue.py
│   ├── wallet_balance.py
│   ├── log_experiment.py
│   └── publish.py
├── logs/               # append-only activity.jsonl + published/
├── workspace/          # agent-created artifacts
└── tests/              # verifier, accounting, resume tests
```

**Data flow**

1. Agent logs strategy / experiment / actions via `log-experiment`.
2. Inbound value is recorded with `mock-wallet credit` (simulated only).
3. `verify-revenue --wallet-tx-id N` submits that credit to the **independent verifier**.
4. Verifier accepts only `third_party` sources backed by the mock credit; rejects faucets, self-payments, giveaways, circular, and operator funds.
5. `wallet-balance` reports balances, costs, net profit, and `mission_complete`.
6. `publish` writes `PROGRESS.md` and a timestamped snapshot under `logs/published/`.

SQLite is the resumable source of truth. JSON mirrors under `state/` exist for inspection and git-friendly snapshots.

## Setup

Requires Python ≥ 3.12 and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

No third-party Python dependencies are required for the harness itself.

## Commands

```bash
uv run wallet-balance
uv run mock-wallet credit --amount 1.0 --source-kind third_party --counterparty alice
uv run verify-revenue --wallet-tx-id 1
uv run log-experiment strategy add --title "..." --content "..."
uv run log-experiment start --hypothesis "..." --method "..." --success-criteria "..."
uv run log-experiment action --kind "..." --detail "..."
uv run log-experiment complete --id 1 --outcome "..." --success
uv run log-experiment cost --amount 0 --description "..."
uv run log-experiment lesson --text "..."
uv run publish
uv run z21 <tool> ...          # same tools via dispatcher
```

Tests:

```bash
uv run python -m unittest discover -s tests -v
```

## How V0 works

| Concern | Mechanism |
|---|---|
| Persistent state | SQLite (`state/zero_to_one.db`) + JSON mirrors |
| Experiment ledger | `experiment`, `action`, `result`, `lesson` tables; `logs/activity.jsonl` |
| Cost accounting | `cost` rows → variable costs; verified revenue − costs = net profit |
| Mock wallet | `wallet_tx` inbound rows only (`mock-wallet`) |
| Independent verifier | `tools/verifier.py` — agent cannot force `verified=1` |
| Resumability | Re-open DB; read strategy/experiments/wallet; continue |
| Structured logs | JSONL events with `ts`, `tool`, `action`, `status`, `payload` |

### Qualifying vs invalid revenue

Invalid source kinds never satisfy the mission: `faucet`, `self_payment`, `giveaway`, `circular`, `operator`.

Only `third_party` credits that pass verification count toward the 1 USDC target.

## What intentionally does NOT exist yet

- Real crypto / blockchain libraries or chain RPC
- Real wallet keys, exchanges, or payment processors
- Communication / outreach channels beyond what you build in `workspace/`
- Docker, queues, microservices, web dashboards, frontends
- Multi-agent orchestration or a general-purpose agent framework
- Automatic “earn money” loops — V0 is the harness only

## State notes

- Do not hand-edit JSON/SQLite to invent verified revenue.
- If the schema changes during development, delete `state/zero_to_one.db` and let tools recreate it from `schema.sql`.
- `PROGRESS.md` numbers are only authoritative when produced by `publish` from verifier-backed state.
