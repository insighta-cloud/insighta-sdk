"""Insighta OpenAPI client."""

import json as _json
import logging
import os

import requests

from .models import Credentials, OrderGroup, UploadConfig

log = logging.getLogger(__name__)


class InsightaClient:
    """Insighta OpenAPI client."""

    def __init__(self, credentials: Credentials, output_dir: str = "output"):
        self.endpoint = credentials.endpoint
        self.output_dir = output_dir
        self.headers = {
            "Authorization": f"Bearer {credentials.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.endpoint}{path}"
        payload = kwargs.get("json")
        if payload is not None:
            self._last_payload = payload
            payload_str = _json.dumps(payload, indent=2, ensure_ascii=False)
            log.debug("%s %s\n%s", method, url, payload_str)
            log_path = os.path.join(self.output_dir, "request_payload.log")
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"=== {method} {url} ===\n{payload_str}\n\n")
        else:
            log.debug("%s %s", method, url)
        resp = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        log.debug("Response %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp

    def create_portfolio(self, config: UploadConfig) -> str:
        """POST /portfolios → portfolio_id 반환."""
        items = [
            {
                "ticker": str(item["ticker"]),
                "type": str(item.get("type", "stock")),
                "quantity": float(item.get("quantity", 0)),
                "ratio": float(item.get("ratio", 0)),
                "price": float(item.get("price", 0)),
                "sector": str(item.get("sector", "N/A")),
                "industry": str(item.get("industry", "N/A")),
            }
            for item in config.items
        ]
        body = {
            "name": config.name,
            "description": config.description,
            "type": config.portfolio_type,
            "currency": config.currency,
            "budget": float(config.budget),
            "target_return": config.target_return,
            "start_date": config.start_date,
            "target_date": config.target_date,
            "items": items,
        }
        if config.settings:
            body["settings"] = config.settings
        resp = self._request("POST", "/portfolios", json=body)
        return resp.json()["portfolio_id"]

    def get_portfolios(self) -> list[dict]:
        """GET /portfolios → return caller's own portfolios."""
        resp = self._request("GET", "/portfolios")
        return resp.json()

    def search_portfolios(
        self,
        search: str | None = None,
        country: str | None = None,
        sort_by: str | None = None,
        last_item: str | None = None,
    ) -> dict:
        """GET /portfolios with search params."""
        params = {k: v for k, v in {
            "search": search, "country": country,
            "sort_by": sort_by, "last_item": last_item,
        }.items() if v is not None}
        resp = self._request("GET", "/portfolios", params=params)
        return resp.json()

    def delete_portfolio(self, portfolio_id: str) -> None:
        """DELETE /portfolios/{portfolio_id}."""
        self._request("DELETE", f"/portfolios/{portfolio_id}")

    def get_nav_history(self, portfolio_id: str) -> dict:
        """GET /portfolios/{portfolio_id}/nav-history."""
        resp = self._request("GET", f"/portfolios/{portfolio_id}/nav-history")
        return resp.json()

    def get_metrics_history(
        self,
        portfolio_id: str,
        metrics: str = "twr",
        from_t: int | None = None,
        to_t: int | None = None,
    ) -> dict:
        """GET /portfolios/{portfolio_id}/metrics-history."""
        params: dict = {"metrics": metrics}
        if from_t is not None:
            params["from_t"] = str(from_t)
        if to_t is not None:
            params["to_t"] = str(to_t)
        resp = self._request(
            "GET", f"/portfolios/{portfolio_id}/metrics-history",
            params=params)
        return resp.json()

    def send_order(self, portfolio_id: str, order_group: OrderGroup, portfolio_currency: str) -> dict:
        """POST /orders → 주문 그룹 하나 전송."""
        body = {
            "portfolio_id": portfolio_id,
            "currency": portfolio_currency,
            "payment_currency": order_group.currency,
            "items": order_group.items,
        }
        if order_group.memo:
            body["memo"] = order_group.memo
        if order_group.exchange_rate:
            body["custom_exchange_rate"] = order_group.exchange_rate
            body["is_custom_exchange_rate"] = True
        if order_group.cash_deposits:
            body["cash_deposits"] = [
                {k: v for k, v in {
                    "type": d.type,
                    "amount": d.amount,
                    "currency": d.currency,
                    "ticker": d.ticker,
                    "timestamp": d.timestamp,
                }.items() if v is not None}
                for d in order_group.cash_deposits
            ]
        resp = self._request("POST", "/orders", json=body)
        return resp.json() if resp.text else {}
