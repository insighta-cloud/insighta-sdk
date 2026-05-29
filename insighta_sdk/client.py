"""Insighta OpenAPI client."""

import json as _json
import logging
import os
from decimal import Decimal
from typing import Any

import requests

from .models import Credentials, OrderGroup, UploadConfig

log = logging.getLogger(__name__)


def _default_serializer(obj: Any) -> Any:
    """JSON serializer for objects not handled by default encoder."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class InsightaClient:
    """HTTP client for the Insighta OpenAPI.

    Args:
        credentials: API credentials containing endpoint and key.
        output_dir: Directory for request payload logs.
    """

    def __init__(self, credentials: Credentials, output_dir: str = "output") -> None:
        self.endpoint = credentials.endpoint
        self.output_dir = output_dir
        self.headers = {
            "Authorization": f"Bearer {credentials.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Send an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API path (e.g. "/portfolios").
            **kwargs: Additional arguments passed to requests.request.

        Returns:
            The HTTP response object.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        url = f"{self.endpoint}{path}"
        payload = kwargs.pop("json", None)
        if payload is not None:
            self._last_payload = payload
            payload_str = _json.dumps(
                payload, indent=2, ensure_ascii=False, default=_default_serializer,
            )
            log.debug("%s %s\n%s", method, url, payload_str)
            log_path = os.path.join(self.output_dir, "request_payload.log")
            os.makedirs(self.output_dir, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"=== {method} {url} ===\n{payload_str}\n\n")
            kwargs["data"] = _json.dumps(payload, ensure_ascii=False, default=_default_serializer)
        else:
            log.debug("%s %s", method, url)
        resp = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        log.debug("Response %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp

    def create_portfolio(self, config: UploadConfig) -> str:
        """Create a new portfolio.

        Args:
            config: Upload configuration with portfolio details.

        Returns:
            The newly created portfolio ID.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        items = [
            {
                "ticker": str(item["ticker"]),
                "type": str(item.get("type", "stock")),
                "quantity": item.get("quantity", 0),
                "ratio": item.get("ratio", 0),
                "price": item.get("price", 0),
                "sector": str(item.get("sector", "N/A")),
                "industry": str(item.get("industry", "N/A")),
            }
            for item in config.items
        ]
        body: dict[str, Any] = {
            "name": config.name,
            "description": config.description,
            "type": config.portfolio_type,
            "currency": config.currency,
            "budget": config.budget,
            "target_return": config.target_return,
            "start_date": config.start_date,
            "target_date": config.target_date,
            "items": items,
        }
        if config.settings:
            body["settings"] = config.settings
        resp = self._request("POST", "/portfolios", json=body)
        return resp.json()["portfolio_id"]

    def get_portfolios(self) -> list[dict[str, Any]]:
        """List the caller's own portfolios.

        Returns:
            List of portfolio dicts.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("GET", "/portfolios")
        return resp.json()

    def search_portfolios(
        self,
        search: str | None = None,
        country: str | None = None,
        sort_by: str | None = None,
        last_item: str | None = None,
    ) -> dict[str, Any]:
        """Search public portfolios.

        Args:
            search: Free-text search query.
            country: Filter by country code.
            sort_by: Sort field name.
            last_item: Pagination cursor.

        Returns:
            Dict containing search results and pagination info.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        params = {k: v for k, v in {
            "search": search, "country": country,
            "sort_by": sort_by, "last_item": last_item,
        }.items() if v is not None}
        resp = self._request("GET", "/portfolios", params=params)
        return resp.json()

    def delete_portfolio(self, portfolio_id: str) -> None:
        """Delete a portfolio.

        Args:
            portfolio_id: ID of the portfolio to delete.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        self._request("DELETE", f"/portfolios/{portfolio_id}")

    def get_nav_history(self, portfolio_id: str) -> dict[str, Any]:
        """Get NAV (Net Asset Value) history for a portfolio.

        Args:
            portfolio_id: Target portfolio ID.

        Returns:
            Dict containing NAV history data.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("GET", f"/portfolios/{portfolio_id}/nav-history")
        return resp.json()

    def get_metrics_history(
        self,
        portfolio_id: str,
        metrics: str = "twr",
        from_t: int | None = None,
        to_t: int | None = None,
    ) -> dict[str, Any]:
        """Get metrics history (e.g. TWR) for a portfolio.

        Args:
            portfolio_id: Target portfolio ID.
            metrics: Metric type to retrieve (default "twr").
            from_t: Start timestamp filter (Unix ms).
            to_t: End timestamp filter (Unix ms).

        Returns:
            Dict containing metrics history data.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        params: dict[str, Any] = {"metrics": metrics}
        if from_t is not None:
            params["from_t"] = str(from_t)
        if to_t is not None:
            params["to_t"] = str(to_t)
        resp = self._request(
            "GET", f"/portfolios/{portfolio_id}/metrics-history",
            params=params)
        return resp.json()

    def send_order(self, portfolio_id: str, order_group: OrderGroup, portfolio_currency: str) -> dict[str, Any]:
        """Submit an order group to a portfolio.

        Args:
            portfolio_id: Target portfolio ID.
            order_group: The order group to submit.
            portfolio_currency: The portfolio's base currency.

        Returns:
            Response dict (empty dict if no response body).

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        body: dict[str, Any] = {
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

    def update_portfolio(self, portfolio_id: str, **kwargs: Any) -> dict[str, Any]:
        """Update portfolio fields.

        Args:
            portfolio_id: Target portfolio ID.
            **kwargs: Fields to update (passed as JSON body).

        Returns:
            Updated portfolio dict.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("PUT", f"/portfolios/{portfolio_id}", json=kwargs)
        return resp.json()

    def trigger_history_backfill(self, portfolio_id: str) -> dict[str, Any]:
        """Trigger history backfill for a portfolio.

        Args:
            portfolio_id: Target portfolio ID.

        Returns:
            Response dict with backfill status.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("POST", f"/portfolios/{portfolio_id}/history-backfill")
        return resp.json()

    def get_orders(
        self,
        order_ids: str | None = None,
        portfolio_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List orders with optional filters.

        Args:
            order_ids: Comma-separated order IDs to filter.
            portfolio_id: Filter by portfolio ID.
            start_date: Filter orders after this date.
            end_date: Filter orders before this date.
            status: Filter by order status.
            limit: Maximum number of results.
            cursor: Pagination cursor.

        Returns:
            Dict containing orders and pagination info.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        params = {k: v for k, v in {
            "order_ids": order_ids, "portfolio_id": portfolio_id,
            "start_date": start_date, "end_date": end_date,
            "status": status, "limit": limit, "cursor": cursor,
        }.items() if v is not None}
        resp = self._request("GET", "/orders", params=params)
        return resp.json()

    def get_news(
        self,
        period: int,
        source_type: str | None = None,
        min_urgency: int | None = None,
    ) -> dict[str, Any]:
        """Fetch recent news articles.

        Args:
            period: Number of days to look back.
            source_type: Optional filter by source type.
            min_urgency: Optional minimum urgency level.

        Returns:
            Dict with "data" key containing list of news items.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        params: dict[str, Any] = {"period": period}
        if source_type is not None:
            params["source_type"] = source_type
        if min_urgency is not None:
            params["min_urgency"] = min_urgency
        resp = self._request("GET", "/news", params=params)
        return resp.json()

    def search_entities(self, keyword: str) -> dict[str, Any]:
        """Search for entities (tickers, companies) by keyword.

        Args:
            keyword: Search keyword.

        Returns:
            Dict containing matching entities.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("GET", "/search/entities", params={"keyword": keyword})
        return resp.json()

    def get_image_upload_url(self, filename: str, content_type: str = "image/png") -> dict[str, Any]:
        """Get a presigned URL for image upload.

        Args:
            filename: Name of the file to upload.
            content_type: MIME type of the image.

        Returns:
            Dict containing the presigned upload URL and metadata.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("GET", "/images/parse", params={"filename": filename, "content_type": content_type})
        return resp.json()

    def parse_image(self, files: list[str], prompt: str) -> dict[str, Any]:
        """Analyze images using AI.

        Args:
            files: List of uploaded file keys.
            prompt: Analysis prompt for the AI.

        Returns:
            Dict containing the AI analysis result.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("POST", "/images/parse", json={"files": files, "prompt": prompt})
        return resp.json()

    def delete_order(self, order_id: str) -> dict[str, Any]:
        """Delete an order.

        Args:
            order_id: ID of the order to delete.

        Returns:
            Dict with confirmation message and order_id.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        resp = self._request("DELETE", f"/orders/{order_id}")
        return resp.json()

    def send_copilot_message(
        self,
        message: str,
        room_id: str | None = None,
        last_messages: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a message to the Copilot and receive a response.

        Args:
            message: The user message text.
            room_id: Optional chat room ID (defaults to "default" server-side).
            last_messages: Optional conversation history for context.

        Returns:
            Dict containing message_id, reply, and session_id.

        Raises:
            requests.HTTPError: If the API returns a non-2xx status.
        """
        body: dict[str, Any] = {"message": message}
        if room_id is not None:
            body["room_id"] = room_id
        if last_messages is not None:
            body["last_messages"] = last_messages
        resp = self._request("POST", "/copilot/message", json=body)
        return resp.json()
