"""Order submission: load CSV orders and send them."""

from insighta_sdk import Credentials, InsightaClient
from insighta_sdk.utils import load_order_groups, merge_and_sort_groups

creds = Credentials.from_file("credentials.yaml")
client = InsightaClient(creds)

PORTFOLIO_ID = "your-portfolio-id"
PORTFOLIO_CURRENCY = "KRW"

# --- Load order groups from CSV ---
order_groups = load_order_groups("order.csv")
merged = merge_and_sort_groups(order_groups, cash_deposits=[], memos={})

# --- Send each order group ---
for group in merged:
    result = client.send_order(PORTFOLIO_ID, group, PORTFOLIO_CURRENCY)
    print(f"Sent order group ({len(group.items)} items): {result}")
