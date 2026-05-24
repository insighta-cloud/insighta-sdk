"""Utility functions for Insighta SDK."""

import csv
from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal

import requests

from .models import CashDeposit, OrderGroup, RateEntry


def _parse_timestamp(val: str) -> int | None:
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
    """order.csv를 읽어서 group_dt별로 묶어 반환."""
    groups: OrderedDict[str, OrderGroup] = OrderedDict()
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gdt = row["group_dt"]
            rate_val = row.get("rate", "").strip() if row.get("rate") else ""
            if gdt not in groups:
                groups[gdt] = OrderGroup(
                    group_id=gdt,
                    currency=row.get("settle_currency", row["currency"]),
                    exchange_rate=float(rate_val) if rate_val else None,
                )
            groups[gdt].items.append({
                "id": row["ticker"],
                "ticker": row["ticker"],
                "quantity": float(row["quantity"]),
                "price": float(row["price"]),
                "currency": row["currency"],
                "price_type": row["price_type"],
                "timestamp": _parse_timestamp(row.get("timestamp", "")),
            })
    return list(groups.values())


def load_cash_deposits(filepath: str) -> dict[str, list[CashDeposit]]:
    """cash_deposits.csv를 읽어서 group_dt별로 묶어 반환."""
    groups: dict[str, list[CashDeposit]] = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gdt = row["group_dt"]
            groups.setdefault(gdt, []).append(CashDeposit(
                type=row["type"],
                amount=float(row["amount"]),
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
    """order + deposit을 group_dt 기준으로 머지하고 시간순 정렬."""
    existing_gdts = {g.group_id for g in orders}
    for gdt, deps in deposits_by_gdt.items():
        if gdt not in existing_gdts:
            cur = deps[0].currency or "USD"
            orders.append(OrderGroup(group_id=gdt, currency=cur))
    deps_map = dict(deposits_by_gdt)
    for g in orders:
        if g.group_id in deps_map:
            g.cash_deposits = deps_map[g.group_id]

    def _sort_key(g: OrderGroup):
        ts = _parse_timestamp(g.group_id)
        return ts if ts is not None else float("inf")
    orders.sort(key=_sort_key)
    for i, g in enumerate(orders, 1):
        g.group_id = str(i)
    for g in orders:
        if g.group_id in memos:
            g.memo = memos[g.group_id]
    return orders


def fetch_ticker_info(tickers: list[str]) -> dict[str, dict]:
    """Insighta /tickers/info API로 sector/industry/type 조회."""
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
    """為替レートCSVを読み込む。

    CSV format:
        from,to,pair,rate
        2024/01/01,2024/12/31,USD/JPY,155.50
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
    return val if " " in val else f"{val} 00:00"


def _normalize_dt_end(val: str) -> str:
    return val if " " in val else f"{val} 23:59"


def lookup_rate(entries: list[RateEntry], dt: str, cur: str, base: str) -> Decimal | None:
    """決済通貨と基準通貨が異なる場合のみ該当期間のレートを返す。"""
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
