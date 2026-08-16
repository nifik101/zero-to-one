"""Publish current scoreboard and a timestamped public snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.runtime import (
    PUBLISHED_DIR,
    ROOT,
    connect,
    log_activity,
    now,
    persist,
    rows_to_dicts,
    wallet_snapshot,
)
from tools.verifier import mission_status

PROGRESS_PATH = ROOT / "PROGRESS.md"


def render_progress(
    snap: dict,
    mission: dict,
    lessons: list[dict],
    experiments: list[dict],
) -> str:
    if mission["mission_complete"]:
        status = "done"
    elif experiments:
        status = "in progress"
    else:
        status = "not started"

    latest_lessons = lessons[-5:]
    lesson_lines = "\n".join(f"- {row['lesson']}" for row in latest_lessons) or "- _(none yet)_"
    exp_lines = "\n".join(
        f"- #{row['id']} `{row['status']}` — {row['hypothesis']}" for row in experiments[-8:]
    ) or "- _(none yet)_"
    blockers = ", ".join(mission.get("blockers") or []) or "_(none)_"

    return f"""# Progress

| | |
|---|---|
| Wallet balance | {snap['wallet_balance_usdc']:.2f} USDC |
| Verified revenue | **{snap['verified_revenue_usdc']:.2f} USDC** |
| Pending revenue | {snap['pending_revenue_usdc']:.2f} USDC |
| External revenue | {snap['external_revenue_usdc']:.2f} USDC |
| Operator spend | {snap['operator_funded_spend_usd']:.2f} USD |
| Variable costs | {snap['variable_costs_usd']:.2f} USD |
| Net profit | {snap['net_profit']:.2f} |
| Remaining | {mission['remaining_usdc']:.2f} USDC |
| Target | {snap['target_usdc']:.2f} USDC |
| Mission | {'complete' if mission['mission_complete'] else 'incomplete'} |
| Blockers | {blockers} |
| Status | {status} |
| Updated | {snap['updated_at']} |

## Experiments

{exp_lines}

## Latest lessons

{lesson_lines}

Updated by `uv run publish`. Manual edits of the numbers do not count.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="publish", description=__doc__)
    parser.add_argument("--note", default="", help="optional note attached to the snapshot")
    args = parser.parse_args(argv)

    with connect() as conn:
        persist(conn)
        snap = wallet_snapshot(conn)
        mission = mission_status(conn)
        lessons = rows_to_dicts(conn.execute("SELECT * FROM lesson ORDER BY id").fetchall())
        experiments = rows_to_dicts(conn.execute("SELECT * FROM experiment ORDER BY id").fetchall())

    body = render_progress(snap, mission, lessons, experiments)
    PROGRESS_PATH.write_text(body, encoding="utf-8")

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now().replace(":", "").replace("+00:00", "Z")
    snapshot: Path = PUBLISHED_DIR / f"{stamp}.md"
    extra = f"\n## Note\n\n{args.note}\n" if args.note else ""
    snapshot.write_text(body + extra, encoding="utf-8")

    payload = {
        "progress": str(PROGRESS_PATH.relative_to(ROOT)),
        "snapshot": str(snapshot.relative_to(ROOT)),
        "mission_complete": mission["mission_complete"],
    }
    log_activity("publish", "snapshot", payload)
    print(f"wrote {payload['progress']}")
    print(f"wrote {payload['snapshot']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
