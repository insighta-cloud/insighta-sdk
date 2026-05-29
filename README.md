# insighta-sdk

[![CI](https://github.com/insighta-cloud/insighta-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/insighta-cloud/insighta-sdk/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/insighta-sdk)](https://pypi.org/project/insighta-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/insighta-sdk)](https://pypi.org/project/insighta-sdk/)
[![License](https://img.shields.io/badge/license-CC--BY--NC--4.0-blue)](LICENSE)

Insighta Cloud SDK — API client and data models for portfolio management.

## Installation

```bash
pip install insighta-sdk
```

## Authentication

You can obtain an API key from the **Developer** tab at [insight.cloud/settings](https://insight.cloud/settings).

Save the key in a `credentials.yaml` file:

```yaml
api_key: "your-api-key-here"
endpoint: "https://openapi.insighta.cloud"
```

Load it in your code:

```python
from insighta_sdk import Credentials

creds = Credentials.from_file("credentials.yaml")
```

## Quick Start

```python
from insighta_sdk import Credentials, InsightaClient

creds = Credentials.from_file("credentials.yaml")
client = InsightaClient(creds)

# List portfolios
portfolios = client.get_portfolios()

# Create a portfolio
from insighta_sdk import UploadConfig
config = UploadConfig.from_file("upload.yaml")
portfolio_id = client.create_portfolio(config)
```

## Features

- **API Client** — Full coverage of Insighta OpenAPI (portfolios, orders, metrics)
- **Data Models** — `Trade`, `Holding`, `Deposit`, `OrderGroup`, `CashDeposit`, `RateEntry`
- **Utilities** — Rate lookup, order grouping, deposit merging
- **Workspace Management** — `Dirs` class for consistent file path resolution

## Use Cases

- **AI Agent-driven portfolio automation** — Integrate with LLM agents (e.g., LangChain, CrewAI) to build autonomous rebalancing, signal-based trading, or research-to-execution pipelines using the SDK as the execution layer.
- **Backtesting dashboards** — Pull NAV/metrics history and visualize portfolio performance programmatically.
- **Multi-portfolio management** — Automate creation, monitoring, and teardown of simulation portfolios at scale.

## API Reference

### Client

| Method | Description |
|--------|-------------|
| `create_portfolio(config)` | Create a new portfolio |
| `get_portfolios()` | List own portfolios |
| `search_portfolios(...)` | Search public portfolios |
| `delete_portfolio(id)` | Delete a portfolio |
| `send_order(portfolio_id, group, currency)` | Submit an order group |
| `get_nav_history(id)` | Get NAV history |
| `get_metrics_history(id, ...)` | Get metrics (TWR, etc.) |

### Utilities

| Function | Description |
|----------|-------------|
| `load_order_groups(path)` | Parse order.csv into OrderGroup list |
| `load_cash_deposits(path)` | Parse cash_deposits.csv |
| `merge_and_sort_groups(orders, deposits, memos)` | Merge and sequence order groups |
| `load_rate_file(path)` | Load exchange rate CSV |
| `lookup_rate(entries, dt, cur, base)` | Find applicable rate for a trade |
| `fetch_ticker_info(tickers)` | Query ticker metadata from API |

## API Endpoint

Base URL: `https://openapi.insighta.cloud`

OpenAPI spec: [`insighta-app/openapi-docs/`](https://github.com/insighta-cloud/insighta/tree/main/insighta-app/openapi-docs)

## Development

```bash
pip install -e .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

CC-BY-NC-4.0 — See [LICENSE](LICENSE)
