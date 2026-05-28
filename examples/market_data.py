"""Market data: news, entity search, NAV and metrics history."""

from insighta_sdk import Credentials, InsightaClient

creds = Credentials.from_file("credentials.yaml")
client = InsightaClient(creds)

# --- News ---
news = client.get_news(period=7)
for article in news.get("data", [])[:3]:
    print(f"[{article.get('source_type')}] {article.get('title')}")

# --- Entity search ---
results = client.search_entities("Tesla")
print(f"Found {len(results.get('data', []))} entities for 'Tesla'")

# --- NAV history ---
portfolios = client.get_portfolios()
if portfolios:
    pid = portfolios[0].get("id") or portfolios[0].get("portfolio_id")
    nav = client.get_nav_history(pid)
    print(f"NAV history: {len(nav.get('data', []))} data points")

    # --- Metrics (TWR) ---
    metrics = client.get_metrics_history(pid, metrics="twr")
    print(f"TWR history: {len(metrics.get('data', []))} data points")
