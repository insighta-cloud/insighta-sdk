"""Utility functions for Insighta SDK."""

import csv
from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import requests

from .models import CashDeposit, OrderGroup, RateEntry


def _parse_timestamp(val: str) -> int | None:
    """Parse a timestamp string into Unix milliseconds.

    Args:
        val: A numeric string (ms) or datetime string.

    Returns:
        Unix timestamp in milliseconds, or None if unparseable.
    """
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return int(datetime.strptime(val, fmt).replace(tzinfo=timezone.utc).timestamp() * 1000)
        except ValueError:
            continue
    return None


def load_order_groups(filepath: str) -> list[OrderGroup]:
    """Parse an order CSV file into a list of OrderGroups.

    Groups rows by the ``group_dt`` column. Each unique group_dt
    becomes one OrderGroup with its associated order items.

    Args:
        filepath: Path to the order CSV file.

    Returns:
        List of OrderGroup instances ordered by appearance.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If required CSV columns are missing.
    """
    groups: OrderedDict[str, OrderGroup] = OrderedDict()
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gdt = row["group_dt"]
            rate_val = row.get("rate", "").strip() if row.get("rate") else ""
            if gdt not in groups:
                groups[gdt] = OrderGroup(
                    group_id=gdt,
                    currency=row.get("settle_currency", row["currency"]),
                    exchange_rate=Decimal(rate_val) if rate_val else None,
                )
            groups[gdt].items.append({
                "id": row["ticker"],
                "ticker": row["ticker"],
                "quantity": Decimal(row["quantity"]),
                "price": Decimal(row["price"]),
                "currency": row["currency"],
                "price_type": row["price_type"],
                "timestamp": _parse_timestamp(row.get("timestamp", "")),
            })
    return list(groups.values())


def load_cash_deposits(filepath: str) -> dict[str, list[CashDeposit]]:
    """Parse a cash deposits CSV file grouped by order group datetime.

    Args:
        filepath: Path to the cash_deposits CSV file.

    Returns:
        Dict mapping group_dt strings to lists of CashDeposit instances.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If required CSV columns are missing.
    """
    groups: dict[str, list[CashDeposit]] = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gdt = row["group_dt"]
            groups.setdefault(gdt, []).append(CashDeposit(
                type=row["type"],
                amount=Decimal(row["amount"]),
                currency=row.get("currency") or None,
                ticker=row.get("ticker") or None,
                timestamp=_parse_timestamp(row.get("timestamp", "")),
            ))
    return groups


def merge_and_sort_groups(
    orders: list[OrderGroup],
    deposits_by_gdt: dict[str, list[CashDeposit]],
    memos: dict[str, str],
) -> list[OrderGroup]:
    """Merge order groups with deposits and memos, then sort chronologically.

    Groups are re-numbered sequentially (1, 2, 3, ...) after sorting.

    Args:
        orders: List of OrderGroup instances from order CSV.
        deposits_by_gdt: Cash deposits keyed by group_dt.
        memos: Memo strings keyed by sequential group ID.

    Returns:
        Merged and sorted list of OrderGroup instances.
    """
    existing_gdts = {g.group_id for g in orders}
    for gdt, deps in deposits_by_gdt.items():
        if gdt not in existing_gdts:
            cur = deps[0].currency or "USD"
            orders.append(OrderGroup(group_id=gdt, currency=cur))
    deps_map = dict(deposits_by_gdt)
    for g in orders:
        if g.group_id in deps_map:
            g.cash_deposits = deps_map[g.group_id]

    def _sort_key(g: OrderGroup) -> float:
        ts = _parse_timestamp(g.group_id)
        return float(ts) if ts is not None else float("inf")
    orders.sort(key=_sort_key)
    for i, g in enumerate(orders, 1):
        g.group_id = str(i)
    for g in orders:
        if g.group_id in memos:
            g.memo = memos[g.group_id]
    return orders


def fetch_ticker_info(tickers: list[str]) -> dict[str, Any]:
    """Query ticker metadata (sector, industry, type) from the Insighta API.

    Args:
        tickers: List of ticker symbols to look up.

    Returns:
        Dict mapping tickers to their metadata.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status.
    """
    if not tickers:
        return {}
    resp = requests.get(
        "https://api.insighta.cloud/tickers/info",
        params={"tickers": ",".join(tickers), "conditions": "sector,industry,type"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def load_rate_file(filepath: str) -> list[RateEntry]:
    """Load exchange rate entries from a CSV file.

    CSV format::

        from,to,pair,rate
        2024/01/01,2024/12/31,USD/JPY,155.50

    Args:
        filepath: Path to the rate CSV file.

    Returns:
        List of RateEntry instances.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    entries: list[RateEntry] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            entries.append(RateEntry(
                start=row["from"].strip(),
                end=row["to"].strip(),
                pair=row["pair"].strip(),
                rate=Decimal(row["rate"].strip()),
            ))
    return entries


def _normalize_dt(val: str) -> str:
    """Normalize a date string to include time component.

    Args:
        val: Date or datetime string.

    Returns:
        String with time appended as "00:00" if missing.
    """
    return val if " " in val else f"{val} 00:00"


def _normalize_dt_end(val: str) -> str:
    """Normalize a date string to end-of-day time.

    Args:
        val: Date or datetime string.

    Returns:
        String with time appended as "23:59" if missing.
    """
    return val if " " in val else f"{val} 23:59"


def lookup_rate(entries: list[RateEntry], dt: str, cur: str, base: str) -> Decimal | None:
    """Find the applicable exchange rate for a trade.

    Returns None if settlement currency equals base currency (no conversion needed).

    Args:
        entries: List of RateEntry instances to search.
        dt: Trade datetime string (ISO 8601).
        cur: Settlement currency code.
        base: Ticker's base currency code.

    Returns:
        The matching exchange rate, or None if not applicable/found.
    """
    if cur == base:
        return None
    trade_dt = dt[:16].replace("-", "/").replace("T", " ") if dt else ""
    pair = f"{base}/{cur}"
    for e in entries:
        start = _normalize_dt(e.start)
        end = _normalize_dt_end(e.end)
        if e.pair == pair and start <= trade_dt <= end:
            return e.rate
    return None
