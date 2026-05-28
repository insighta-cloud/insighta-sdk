"""Basic usage: authentication, portfolio CRUD."""

from decimal import Decimal

from insighta_sdk import Credentials, InsightaClient, UploadConfig

# --- Authentication ---
creds = Credentials.from_file("credentials.yaml")
client = InsightaClient(creds)

# --- List portfolios ---
portfolios = client.get_portfolios()
print(f"You have {len(portfolios)} portfolio(s)")

# --- Create a portfolio ---
config = UploadConfig(
    name="My Portfolio",
    description="Example portfolio",
    portfolio_type="simulation",
    currency="USD",
    budget=Decimal("50000"),
    balance=Decimal("50000"),
    order_file="",
    items=[
        {
            "ticker": "AAPL",
            "type": "stock",
            "quantity": 10,
            "ratio": 0.3,
            "price": 180,
            "sector": "Technology",
            "industry": "Consumer Electronics",
        },
        {
            "ticker": "MSFT",
            "type": "stock",
            "quantity": 8,
            "ratio": 0.7,
            "price": 420,
            "sector": "Technology",
            "industry": "Software",
        },
    ],
)
portfolio_id = client.create_portfolio(config)
print(f"Created portfolio: {portfolio_id}")

# --- Update ---
client.update_portfolio(portfolio_id, name="My Portfolio (updated)")

# --- Delete ---
client.delete_portfolio(portfolio_id)
print("Portfolio deleted")
