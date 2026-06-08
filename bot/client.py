"""
Binance Futures Testnet REST client.

Handles request signing, HTTP communication, and low-level error handling.
All API calls are logged before being sent and after a response is received.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logging_config import setup_logging

logger = setup_logging()
_log = logging.getLogger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
FUTURES_ORDER_ENDPOINT = "/fapi/v1/order"
RECV_WINDOW = 5000


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error payload."""

    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg
        super().__init__(f"Binance API error {code}: {msg}")


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance USDT-M Futures Testnet REST API.

    Args:
        api_key:    Testnet API key.
        api_secret: Testnet API secret.
        base_url:   Override the base URL (defaults to testnet).
        timeout:    HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")

        self.api_key = api_key
        self._api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._session = self._build_session()
        _log.debug("BinanceFuturesClient initialised (base_url=%s)", self.base_url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        """
        Place a futures order.

        Args:
            symbol:        Trading pair (e.g. 'BTCUSDT').
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET', 'LIMIT', or 'STOP_MARKET'.
            quantity:      Order quantity.
            price:         Limit price (required for LIMIT orders).
            stop_price:    Stop trigger price (required for STOP_MARKET).
            time_in_force: 'GTC', 'IOC', 'FOK' (ignored for MARKET orders).

        Returns:
            Raw JSON response dict from Binance.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders.")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("stopPrice is required for STOP_MARKET orders.")
            params["stopPrice"] = str(stop_price)

        return self._signed_post(FUTURES_ORDER_ENDPOINT, params)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """Append timestamp + HMAC-SHA256 signature to params."""
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _signed_post(
        self, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Sign params and send a POST request."""
        signed_params = self._sign(params)
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}

        _log.info(
            "POST %s | params=%s",
            endpoint,
            {k: v for k, v in signed_params.items() if k != "signature"},
        )

        try:
            response = self._session.post(
                url,
                params=signed_params,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            _log.error("Network error: %s", exc)
            raise ConnectionError(
                f"Could not reach Binance testnet at {self.base_url}. "
                "Check your internet connection."
            ) from exc
        except requests.exceptions.Timeout as exc:
            _log.error("Request timed out after %ds", self.timeout)
            raise TimeoutError("Binance API request timed out.") from exc

        _log.debug("HTTP %d | body=%s", response.status_code, response.text[:500])

        data = response.json()

        if "code" in data and data["code"] != 200:
            _log.error(
                "Binance API error | code=%s msg=%s", data["code"], data.get("msg")
            )
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        _log.info("Order accepted | orderId=%s status=%s", data.get("orderId"), data.get("status"))
        return data

    @staticmethod
    def _build_session() -> requests.Session:
        """Create a requests Session with automatic retries on transient errors."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
