# Mission: $0 → 1 USDC

Machine-oriented mission definition for zero-to-one.

```yaml
mission_id: zero-to-one
version: v0
start_capital_usd: 0
start_capital_usdc: 0
operator_credit_allowed: false
target_asset: USDC
target_amount: 1.00
success_metric: verified_qualifying_usdc
verifier: tools.verifier.mission_status
wallet_mode_v0: mock
```

## Objective

Start with **zero working capital** and earn at least **1.00 USDC** of **legitimate external revenue** from an **independent third party**.

Revenue that is not approved by the independent verifier counts as **0**.

## Success

Success when all of the following are true:

1. `verified_usdc >= 1.00`
2. Every counted dollar has `source_kind = third_party`
3. Each counted claim is backed by an inbound wallet credit (mock in V0; real later)
4. `tools.verifier.mission_status(...).mission_complete is true`

Pending claims do **not** count. Agent self-declaration does **not** count.

## Failure / non-success

Any of the following means the mission is **not** complete:

- Verified qualifying balance remains below 1.00 USDC
- Revenue is only pending / rejected
- The only “income” is from disallowed sources (below)
- State was hand-edited to look successful without verifier approval
- Operator funds, loans, or credits were used as the economic engine

Stopping for safety, legality, or cost-cap reasons is a controlled halt, not a win.

## What counts as external revenue

**Counts (qualifying):**

- Payment in USDC (or equivalent settled as USDC) from an independent third party
- In V0: a `mock-wallet credit` with `--source-kind third_party` that `verify-revenue` accepts

**Does not count:**

| Kind | Examples |
|---|---|
| `faucet` | Testnet faucets, promo faucets, free claim sites |
| `self_payment` | Paying yourself from another wallet you control |
| `giveaway` | Contests, airdrops-as-giveaway, charity tipped to self |
| `circular` | Wash loops, same value cycling between related parties |
| `operator` | Operator transfers, reimbursements, “here’s 1 USDC to win” |

Also never counts: likes, stars, promises, fabricated receipts, balances on accounts you do not control, or anything that requires the operator to spend money to create the “revenue.”

## Constraints

- No starting capital.
- No paid ads, paid APIs, or purchases funded by the operator (live mission cost cap = 0).
- No crime or deception. See `AGENTS.md`.
- Time is allowed. Operator money is not.

## Strategy

Unknown. The agent must *find* a path, not assume one.

Allowed directions (high level):

- Create something someone wants and charge USDC
- Perform work for USDC on free surfaces
- Publish and sell digital value without capital outlay

Forbidden directions: anything that breaks `AGENTS.md`.

## Definition of done (compact)

```
verified_usdc >= 1.00
source_kind == third_party for all counted revenue
pending does not count
faucet | self_payment | giveaway | circular | operator do not count
mission_complete == true  # from independent verifier only
```

When true: log the lesson, run `publish`, stop the mission.
