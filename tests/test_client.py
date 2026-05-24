"""Tests for insighta_sdk.client (InsightaClient)."""

import json
import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from insighta_sdk.client import InsightaClient
from insighta_sdk.models import CashDeposit, Credentials, OrderGroup, UploadConfig


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
            order_file="order.csv", items=[{"ticker": "SPY", "type": "stock", "quantity": 10, "ratio": 1.0, "price": 0, "sector": "N/A", "industry": "N/A"}],
        )
        pid = client.create_portfolio(config)
        assert pid == "pf-123"
        call_kwargs = mock_req.call_args[1]
        body = call_kwargs["json"]
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

        result = client.search_portfolios(search="tech", country="US")
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
        body = mock_req.call_args[1]["json"]
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
            cash_deposits=[CashDeposit(type="budget", amount=100000.0, currency="JPY")],
            exchange_rate=155.0,
            memo="test memo",
        )
        client.send_order("pf-123", group, "USD")
        body = mock_req.call_args[1]["json"]
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

        result = client.get_metrics_history("pf-123", metrics="twr", from_t=1000, to_t=2000)
        params = mock_req.call_args[1]["params"]
        assert params["metrics"] == "twr"
        assert params["from_t"] == "1000"
        assert params["to_t"] == "2000"
