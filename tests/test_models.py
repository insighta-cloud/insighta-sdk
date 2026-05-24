"""Tests for insighta_sdk.models."""

import os
import tempfile
from decimal import Decimal

import pytest
import yaml

from insighta_sdk.models import (
    Credentials,
    Deposit,
    Dirs,
    Holding,
    RateEntry,
    Trade,
    UploadConfig,
)


class TestDirs:
    def test_from_work_empty(self):
        d = Dirs.from_work("")
        assert d._base == ""
        assert d.input == "input"
        assert d.output == "output"

    def test_from_work_named(self):
        d = Dirs.from_work("my-portfolio")
        assert d._base == "workspaces/my-portfolio"
        assert d.input == "workspaces/my-portfolio/input"
        assert d.output == "workspaces/my-portfolio/output"
        assert d.history_csv == "workspaces/my-portfolio/output/history.csv"
        assert d.rate_csv == "workspaces/my-portfolio/input/rate.csv"

    def test_ensure_output(self, tmp_path):
        d = Dirs(work="")
        d_output = str(tmp_path / "out")
        # monkey-patch output property
        Dirs.output = property(lambda self: d_output)
        d.ensure_output()
        assert os.path.isdir(d_output)
        # restore
        Dirs.output = property(lambda self: os.path.join(self._base, "output") if self._base else "output")

    def test_all_paths(self):
        d = Dirs.from_work("test")
        assert "seed" in d.seed
        assert "deposit" in d.deposit
        assert "manual" in d.manual
        assert "order.csv" in d.order_csv
        assert "upload.yaml" in d.upload_yaml
        assert "memo.csv" in d.memo_csv


class TestCredentials:
    def test_from_file(self, tmp_path):
        cred_file = tmp_path / "creds.yaml"
        cred_file.write_text(yaml.dump({"api_key": "sk-test-12345678", "endpoint": "https://api.example.com/"}))
        c = Credentials.from_file(str(cred_file))
        assert c.api_key == "sk-test-12345678"
        assert c.endpoint == "https://api.example.com"  # trailing slash stripped

    def test_masked_key_long(self):
        c = Credentials(api_key="sk-test-12345678", endpoint="")
        assert c.masked_key == "sk-t****5678"

    def test_masked_key_short(self):
        c = Credentials(api_key="short", endpoint="")
        assert c.masked_key == "****"


class TestUploadConfig:
    def test_from_file(self, tmp_path):
        config = {
            "portfolio": {
                "name": "Test",
                "description": "desc",
                "type": "record",
                "currency": "USD",
                "budget": 10000,
                "target_return": 0.1,
                "start_date": "2024-01-01",
                "target_date": "2034-01-01",
                "items": [{"ticker": "SPY", "ratio": 1.0}],
            },
            "files": {"order": "order.csv", "cash_deposits": "deposits.csv"},
        }
        f = tmp_path / "upload.yaml"
        f.write_text(yaml.dump(config))
        uc = UploadConfig.from_file(str(f))
        assert uc.name == "Test"
        assert uc.budget == Decimal("10000")
        assert uc.order_file == "order.csv"
        assert uc.cash_deposits_file == "deposits.csv"
        assert uc.items == [{"ticker": "SPY", "ratio": 1.0}]


class TestTrade:
    def test_creation(self):
        t = Trade(dt="2024-01-01T10:00:00+09:00", ticker="AAPL", qty=10,
                  acct="TT", price=Decimal("150.5"), avg=Decimal("150.5"), cur="USD")
        assert t.base == "USD"
        assert t.qty == 10


class TestHolding:
    def test_defaults(self):
        h = Holding(ticker="MSFT", acct="NISA", qty=5)
        assert h.cost == Decimal("0")
        assert h.pnl == Decimal("0")


class TestDeposit:
    def test_creation(self):
        d = Deposit(dt="2024-01-01", amount=Decimal("1000"), cur="JPY", type="budget")
        assert d.ticker == ""
        assert d.rate is None


class TestRateEntry:
    def test_creation(self):
        r = RateEntry(start="2024/01/01", end="2024/12/31", pair="USD/JPY", rate=Decimal("155.5"))
        assert r.pair == "USD/JPY"
