# insighta-sdk

Insighta Cloud SDK — API client and data models for portfolio management.

## Installation

```bash
pip install insighta-sdk
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

## API Endpoints

| Environment | Base URL |
|-------------|----------|
| Production | `https://openapi.insighta.cloud` |
| Development | `https://dev.openapi.insighta.cloud` |

OpenAPI spec: [`insighta-app/openapi-docs/`](https://github.com/insighta-cloud/insighta/tree/main/insighta-app/openapi-docs)

## Development

```bash
pip install -e .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

CC-BY-NC-4.0 — See [LICENSE](LICENSE)
