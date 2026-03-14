"""
CSV Parser — normalizes statements from HDFC, ICICI, SBI, Axis Bank.

Each bank uses different column names and date formats.
This module detects the format and produces a unified list of dicts:
  [{ "date": "YYYY-MM-DD", "description": str, "amount": float }]
"""

import pandas as pd
import re
from datetime import datetime
from typing import IO, List, Dict, Any


# ─── Column name aliases per bank ─────────────────────────────────────────────

DESCRIPTION_ALIASES = [
    "narration", "description", "transaction details",
    "particulars", "remarks", "txn description", "details",
]

AMOUNT_ALIASES = [
    "withdrawal amt.", "debit amount", "amount (inr)",
    "debit", "withdrawal", "amount", "txn amount",
]

DATE_ALIASES = [
    "value dt", "date", "txn date", "transaction date",
    "posting date", "value date",
]

# Common date formats across Indian banks
DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y",
    "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d",
    "%d %B %Y",
]


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_csv(file_obj: IO[str]) -> List[Dict[str, Any]]:
    """
    Parse a bank statement CSV from a file-like object.
    Returns a list of unified transaction dicts.
    """
    try:
        # Try reading with header detection (skip leading bank-header rows)
        raw = file_obj.read()
        lines = raw.splitlines()
        header_row = _find_header_row(lines)
        df = pd.read_csv(
            pd.io.common.StringIO("\n".join(lines[header_row:])),
            skip_blank_lines=True,
        )
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")

    # Normalize column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    date_col = _find_col(df, DATE_ALIASES)
    desc_col = _find_col(df, DESCRIPTION_ALIASES)
    amount_col = _find_col(df, AMOUNT_ALIASES)

    if not all([date_col, desc_col, amount_col]):
        raise ValueError(
            f"Could not detect required columns. Found: {list(df.columns)}"
        )

    transactions = []
    for _, row in df.iterrows():
        try:
            amount = _parse_amount(str(row[amount_col]))
            if amount <= 0:
                continue  # Skip credits / zero rows

            date = _parse_date(str(row[date_col]))
            if date is None:
                continue

            desc = str(row[desc_col]).strip()
            if not desc or desc.lower() in ("nan", ""):
                continue

            transactions.append({
                "date": date,
                "description": desc,
                "amount": round(amount, 2),
            })
        except Exception:
            continue  # Skip malformed rows

    return transactions


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _find_header_row(lines: List[str]) -> int:
    """Find the row index containing the actual CSV header."""
    for i, line in enumerate(lines[:20]):
        lower = line.lower()
        # If the line contains at least 2 known column name hints → it's the header
        hits = sum(alias in lower for alias in DATE_ALIASES + DESCRIPTION_ALIASES + AMOUNT_ALIASES)
        if hits >= 2:
            return i
    return 0  # Fall back to first row


def _find_col(df: pd.DataFrame, aliases: List[str]) -> str | None:
    """Return the first column name that matches any alias."""
    for alias in aliases:
        for col in df.columns:
            if alias in col:
                return col
    return None


def _parse_amount(raw: str) -> float:
    """Strip currency symbols, commas, parentheses and parse as float."""
    cleaned = re.sub(r"[₹$,\s]", "", raw)
    cleaned = cleaned.replace("(", "-").replace(")", "")
    try:
        return abs(float(cleaned))
    except ValueError:
        return 0.0


def _parse_date(raw: str) -> str | None:
    """Try all known date formats and return ISO date string."""
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None
