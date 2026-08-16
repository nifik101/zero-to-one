"""Cost and profit accounting helpers."""

from __future__ import annotations

import sqlite3
from typing import Any

from tools.verifier import verified_revenue_usdc


def total_costs_usd(conn: sqlite3.Connection) -> float:
    row = conn.execute("SELECT COALESCE(SUM(amount_usd), 0) FROM cost").fetchone()
    return float(row[0])


def accounting_snapshot(conn: sqlite3.Connection) -> dict[str, Any]:
    """External revenue, variable costs, and net profit in USDC/USD terms.

    V0 treats 1 USDC ≈ 1 USD for net profit. Verified revenue only.
    """
    external_revenue_usdc = verified_revenue_usdc(conn)
    variable_costs_usd = total_costs_usd(conn)
    net_profit = external_revenue_usdc - variable_costs_usd
    return {
        "external_revenue_usdc": external_revenue_usdc,
        "variable_costs_usd": variable_costs_usd,
        "net_profit": net_profit,
    }
