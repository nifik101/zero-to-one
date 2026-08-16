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

PROGRESS_PATH = ROOT / "PROGRESS.md"


def render_progress(snap: dict, lessons: list[dict], experiments: list[dict]) -> str:
    remaining = max(snap["target_usdc"] - snap["balance_usdc"], 0.0)
    if snap["balance_usdc"] >= snap["target_usdc"]:
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

    return f"""# Progress

| | |
|---|---|
| Verified | **{snap['balance_usdc']:.2f} USDC** |
| Pending | {snap['pending_usdc']:.2f} USDC |
| Costs | {snap['costs_usd']:.2f} USD |
| Remaining | {remaining:.2f} USDC |
| Target | {snap['target_usdc']:.2f} USDC |
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
        lessons = rows_to_dicts(conn.execute("SELECT * FROM lesson ORDER BY id").fetchall())
        experiments = rows_to_dicts(conn.execute("SELECT * FROM experiment ORDER BY id").fetchall())

    body = render_progress(snap, lessons, experiments)
    PROGRESS_PATH.write_text(body, encoding="utf-8")

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now().replace(":", "").replace("+00:00", "Z")
    snapshot: Path = PUBLISHED_DIR / f"{stamp}.md"
    extra = f"\n## Note\n\n{args.note}\n" if args.note else ""
    snapshot.write_text(body + extra, encoding="utf-8")

    payload = {"progress": str(PROGRESS_PATH.relative_to(ROOT)), "snapshot": str(snapshot.relative_to(ROOT))}
    log_activity("publish", "snapshot", payload)
    print(f"wrote {payload['progress']}")
    print(f"wrote {payload['snapshot']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
