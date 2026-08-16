# state/

Source of truth for strategy, experiments, actions, results, costs, lessons,
mock wallet credits, and revenue claims.

| File | Role |
|---|---|
| `schema.sql` | SQLite schema |
| `zero_to_one.db` | local database (gitignored) |
| `strategy.json` | snapshot |
| `experiment.json` | snapshot |
| `action.json` | snapshot (append-only ledger rows) |
| `result.json` | snapshot |
| `cost.json` | snapshot |
| `lesson.json` | snapshot |
| `wallet_tx.json` | mock inbound credits |
| `revenue.json` | claims + verifier outcomes |
| `wallet.json` | balances, net profit, mission flag |

JSON is updated by the tools. Do not hand-edit “wins”.
