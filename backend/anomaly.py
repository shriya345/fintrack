"""
Anomaly Detector — flags transactions that are unusually large.

Algorithm:
  For each category in the given month, compute the average transaction
  amount for that category across all other months (rolling baseline).
  If a single transaction > 2× that baseline average, it's anomalous.

  Fallback: if a category has no history (new user), use 1.5× the
  current month's own average for that category instead.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional

import models


ANOMALY_MULTIPLIER = 2.0  # Flag if transaction > N× baseline average


def detect_anomalies(
    db: Session,
    user_id: int,
    month: Optional[str] = None,   # "YYYY-MM"; if None, uses latest month
) -> List[Dict[str, Any]]:
    """
    Return a list of anomalous transactions for the user in the given month.
    Each item includes the transaction plus baseline_avg and multiplier fields.
    """
    # Determine the target month
    if month is None:
        latest = (
            db.query(func.max(models.Transaction.date))
            .filter(models.Transaction.user_id == user_id)
            .scalar()
        )
        if not latest:
            return []
        month = str(latest)[:7]  # "YYYY-MM"

    # Transactions in the target month
    target_txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            func.strftime("%Y-%m", models.Transaction.date) == month,
        )
        .all()
    )

    if not target_txns:
        return []

    # Baseline: historical average per category (all months EXCEPT the target)
    historical = (
        db.query(
            models.Transaction.category,
            func.avg(models.Transaction.amount).label("avg_amount"),
            func.count(models.Transaction.id).label("count"),
        )
        .filter(
            models.Transaction.user_id == user_id,
            func.strftime("%Y-%m", models.Transaction.date) != month,
        )
        .group_by(models.Transaction.category)
        .all()
    )
    baseline = {row.category: row.avg_amount for row in historical}

    # Fallback: current month average per category
    current_avgs: Dict[str, float] = {}
    current_counts: Dict[str, int] = {}
    for txn in target_txns:
        current_avgs[txn.category] = current_avgs.get(txn.category, 0) + txn.amount
        current_counts[txn.category] = current_counts.get(txn.category, 0) + 1
    for cat in current_avgs:
        current_avgs[cat] /= current_counts[cat]

    # Detect anomalies
    anomalies = []
    for txn in target_txns:
        avg = baseline.get(txn.category) or current_avgs.get(txn.category, txn.amount)
        if avg and txn.amount >= ANOMALY_MULTIPLIER * avg:
            anomalies.append({
                "id": txn.id,
                "date": str(txn.date),
                "description": txn.description,
                "category": txn.category,
                "amount": txn.amount,
                "baseline_avg": round(avg, 2),
                "multiplier": round(txn.amount / avg, 2),
            })

    # Sort by most extreme first
    return sorted(anomalies, key=lambda x: x["multiplier"], reverse=True)
