"""Data models for Insighta SDK."""

import os
from dataclasses import dataclass, field
from datetime import timedelta, timezone
from decimal import Decimal
from typing import Any

import yaml

WORKSPACES_DIR = "workspaces"
JST = timezone(timedelta(hours=9))


@dataclass
class Credentials:
    """API credentials for authenticating with Insighta Cloud.

    Attributes:
        api_key: The API key string.
        endpoint: Base URL of the Insighta API.
    """

    api_key: str
    endpoint: str

    @property
    def masked_key(self) -> str:
        """Return a partially masked API key for safe display.

        Returns:
            Masked string showing only first and last 4 characters.
        """
        if len(self.api_key) <= 8:
            return "****"
        return self.api_key[:4] + "****" + self.api_key[-4:]

    @classmethod
    def from_file(cls, path: str) -> "Credentials":
        """Load credentials from a YAML file.

        Args:
            path: Path to the YAML credentials file.

        Returns:
            A Credentials instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            KeyError: If required keys are missing.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(api_key=data["api_key"], endpoint=data["endpoint"].rstrip("/"))


@dataclass
class UploadConfig:
    """Configuration for creating a new portfolio.

    Attributes:
        name: Portfolio display name.
        description: Portfolio description.
        portfolio_type: Type of portfolio (e.g. "stock").
        currency: Base currency code (e.g. "USD", "JPY").
        budget: Initial budget amount.
        balance: Current balance amount.
        order_file: Path to the order CSV file.
        target_return: Target return ratio.
        start_date: Portfolio start date (ISO 8601).
        target_date: Target end date (ISO 8601).
        items: List of portfolio item dicts.
        cash_deposits_file: Optional path to cash deposits CSV.
        memo_file: Optional path to memo CSV.
        settings: Optional portfolio settings dict.
    """

    name: str
    description: str
    portfolio_type: str
    currency: str
    budget: Decimal
    balance: Decimal
    order_file: str
    target_return: Decimal = Decimal("0")
    start_date: str = ""
    target_date: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    cash_deposits_file: str | None = None
    memo_file: str | None = None
    settings: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, path: str) -> "UploadConfig":
        """Load upload configuration from a YAML file.

        Args:
            path: Path to the YAML config file.

        Returns:
            An UploadConfig instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            KeyError: If required keys are missing.
        """
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
            target_return=Decimal(str(p.get("target_return", 0))),
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
    """A cash deposit or dividend event within an order group.

    Attributes:
        type: Deposit type ("budget" or "dividend").
        amount: Deposit amount.
        currency: Optional currency code.
        ticker: Optional ticker for dividend deposits.
        timestamp: Optional Unix timestamp in milliseconds.
    """

    type: str
    amount: Decimal
    currency: str | None = None
    ticker: str | None = None
    timestamp: int | None = None


@dataclass
class OrderGroup:
    """A group of orders submitted together.

    Attributes:
        group_id: Unique identifier for the group (typically a datetime string).
        currency: Settlement currency code.
        items: List of order item dicts.
        cash_deposits: Associated cash deposits.
        exchange_rate: Custom exchange rate override.
        memo: Optional memo text.
    """

    group_id: str
    currency: str
    items: list[dict[str, Any]] = field(default_factory=list)
    cash_deposits: list[CashDeposit] = field(default_factory=list)
    exchange_rate: Decimal | None = None
    memo: str = ""


@dataclass
class Trade:
    """A single executed trade record.

    Attributes:
        dt: Trade datetime in ISO 8601 JST.
        ticker: Ticker symbol.
        qty: Number of shares traded.
        acct: Account identifier.
        price: Execution price per share.
        avg: Average cost basis after trade.
        cur: Settlement currency (e.g. "JPY", "USD").
        base: Ticker's base currency (default "USD").
    """

    dt: str
    ticker: str
    qty: int
    acct: str
    price: Decimal
    avg: Decimal
    cur: str
    base: str = "USD"


@dataclass
class Holding:
    """A current portfolio holding.

    Attributes:
        ticker: Ticker symbol.
        acct: Account identifier.
        qty: Number of shares held.
        cost: Total cost basis.
        price: Current market price.
        pnl: Unrealized profit/loss.
    """

    ticker: str
    acct: str
    qty: int
    cost: Decimal = Decimal("0")
    price: Decimal = Decimal("0")
    pnl: Decimal = Decimal("0")


@dataclass
class Deposit:
    """A deposit record (budget addition or dividend).

    Attributes:
        dt: Deposit datetime in ISO 8601.
        amount: Deposit amount.
        cur: Currency code.
        type: Deposit type ("budget" or "dividend").
        ticker: Ticker symbol for dividend deposits.
        rate: Exchange rate applied at deposit time.
    """

    dt: str
    amount: Decimal
    cur: str
    type: str = "budget"
    ticker: str = ""
    rate: Decimal | None = None


@dataclass
class RateEntry:
    """An exchange rate entry valid for a date range.

    Attributes:
        start: Start date of validity (e.g. "2024/01/01").
        end: End date of validity (e.g. "2024/12/31").
        pair: Currency pair (e.g. "USD/JPY").
        rate: Exchange rate value.
    """

    start: str
    end: str
    pair: str
    rate: Decimal


@dataclass
class Dirs:
    """Workspace directory layout. Switchable via --work option.

    Attributes:
        work: Workspace name. Empty string means the default workspace.
    """

    work: str = ""

    @classmethod
    def from_work(cls, work: str = "") -> "Dirs":
        """Create a Dirs instance for the given workspace.

        Args:
            work: Workspace name. Defaults to the root workspace.

        Returns:
            A Dirs instance configured for the workspace.
        """
        return cls(work=work)

    @property
    def _base(self) -> str:
        return os.path.join(WORKSPACES_DIR, self.work) if self.work else ""

    @property
    def input(self) -> str:
        """Input directory path."""
        return os.path.join(self._base, "input") if self._base else "input"

    @property
    def output(self) -> str:
        """Output directory path."""
        return os.path.join(self._base, "output") if self._base else "output"

    @property
    def history(self) -> str:
        """History subdirectory path."""
        return os.path.join(self.input, "history")

    @property
    def summary(self) -> str:
        """Summary subdirectory path."""
        return os.path.join(self.input, "summary")

    @property
    def seed(self) -> str:
        """Seed subdirectory path."""
        return os.path.join(self.input, "seed")

    @property
    def deposit(self) -> str:
        """Deposit subdirectory path."""
        return os.path.join(self.input, "deposit")

    @property
    def exchange(self) -> str:
        """Currency exchange subdirectory path."""
        return os.path.join(self.input, "currency_exchange")

    @property
    def manual(self) -> str:
        """Manual input subdirectory path."""
        return os.path.join(self.input, "manual")

    @property
    def rate_csv(self) -> str:
        """Path to rate.csv."""
        return os.path.join(self.input, "rate.csv")

    @property
    def ratio_csv(self) -> str:
        """Path to ratio.csv."""
        return os.path.join(self.input, "ratio.csv")

    @property
    def history_csv(self) -> str:
        """Path to output history.csv."""
        return os.path.join(self.output, "history.csv")

    @property
    def order_csv(self) -> str:
        """Path to output order.csv."""
        return os.path.join(self.output, "order.csv")

    @property
    def upload_yaml(self) -> str:
        """Path to output upload.yaml."""
        return os.path.join(self.output, "upload.yaml")

    @property
    def memo_csv(self) -> str:
        """Path to output memo.csv."""
        return os.path.join(self.output, "memo.csv")

    @property
    def cash_deposits_csv(self) -> str:
        """Path to output cash_deposits.csv."""
        return os.path.join(self.output, "cash_deposits.csv")

    @property
    def request_payload_log(self) -> str:
        """Path to output request_payload.log."""
        return os.path.join(self.output, "request_payload.log")

    def ensure_output(self) -> None:
        """Create the output directory if it does not exist."""
        os.makedirs(self.output, exist_ok=True)
