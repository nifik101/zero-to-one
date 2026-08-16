"""Independent mission / revenue verifier.

The agent may submit claims. This module alone decides whether revenue
qualifies and whether the mission success condition is met. There is no
API here that lets a caller force `verified=1`.
"""

from __future__ import annotations

import sqlite3
from typing import Any

# Explicit non-qualifying sources (mission.md).
DISALLOWED_SOURCE_KINDS = frozenset(
    {
        "faucet",
        "self_payment",
        "giveaway",
        "circular",
        "operator",
    }
)

# Only independent third-party payments can qualify in V0.
ALLOWED_SOURCE_KINDS = frozenset({"third_party"})

TARGET_USDC = 1.0


def evaluate_claim(
    *,
    amount_usdc: float,
    source_kind: str,
    wallet_tx: dict[str, Any] | None,
) -> tuple[bool, str]:
    """Return (qualifies, reason). Qualifying claims may be marked verified."""
    if amount_usdc <= 0:
        return False, "non_positive_amount"

    kind = source_kind.strip().lower()
    if kind in DISALLOWED_SOURCE_KINDS:
        return False, f"disallowed_source:{kind}"
    if kind not in ALLOWED_SOURCE_KINDS:
        return False, f"unknown_source:{kind}"

    # V0: every verified dollar must be backed by a mock inbound wallet credit.
    if wallet_tx is None:
        return False, "missing_wallet_tx"

    if wallet_tx.get("direction") != "in":
        return False, "wallet_tx_not_inbound"

    tx_kind = str(wallet_tx.get("source_kind", "")).strip().lower()
    if tx_kind != kind:
        return False, "source_mismatch"

    try:
        tx_amount = float(wallet_tx["amount_usdc"])
    except (KeyError, TypeError, ValueError):
        return False, "invalid_wallet_tx_amount"

    if abs(tx_amount - float(amount_usdc)) > 1e-9:
        return False, "amount_mismatch"

    return True, "ok"


def verified_revenue_usdc(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_usdc), 0) FROM revenue WHERE verified = 1"
    ).fetchone()
    return float(row[0])


def pending_revenue_usdc(conn: sqlite3.Connection) -> float:
    # Rejected claims stay in the ledger but do not count as pending.
    row = conn.execute(
        """
        SELECT COALESCE(SUM(amount_usdc), 0) FROM revenue
        WHERE verified = 0 AND rejection_reason = ''
        """
    ).fetchone()
    return float(row[0])


def mission_status(conn: sqlite3.Connection) -> dict[str, Any]:
    verified = verified_revenue_usdc(conn)
    pending = pending_revenue_usdc(conn)
    complete = verified >= TARGET_USDC
    return {
        "verified_usdc": verified,
        "pending_usdc": pending,
        "target_usdc": TARGET_USDC,
        "remaining_usdc": max(TARGET_USDC - verified, 0.0),
        "mission_complete": complete,
        # Pending never satisfies the mission.
        "success_definition": "verified_usdc >= 1.00 from qualifying third_party revenue",
    }
