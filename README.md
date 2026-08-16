# zero-to-one (V0)

Minimal experiment harness for autonomous economic agency.

**Goal (future live runs):** go from **$0 → 1 USDC** of verified external revenue with **zero operator-funded spend**.  
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
│   ├── runtime.py
│   ├── verifier.py
│   ├── accounting.py
│   ├── operator_inject_payment.py  # OPERATOR/TEST ONLY
│   ├── verify_revenue.py
│   ├── wallet_balance.py
│   ├── log_experiment.py
│   └── publish.py
├── logs/
├── workspace/
└── tests/
```

**Data flow**

1. Agent logs strategy / experiment / actions via `log-experiment` (one running experiment; one active strategy).
2. **Operator/test harness** may inject a simulated inbound credit with `operator-inject-payment` (agent must never do this).
3. Agent observes via `wallet-balance` / `--txs`.
4. Agent runs `verify-revenue --wallet-tx-id N` on an existing credit.
5. Verifier accepts only `third_party` sources; mission also requires `operator_funded_spend_usd == 0`.
6. `publish` writes `PROGRESS.md` and a timestamped snapshot.

SQLite is the resumable source of truth. JSON mirrors under `state/` are inspection aids.

## Setup

Requires Python ≥ 3.12 and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

No third-party Python dependencies are required for the harness itself.

## Commands

Agent-facing:

```bash
uv run wallet-balance
uv run wallet-balance --txs
uv run verify-revenue --wallet-tx-id 1
uv run log-experiment strategy add --title "..." --content "..."
uv run log-experiment start --hypothesis "..." --method "..." --success-criteria "..."
uv run log-experiment action --kind "..." --detail "..."
uv run log-experiment complete --id 1 --outcome "..." --success
uv run log-experiment cost --amount 0 --funding-source earned_capital --description "..."
uv run log-experiment lesson --text "..."
uv run publish
```

Operator / test harness only:

```bash
uv run operator-inject-payment --amount 1.0 --source-kind third_party --counterparty alice
```

Tests:

```bash
uv run python -m unittest discover -s tests -v
```

## How V0 works

| Concern | Mechanism |
|---|---|
| Persistent state | SQLite + JSON mirrors |
| One running experiment | Partial unique index + CLI check |
| One active strategy | Partial unique index; new strategy pauses the previous |
| Cost funding | `earned_capital` / `operator` / `experiment_infrastructure` |
| Mission gate | `verified >= 1` **and** `operator_funded_spend == 0` |
| Wallet vs revenue | `wallet_balance_usdc` ≠ `verified_revenue_usdc` |
| Payment injection | `operator-inject-payment` only (not agent) |
| Independent verifier | `tools/verifier.py` — no force-verify flag |
| Duplicate claims | `revenue.wallet_tx_id` is `UNIQUE` |

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
