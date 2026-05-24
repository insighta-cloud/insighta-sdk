"""Data models for Insighta SDK."""

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import yaml

WORKSPACES_DIR = "workspaces"
JST = timezone(timedelta(hours=9))


@dataclass
class Credentials:
    api_key: str
    endpoint: str

    @property
    def masked_key(self) -> str:
        if len(self.api_key) <= 8:
            return "****"
        return self.api_key[:4] + "****" + self.api_key[-4:]

    @classmethod
    def from_file(cls, path: str) -> "Credentials":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(api_key=data["api_key"], endpoint=data["endpoint"].rstrip("/"))


@dataclass
class UploadConfig:
    name: str
    description: str
    portfolio_type: str
    currency: str
    budget: Decimal
    balance: Decimal
    order_file: str
    target_return: float = 0.0
    start_date: str = ""
    target_date: str = ""
    items: list = field(default_factory=list)
    cash_deposits_file: str | None = None
    memo_file: str | None = None
    settings: dict | None = None

    @classmethod
    def from_file(cls, path: str) -> "UploadConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        p = data["portfolio"]
        files = data.get("files", {})
        return cls(
            name=p["name"],
            description=p.get("description", ""),
            portfolio_type=p["type"],
            currency=p["currency"],
            budget=Decimal(str(p["budget"])),
            balance=Decimal(str(p["budget"])),
            target_return=float(p.get("target_return", 0)),
            start_date=p.get("start_date", ""),
            target_date=p.get("target_date", ""),
            items=p.get("items", []),
            order_file=files["order"],
            cash_deposits_file=files.get("cash_deposits"),
            memo_file=files.get("memo"),
            settings=p.get("settings"),
        )


@dataclass
class CashDeposit:
    type: str       # budget | dividend
    amount: float
    currency: str | None = None
    ticker: str | None = None
    timestamp: int | None = None


@dataclass
class OrderGroup:
    group_id: str
    currency: str
    items: list = field(default_factory=list)
    cash_deposits: list[CashDeposit] = field(default_factory=list)
    exchange_rate: float | None = None
    memo: str = ""


@dataclass
class Trade:
    dt: str          # ISO 8601 JST
    ticker: str
    qty: int
    acct: str
    price: Decimal
    avg: Decimal
    cur: str         # 決済通貨 (JPY or USD)
    base: str = "USD"  # 銘柄の基準通貨


@dataclass
class Holding:
    ticker: str
    acct: str
    qty: int
    cost: Decimal = Decimal("0")
    price: Decimal = Decimal("0")
    pnl: Decimal = Decimal("0")


@dataclass
class Deposit:
    dt: str          # ISO 8601 JST or raw datetime
    amount: Decimal
    cur: str
    type: str = "budget"  # budget | dividend
    ticker: str = ""
    rate: Decimal | None = None


@dataclass
class RateEntry:
    start: str
    end: str
    pair: str
    rate: Decimal


@dataclass
class Dirs:
    """作業ディレクトリ設定。--work オプションで切り替え可能。"""
    work: str = ""

    @classmethod
    def from_work(cls, work: str = "") -> "Dirs":
        return cls(work=work)

    @property
    def _base(self) -> str:
        return os.path.join(WORKSPACES_DIR, self.work) if self.work else ""

    @property
    def input(self) -> str:
        return os.path.join(self._base, "input") if self._base else "input"

    @property
    def output(self) -> str:
        return os.path.join(self._base, "output") if self._base else "output"

    @property
    def history(self) -> str:
        return os.path.join(self.input, "history")

    @property
    def summary(self) -> str:
        return os.path.join(self.input, "summary")

    @property
    def seed(self) -> str:
        return os.path.join(self.input, "seed")

    @property
    def deposit(self) -> str:
        return os.path.join(self.input, "deposit")

    @property
    def exchange(self) -> str:
        return os.path.join(self.input, "currency_exchange")

    @property
    def manual(self) -> str:
        return os.path.join(self.input, "manual")

    @property
    def rate_csv(self) -> str:
        return os.path.join(self.input, "rate.csv")

    @property
    def ratio_csv(self) -> str:
        return os.path.join(self.input, "ratio.csv")

    @property
    def history_csv(self) -> str:
        return os.path.join(self.output, "history.csv")

    @property
    def order_csv(self) -> str:
        return os.path.join(self.output, "order.csv")

    @property
    def upload_yaml(self) -> str:
        return os.path.join(self.output, "upload.yaml")

    @property
    def memo_csv(self) -> str:
        return os.path.join(self.output, "memo.csv")

    @property
    def cash_deposits_csv(self) -> str:
        return os.path.join(self.output, "cash_deposits.csv")

    @property
    def request_payload_log(self) -> str:
        return os.path.join(self.output, "request_payload.log")

    def ensure_output(self):
        """output ディレクトリを作成する。"""
        os.makedirs(self.output, exist_ok=True)
