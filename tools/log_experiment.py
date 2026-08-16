"""Log strategy, experiments, results, costs, and lessons."""

from __future__ import annotations

import argparse
import json
import sys

from tools.runtime import connect, log_activity, now, persist, rows_to_dicts


def cmd_strategy(args: argparse.Namespace) -> int:
    with connect() as conn:
        if args.strategy_command == "list":
            rows = rows_to_dicts(conn.execute("SELECT * FROM strategy ORDER BY id").fetchall())
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            log_activity("log_experiment", "strategy_list", {"count": len(rows)})
            return 0
        if not args.title or not args.content:
            print("strategy add requires --title and --content", file=sys.stderr)
            return 2
        ts = now()
        cur = conn.execute(
            """
            INSERT INTO strategy (created_at, updated_at, title, content, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (ts, ts, args.title, args.content),
        )
        persist(conn)
        payload = {"id": cur.lastrowid, "title": args.title}
        log_activity("log_experiment", "strategy_add", payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    ts = now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO experiment (
                created_at, updated_at, strategy_id, hypothesis, method, success_criteria, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'running')
            """,
            (ts, ts, args.strategy_id, args.hypothesis, args.method, args.success_criteria or ""),
        )
        persist(conn)
        payload = {"id": cur.lastrowid, "status": "running"}
        log_activity("log_experiment", "start", payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_finish(args: argparse.Namespace, status: str) -> int:
    ts = now()
    success = 1 if status == "completed" and args.success else 0
    with connect() as conn:
        exists = conn.execute("SELECT id FROM experiment WHERE id = ?", (args.id,)).fetchone()
        if exists is None:
            print(f"experiment {args.id} not found", file=sys.stderr)
            log_activity("log_experiment", "missing", {"id": args.id}, status="error")
            return 2
        conn.execute(
            "UPDATE experiment SET status = ?, updated_at = ? WHERE id = ?",
            (status, ts, args.id),
        )
        conn.execute(
            """
            INSERT INTO result (created_at, experiment_id, outcome, metrics_json, success)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ts, args.id, args.outcome, args.metrics or "{}", success),
        )
        persist(conn)
        payload = {"id": args.id, "status": status, "success": bool(success)}
        log_activity("log_experiment", status, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_cost(args: argparse.Namespace) -> int:
    if args.amount < 0:
        print("cost amount must be >= 0", file=sys.stderr)
        return 2
    if args.amount > 0:
        print(
            "warning: mission cost cap is 0 USD of operator funds — record only if already incurred",
            file=sys.stderr,
        )
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO cost (created_at, experiment_id, amount_usd, description)
            VALUES (?, ?, ?, ?)
            """,
            (now(), args.experiment_id, args.amount, args.description),
        )
        persist(conn)
        payload = {"id": cur.lastrowid, "amount_usd": args.amount}
        log_activity("log_experiment", "cost", payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_lesson(args: argparse.Namespace) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO lesson (created_at, experiment_id, lesson)
            VALUES (?, ?, ?)
            """,
            (now(), args.experiment_id, args.text),
        )
        persist(conn)
        payload = {"id": cur.lastrowid}
        log_activity("log_experiment", "lesson", payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    with connect() as conn:
        if args.what == "experiments":
            rows = rows_to_dicts(conn.execute("SELECT * FROM experiment ORDER BY id").fetchall())
        elif args.what == "results":
            rows = rows_to_dicts(conn.execute("SELECT * FROM result ORDER BY id").fetchall())
        elif args.what == "costs":
            rows = rows_to_dicts(conn.execute("SELECT * FROM cost ORDER BY id").fetchall())
        else:
            rows = rows_to_dicts(conn.execute("SELECT * FROM lesson ORDER BY id").fetchall())
    log_activity("log_experiment", "list", {"what": args.what, "count": len(rows)})
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="log-experiment", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    strategy = sub.add_parser("strategy", help="add or list strategies")
    strategy.add_argument("strategy_command", choices=("add", "list"))
    strategy.add_argument("--title")
    strategy.add_argument("--content")

    start = sub.add_parser("start", help="open a running experiment")
    start.add_argument("--hypothesis", required=True)
    start.add_argument("--method", required=True)
    start.add_argument("--success-criteria", dest="success_criteria", default="")
    start.add_argument("--strategy-id", dest="strategy_id", type=int)

    complete = sub.add_parser("complete", help="close experiment as completed")
    complete.add_argument("--id", required=True, type=int)
    complete.add_argument("--outcome", required=True)
    complete.add_argument("--metrics")
    complete.add_argument("--success", action="store_true")

    fail = sub.add_parser("fail", help="close experiment as failed")
    fail.add_argument("--id", required=True, type=int)
    fail.add_argument("--outcome", required=True)
    fail.add_argument("--metrics")

    cost = sub.add_parser("cost", help="record a cost (cap is 0 operator USD)")
    cost.add_argument("--amount", required=True, type=float)
    cost.add_argument("--description", required=True)
    cost.add_argument("--experiment-id", dest="experiment_id", type=int)

    lesson = sub.add_parser("lesson", help="record a lesson")
    lesson.add_argument("--text", required=True)
    lesson.add_argument("--experiment-id", dest="experiment_id", type=int)

    listing = sub.add_parser("list", help="list experiments, results, costs, or lessons")
    listing.add_argument(
        "what",
        nargs="?",
        default="experiments",
        choices=("experiments", "results", "costs", "lessons"),
    )

    args = parser.parse_args(argv)
    if args.command == "strategy":
        return cmd_strategy(args)
    if args.command == "start":
        return cmd_start(args)
    if args.command == "complete":
        return cmd_finish(args, "completed")
    if args.command == "fail":
        args.success = False
        return cmd_finish(args, "failed")
    if args.command == "cost":
        return cmd_cost(args)
    if args.command == "lesson":
        return cmd_lesson(args)
    return cmd_list(args)


if __name__ == "__main__":
    raise SystemExit(main())
