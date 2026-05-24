"""Tests for insighta_sdk.utils."""

import csv
import os
from decimal import Decimal

import pytest

from insighta_sdk.models import CashDeposit, OrderGroup, RateEntry
from insighta_sdk.utils import (
    _parse_timestamp,
    load_cash_deposits,
    load_order_groups,
    load_rate_file,
    lookup_rate,
    merge_and_sort_groups,
)


class TestParseTimestamp:
    def test_integer_string(self):
        assert _parse_timestamp("1700000000000") == 1700000000000

    def test_datetime_string(self):
        ts = _parse_timestamp("2024-01-01 00:00:00")
        assert ts == 1704067200000

    def test_empty(self):
        assert _parse_timestamp("") is None

    def test_invalid(self):
        assert _parse_timestamp("not-a-date") is None


class TestLoadRateFile:
    def test_load(self, tmp_path):
        f = tmp_path / "rate.csv"
        f.write_text("from,to,pair,rate\n2024/01/01,2024/06/30,USD/JPY,150.00\n2024/07/01,2024/12/31,USD/JPY,155.50\n")
        entries = load_rate_file(str(f))
        assert len(entries) == 2
        assert entries[0].pair == "USD/JPY"
        assert entries[0].rate == Decimal("150.00")
        assert entries[1].rate == Decimal("155.50")


class TestLookupRate:
    @pytest.fixture
    def rates(self):
        return [
            RateEntry(start="2024/01/01", end="2024/06/30", pair="USD/JPY", rate=Decimal("150")),
            RateEntry(start="2024/07/01", end="2024/12/31", pair="USD/JPY", rate=Decimal("155")),
        ]

    def test_match_first_period(self, rates):
        r = lookup_rate(rates, "2024-03-15T10:00:00+09:00", "JPY", "USD")
        assert r == Decimal("150")

    def test_match_second_period(self, rates):
        r = lookup_rate(rates, "2024-08-01T10:00:00+09:00", "JPY", "USD")
        assert r == Decimal("155")

    def test_same_currency_returns_none(self, rates):
        r = lookup_rate(rates, "2024-03-15T10:00:00+09:00", "USD", "USD")
        assert r is None

    def test_no_match_returns_none(self, rates):
        r = lookup_rate(rates, "2025-01-01T10:00:00+09:00", "JPY", "USD")
        assert r is None

    def test_date_only_format(self, rates):
        r = lookup_rate(rates, "2024-01-15", "JPY", "USD")
        assert r == Decimal("150")


class TestLoadOrderGroups:
    def test_load(self, tmp_path):
        f = tmp_path / "order.csv"
        f.write_text(
            "group_dt,ticker,quantity,price,currency,settle_currency,rate,price_type,timestamp\n"
            "2024-01-01 10:00:00,AAPL,5,150.0,USD,USD,,LIMIT,2024-01-01 01:00:00\n"
            "2024-01-01 10:00:00,MSFT,3,300.0,USD,USD,,LIMIT,2024-01-01 01:00:00\n"
            "2024-01-02 10:00:00,GOOG,2,140.0,USD,JPY,155.0,LIMIT,2024-01-02 01:00:00\n"
        )
        groups = load_order_groups(str(f))
        assert len(groups) == 2
        assert groups[0].group_id == "2024-01-01 10:00:00"
        assert len(groups[0].items) == 2
        assert groups[0].items[0]["ticker"] == "AAPL"
        assert groups[1].exchange_rate == 155.0

    def test_empty_file(self, tmp_path):
        f = tmp_path / "order.csv"
        f.write_text("group_dt,ticker,quantity,price,currency,settle_currency,rate,price_type,timestamp\n")
        groups = load_order_groups(str(f))
        assert groups == []


class TestLoadCashDeposits:
    def test_load(self, tmp_path):
        f = tmp_path / "deposits.csv"
        f.write_text(
            "group_dt,type,amount,currency,ticker,timestamp\n"
            "2024-01-01 00:00:00,budget,5000.0,USD,,2024-01-01 00:00:00\n"
            "2024-01-01 00:00:00,dividend,50.0,USD,AAPL,2024-01-01 00:00:00\n"
            "2024-01-02 00:00:00,budget,3000.0,JPY,,2024-01-02 00:00:00\n"
        )
        groups = load_cash_deposits(str(f))
        assert len(groups) == 2
        assert len(groups["2024-01-01 00:00:00"]) == 2
        assert groups["2024-01-01 00:00:00"][0].type == "budget"
        assert groups["2024-01-01 00:00:00"][1].ticker == "AAPL"


class TestMergeAndSortGroups:
    def test_merge_basic(self):
        orders = [
            OrderGroup(group_id="1704067200000", currency="USD", items=[{"ticker": "AAPL"}]),
        ]
        deposits = {
            "1704067200000": [CashDeposit(type="budget", amount=5000.0, currency="USD")],
            "1704153600000": [CashDeposit(type="budget", amount=3000.0, currency="JPY")],
        }
        result = merge_and_sort_groups(orders, deposits, {"1": "first memo"})
        assert len(result) == 2
        # 정렬 후 순번 재배정
        assert result[0].group_id == "1"
        assert result[1].group_id == "2"
        # deposit 붙었는지
        assert len(result[0].cash_deposits) == 1
        # memo 적용
        assert result[0].memo == "first memo"

    def test_empty(self):
        result = merge_and_sort_groups([], {}, {})
        assert result == []
