"""Cost and profit accounting helpers."""

from __future__ import annotations

import sqlite3
from typing import Any

from tools.verifier import verified_revenue_usdc

FUNDING_SOURCES = frozenset({"earned_capital", "operator", "experiment_infrastructure"})


def costs_by_funding_source(conn: sqlite3.Connection) -> dict[str, float]:
    rows = conn.execute(
        """
        SELECT funding_source, COALESCE(SUM(amount_usd), 0) AS total
        FROM cost
        GROUP BY funding_source
        """
    ).fetchall()
    totals = {name: 0.0 for name in FUNDING_SOURCES}
    for row in rows:
        totals[str(row["funding_source"])] = float(row["total"])
    return totals


def total_costs_usd(conn: sqlite3.Connection) -> float:
    """All recorded costs (including experiment_infrastructure)."""
    row = conn.execute("SELECT COALESCE(SUM(amount_usd), 0) FROM cost").fetchone()
    return float(row[0])


def accounting_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    """External revenue, costs by funding source, and net profit.

    V0 treats 1 USDC ≈ 1 USD for net profit. Verified revenue only.
    experiment_infrastructure is reported but excluded from mission variable costs.
    """
    by_source = costs_by_funding_source(conn)
    external_revenue_usdc = verified_revenue_usdc(conn)
    # Mission economy: earned capital + operator spend (infrastructure excluded).
    variable_costs_usd = by_source["earned_capital"] + by_source["operator"]
    net_profit = external_revenue_usdc - variable_costs_usd
    return {
        "external_revenue_usdc": external_revenue_usdc,
        "earned_capital_spend_usd": by_source["earned_capital"],
        "operator_funded_spend_usd": by_source["operator"],
        "experiment_infrastructure_spend_usd": by_source["experiment_infrastructure"],
        "variable_costs_usd": variable_costs_usd,
        "total_costs_usd": total_costs_usd(conn),
        "net_profit": net_profit,
    }
