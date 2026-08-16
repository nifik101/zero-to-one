# state/

Source of truth for strategy, experiments, actions, results, costs, lessons,
wallet credits, and revenue claims.

| File | Role |
|---|---|
| `schema.sql` | SQLite schema |
| `zero_to_one.db` | local database (gitignored) |
| `strategy.json` | snapshot (at most one `active`) |
| `experiment.json` | snapshot (at most one `running`) |
| `action.json` | snapshot (append-only ledger rows) |
| `result.json` | snapshot |
| `cost.json` | snapshot (includes `funding_source`) |
| `lesson.json` | snapshot |
| `wallet_tx.json` | inbound credits (written by operator injector) |
| `revenue.json` | claims + verifier outcomes |
| `wallet.json` | wallet balance vs verified/pending revenue, mission flag |

JSON is updated by the tools. Do not hand-edit “wins”.
