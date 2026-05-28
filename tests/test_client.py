"""Tests for insighta_sdk.client (InsightaClient)."""

import json
import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from insighta_sdk.client import InsightaClient
from insighta_sdk.models import CashDeposit, Credentials, OrderGroup, UploadConfig


def _get_request_body(mock_req) -> dict:
    """Extract the JSON body from a mocked requests.request call."""
    call_kwargs = mock_req.call_args[1]
    return json.loads(call_kwargs["data"])


@pytest.fixture
def creds():
    return Credentials(api_key="sk-test-12345678", endpoint="https://api.example.com")


@pytest.fixture
def client(creds, tmp_path):
    return InsightaClient(creds, output_dir=str(tmp_path))


class TestInit:
    def test_headers(self, client):
        assert client.headers["Authorization"] == "Bearer sk-test-12345678"
        assert client.headers["Content-Type"] == "application/json"

    def test_endpoint(self, client):
        assert client.endpoint == "https://api.example.com"


class TestRequest:
    @patch("insighta_sdk.client.requests.request")
    def test_get(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '[]'
        mock_resp.json.return_value = []
        mock_req.return_value = mock_resp

        resp = client._request("GET", "/portfolios")
        mock_req.assert_called_once_with(
            "GET", "https://api.example.com/portfolios",
            headers=client.headers, timeout=30,
        )
        assert resp.json() == []

    @patch("insighta_sdk.client.requests.request")
    def test_post_logs_payload(self, mock_req, client, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"id": "123"}'
        mock_resp.json.return_value = {"id": "123"}
        mock_req.return_value = mock_resp

        client._request("POST", "/test", json={"key": "value"})
        log_path = os.path.join(str(tmp_path), "request_payload.log")
        assert os.path.exists(log_path)
        content = open(log_path).read()
        assert '"key": "value"' in content


class TestCreatePortfolio:
    @patch("insighta_sdk.client.requests.request")
    def test_create(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.text = '{"portfolio_id": "pf-123"}'
        mock_resp.json.return_value = {"portfolio_id": "pf-123"}
        mock_req.return_value = mock_resp

        config = UploadConfig(
            name="Test", description="", portfolio_type="record",
            currency="USD", budget=Decimal("10000"), balance=Decimal("10000"),
            order_file="order.csv",
            items=[{
                "ticker": "SPY", "type": "stock", "quantity": 10,
                "ratio": 1.0, "price": 0, "sector": "N/A", "industry": "N/A",
            }],
        )
        pid = client.create_portfolio(config)
        assert pid == "pf-123"
        body = _get_request_body(mock_req)
        assert body["name"] == "Test"
        assert body["budget"] == 10000.0


class TestGetPortfolios:
    @patch("insighta_sdk.client.requests.request")
    def test_get(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '[{"portfolio_id": "pf-1", "name": "A"}]'
        mock_resp.json.return_value = [{"portfolio_id": "pf-1", "name": "A"}]
        mock_req.return_value = mock_resp

        result = client.get_portfolios()
        assert len(result) == 1
        assert result[0]["name"] == "A"


class TestSearchPortfolios:
    @patch("insighta_sdk.client.requests.request")
    def test_search(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_req.return_value = mock_resp

        client.search_portfolios(search="tech", country="US")
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["params"]["search"] == "tech"
        assert call_kwargs["params"]["country"] == "US"


class TestDeletePortfolio:
    @patch("insighta_sdk.client.requests.request")
    def test_delete(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.text = ''
        mock_req.return_value = mock_resp

        client.delete_portfolio("pf-123")
        mock_req.assert_called_once()
        assert "/portfolios/pf-123" in mock_req.call_args[0][1]


class TestSendOrder:
    @patch("insighta_sdk.client.requests.request")
    def test_basic_order(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"order_id": "o-1"}'
        mock_resp.json.return_value = {"order_id": "o-1"}
        mock_req.return_value = mock_resp

        group = OrderGroup(
            group_id="1", currency="USD",
            items=[{"ticker": "AAPL", "quantity": 5, "price": 150.0}],
        )
        result = client.send_order("pf-123", group, "USD")
        assert result["order_id"] == "o-1"
        body = _get_request_body(mock_req)
        assert body["portfolio_id"] == "pf-123"
        assert body["payment_currency"] == "USD"

    @patch("insighta_sdk.client.requests.request")
    def test_order_with_deposits_and_rate(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_resp.json.return_value = {}
        mock_req.return_value = mock_resp

        group = OrderGroup(
            group_id="1", currency="JPY",
            items=[{"ticker": "AAPL", "quantity": 5, "price": 150.0}],
            cash_deposits=[CashDeposit(type="budget", amount=Decimal("100000"), currency="JPY")],
            exchange_rate=Decimal("155.0"),
            memo="test memo",
        )
        client.send_order("pf-123", group, "USD")
        body = _get_request_body(mock_req)
        assert body["custom_exchange_rate"] == 155.0
        assert body["is_custom_exchange_rate"] is True
        assert body["memo"] == "test memo"
        assert len(body["cash_deposits"]) == 1
        assert body["cash_deposits"][0]["amount"] == 100000.0


class TestGetNavHistory:
    @patch("insighta_sdk.client.requests.request")
    def test_nav(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"history": [{"date": "2024-01-01", "nav": 10000}]}
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_req.return_value = mock_resp

        result = client.get_nav_history("pf-123")
        assert "history" in result


class TestGetMetricsHistory:
    @patch("insighta_sdk.client.requests.request")
    def test_metrics(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"history": []}
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_req.return_value = mock_resp

        client.get_metrics_history("pf-123", metrics="twr", from_t=1000, to_t=2000)
        params = mock_req.call_args[1]["params"]
        assert params["metrics"] == "twr"
        assert params["from_t"] == "1000"
        assert params["to_t"] == "2000"


class TestUpdatePortfolio:
    @patch("insighta_sdk.client.requests.request")
    def test_update(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": {"portfolio_id": "pf-123", "result": "updated"}}'
        mock_resp.json.return_value = {"data": {"portfolio_id": "pf-123", "result": "updated"}}
        mock_req.return_value = mock_resp

        result = client.update_portfolio("pf-123", name="New Name", is_public=True)
        body = _get_request_body(mock_req)
        assert body["name"] == "New Name"
        assert body["is_public"] is True
        assert "PUT" == mock_req.call_args[0][0]
        assert "/portfolios/pf-123" in mock_req.call_args[0][1]
        assert result["data"]["result"] == "updated"


class TestTriggerHistoryBackfill:
    @patch("insighta_sdk.client.requests.request")
    def test_backfill(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": {"status": "processing"}}'
        mock_resp.json.return_value = {"data": {"status": "processing"}}
        mock_req.return_value = mock_resp

        result = client.trigger_history_backfill("pf-123")
        assert "POST" == mock_req.call_args[0][0]
        assert "/portfolios/pf-123/history-backfill" in mock_req.call_args[0][1]
        assert result["data"]["status"] == "processing"


class TestGetOrders:
    @patch("insighta_sdk.client.requests.request")
    def test_by_order_ids(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": [{"id": "o-1"}]}'
        mock_resp.json.return_value = {"data": [{"id": "o-1"}]}
        mock_req.return_value = mock_resp

        result = client.get_orders(order_ids="o-1,o-2")
        params = mock_req.call_args[1]["params"]
        assert params["order_ids"] == "o-1,o-2"
        assert result["data"][0]["id"] == "o-1"

    @patch("insighta_sdk.client.requests.request")
    def test_by_portfolio_id(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_resp.json.return_value = {"data": {"items": [], "next_cursor": None}}
        mock_req.return_value = mock_resp

        client.get_orders(portfolio_id="pf-123", limit=10)
        params = mock_req.call_args[1]["params"]
        assert params["portfolio_id"] == "pf-123"
        assert params["limit"] == 10


class TestGetNews:
    @patch("insighta_sdk.client.requests.request")
    def test_news(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_resp.json.return_value = {"data": {"data": []}}
        mock_req.return_value = mock_resp

        client.get_news(period=2, source_type="NEWS", min_urgency=3)
        params = mock_req.call_args[1]["params"]
        assert params["period"] == 2
        assert params["source_type"] == "NEWS"
        assert params["min_urgency"] == 3


class TestSearchEntities:
    @patch("insighta_sdk.client.requests.request")
    def test_search(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_resp.json.return_value = {"data": {"total": 1, "results": [{"id": "e-1", "name": "Elon Musk"}]}}
        mock_req.return_value = mock_resp

        result = client.search_entities("Elon")
        params = mock_req.call_args[1]["params"]
        assert params["keyword"] == "Elon"
        assert result["data"]["total"] == 1


class TestGetImageUploadUrl:
    @patch("insighta_sdk.client.requests.request")
    def test_upload_url(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_resp.json.return_value = {"data": {"upload_url": "https://s3.example.com/upload", "file_key": "abc123"}}
        mock_req.return_value = mock_resp

        result = client.get_image_upload_url("screenshot.png", content_type="image/png")
        params = mock_req.call_args[1]["params"]
        assert params["filename"] == "screenshot.png"
        assert params["content_type"] == "image/png"
        assert result["data"]["file_key"] == "abc123"


class TestParseImage:
    @patch("insighta_sdk.client.requests.request")
    def test_parse(self, mock_req, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{}'
        mock_resp.json.return_value = {"data": {"analysis": "some result"}}
        mock_req.return_value = mock_resp

        result = client.parse_image(files=["abc123"], prompt="Describe this image")
        body = _get_request_body(mock_req)
        assert body["files"] == ["abc123"]
        assert body["prompt"] == "Describe this image"
        assert result["data"]["analysis"] == "some result"
