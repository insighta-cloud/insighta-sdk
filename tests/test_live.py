"""Live API tests — run with: pytest --live"""

import pytest

pytestmark = pytest.mark.live


class TestPortfoliosLive:
    def test_get_portfolios(self, live_client):
        result = live_client.get_portfolios()
        assert isinstance(result, (list, dict))

    def test_search_portfolios(self, live_client):
        result = live_client.search_portfolios(search="test")
        assert isinstance(result, dict)

    def test_create_update_delete(self, live_client):
        from decimal import Decimal
        from insighta_sdk.models import UploadConfig

        config = UploadConfig(
            name="SDK Live Test",
            description="auto test - delete me",
            portfolio_type="simulation",
            currency="USD",
            budget=Decimal("10000"),
            balance=Decimal("10000"),
            order_file="",
            items=[{"ticker": "AAPL", "type": "stock", "quantity": 10, "ratio": 1.0, "price": 150, "sector": "Tech", "industry": "Consumer Electronics"}],
        )
        pid = live_client.create_portfolio(config)
        assert pid

        updated = live_client.update_portfolio(pid, name="SDK Live Test Updated")
        assert updated

        live_client.delete_portfolio(pid)


class TestOrdersLive:
    def test_get_orders_empty(self, live_client):
        result = live_client.get_orders(portfolio_id="nonexistent-id")
        assert isinstance(result, dict)


class TestNewsLive:
    def test_get_news(self, live_client):
        result = live_client.get_news(period=1)
        assert "data" in result


class TestSearchEntitiesLive:
    def test_search(self, live_client):
        result = live_client.search_entities("Tesla")
        assert "results" in result or "data" in result


class TestHistoryLive:
    def test_nav_history(self, live_client):
        portfolios = live_client.get_portfolios()
        if isinstance(portfolios, list) and len(portfolios) > 0:
            pid = portfolios[0].get("id") or portfolios[0].get("portfolio_id")
            result = live_client.get_nav_history(pid)
            assert isinstance(result, dict)

    def test_metrics_history(self, live_client):
        portfolios = live_client.get_portfolios()
        if isinstance(portfolios, list) and len(portfolios) > 0:
            pid = portfolios[0].get("id") or portfolios[0].get("portfolio_id")
            result = live_client.get_metrics_history(pid, metrics="twr")
            assert isinstance(result, dict)
