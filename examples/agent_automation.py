"""AI Agent automation: use the SDK as an execution layer for LLM-driven portfolios.

This example shows how an AI agent might use insighta-sdk to:
1. Create a portfolio based on a research signal
2. Submit orders
3. Monitor performance

Adapt this pattern for LangChain tools, CrewAI tasks, or any agent framework.
"""

from decimal import Decimal

from insighta_sdk import Credentials, InsightaClient, UploadConfig

creds = Credentials.from_file("credentials.yaml")
client = InsightaClient(creds)


def agent_create_portfolio(signal: dict) -> str:
    """Agent action: create a portfolio from a research signal."""
    config = UploadConfig(
        name=signal["name"],
        description=f"Auto-generated from signal: {signal['thesis']}",
        portfolio_type="simulation",
        currency="USD",
        budget=Decimal(str(signal["budget"])),
        balance=Decimal(str(signal["budget"])),
        order_file="",
        items=[
            {
                "ticker": t["ticker"],
                "type": "stock",
                "quantity": t["qty"],
                "ratio": t["weight"],
                "price": t["price"],
                "sector": t.get("sector", "N/A"),
                "industry": t.get("industry", "N/A"),
            }
            for t in signal["tickers"]
        ],
    )
    return client.create_portfolio(config)


def agent_check_performance(portfolio_id: str) -> dict:
    """Agent action: check TWR and decide whether to rebalance."""
    metrics = client.get_metrics_history(portfolio_id, metrics="twr")
    return metrics


# --- Example signal from an LLM research agent ---
signal = {
    "name": "AI Momentum Q2",
    "thesis": "Overweight semis on AI capex cycle",
    "budget": 100000,
    "tickers": [
        {"ticker": "NVDA", "qty": 20, "weight": 0.5, "price": 950,
         "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AVGO", "qty": 15, "weight": 0.3, "price": 170,
         "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AMD", "qty": 30, "weight": 0.2, "price": 160,
         "sector": "Technology", "industry": "Semiconductors"},
    ],
}

if __name__ == "__main__":
    pid = agent_create_portfolio(signal)
    print(f"Portfolio created: {pid}")

    perf = agent_check_performance(pid)
    print(f"Performance data points: {len(perf.get('data', []))}")

    # Cleanup
    client.delete_portfolio(pid)
    print("Portfolio deleted")
