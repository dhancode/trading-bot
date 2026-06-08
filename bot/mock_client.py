"""
mock_client.py — Simulates the Binance Futures Testnet API locally.

Used when the real testnet is inaccessible (e.g. geo-restrictions).
Produces realistic responses identical in structure to the real API,
and logs everything exactly as the real client would.
"""

from __future__ import annotations

import logging
import random
import time
from decimal import Decimal
from typing import Any, Optional

_log = logging.getLogger("trading_bot.client")

# Realistic mid-prices for common pairs
_MOCK_PRICES: dict[str, float] = {
    "BTCUSDT":  67_800.00,
    "ETHUSDT":   3_520.00,
    "BNBUSDT":     580.00,
    "SOLUSDT":     175.00,
    "XRPUSDT":       0.62,
    "DOGEUSDT":      0.17,
}

_order_id_counter = random.randint(4_000_000_000, 5_000_000_000)


def _next_order_id() -> int:
    global _order_id_counter
    _order_id_counter += random.randint(1, 50)
    return _order_id_counter


def _mock_price(symbol: str) -> float:
    """Return a slightly jittered price for the symbol."""
    base = _MOCK_PRICES.get(symbol.upper(), 100.0)
    jitter = random.uniform(-0.002, 0.002)   # ±0.2 %
    return round(base * (1 + jitter), 2)


class MockBinanceFuturesClient:
    """
    Drop-in replacement for BinanceFuturesClient that never hits the network.

    All responses mirror the real Binance Futures REST API structure so the
    rest of the codebase (orders.py, cli.py) works without any changes.
    """

    def __init__(self, api_key: str = "MOCK_KEY", api_secret: str = "MOCK_SECRET") -> None:
        self.api_key = api_key
        self._api_secret = api_secret
        _log.info("[MOCK MODE] MockBinanceFuturesClient initialised — no real API calls will be made")

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
        """Simulate placing an order and return a realistic Binance response."""

        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }
        if price:
            params["price"] = str(price)
            params["timeInForce"] = time_in_force
        if stop_price:
            params["stopPrice"] = str(stop_price)

        _log.info(
            "[MOCK] POST /fapi/v1/order | params=%s", params
        )

        # Simulate small network delay
        time.sleep(random.uniform(0.05, 0.15))

        fill_price = _mock_price(symbol)
        order_id   = _next_order_id()
        ts         = int(time.time() * 1000)

        if order_type == "MARKET":
            response = {
                "orderId":        order_id,
                "symbol":         symbol,
                "status":         "FILLED",
                "clientOrderId":  f"mock_{order_id}",
                "price":          "0",
                "avgPrice":       str(fill_price),
                "origQty":        str(quantity),
                "executedQty":    str(quantity),
                "cumQty":         str(quantity),
                "cumQuote":       str(round(float(quantity) * fill_price, 4)),
                "timeInForce":    "GTC",
                "type":           "MARKET",
                "reduceOnly":     False,
                "closePosition":  False,
                "side":           side,
                "positionSide":   "BOTH",
                "stopPrice":      "0",
                "workingType":    "CONTRACT_PRICE",
                "priceProtect":   False,
                "origType":       "MARKET",
                "updateTime":     ts,
            }

        elif order_type == "LIMIT":
            response = {
                "orderId":        order_id,
                "symbol":         symbol,
                "status":         "NEW",
                "clientOrderId":  f"mock_{order_id}",
                "price":          str(price),
                "avgPrice":       "0",
                "origQty":        str(quantity),
                "executedQty":    "0",
                "cumQty":         "0",
                "cumQuote":       "0",
                "timeInForce":    time_in_force,
                "type":           "LIMIT",
                "reduceOnly":     False,
                "closePosition":  False,
                "side":           side,
                "positionSide":   "BOTH",
                "stopPrice":      "0",
                "workingType":    "CONTRACT_PRICE",
                "priceProtect":   False,
                "origType":       "LIMIT",
                "updateTime":     ts,
            }

        elif order_type == "STOP_MARKET":
            response = {
                "orderId":        order_id,
                "symbol":         symbol,
                "status":         "NEW",
                "clientOrderId":  f"mock_{order_id}",
                "price":          "0",
                "avgPrice":       "0",
                "origQty":        str(quantity),
                "executedQty":    "0",
                "cumQty":         "0",
                "cumQuote":       "0",
                "timeInForce":    "GTC",
                "type":           "STOP_MARKET",
                "reduceOnly":     False,
                "closePosition":  False,
                "side":           side,
                "positionSide":   "BOTH",
                "stopPrice":      str(stop_price),
                "workingType":    "CONTRACT_PRICE",
                "priceProtect":   False,
                "origType":       "STOP_MARKET",
                "updateTime":     ts,
            }

        else:
            raise ValueError(f"Unsupported order type in mock: {order_type}")

        _log.info(
            "[MOCK] Order accepted | orderId=%s status=%s",
            response["orderId"], response["status"],
        )
        _log.debug("[MOCK] Full response: %s", response)
        return response
