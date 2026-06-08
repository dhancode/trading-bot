"""
Order placement logic — sits between the CLI layer and the API client.

Responsibilities:
  - Validate inputs (delegating to validators.py)
  - Call the client
  - Format and return a structured result dict
  - Never interact with sys.stdout directly (that's the CLI's job)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from .client import BinanceFuturesClient
from .validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

_log = logging.getLogger("trading_bot.orders")


class OrderResult:
    """
    Lightweight container for an order outcome.

    Attributes:
        success:    True if the order was accepted.
        order_id:   Exchange-assigned order ID (None on failure).
        status:     Order status string (e.g. 'NEW', 'FILLED').
        executed_qty: Quantity actually executed so far.
        avg_price:  Average fill price (may be '0' for pending orders).
        raw:        Raw response dict from the API.
        error:      Human-readable error message (None on success).
    """

    def __init__(
        self,
        success: bool,
        raw: dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.raw = raw
        self.error = error

        self.order_id: Optional[int] = raw.get("orderId")
        self.status: Optional[str] = raw.get("status")
        self.executed_qty: Optional[str] = raw.get("executedQty")
        self.avg_price: Optional[str] = raw.get("avgPrice")
        self.symbol: Optional[str] = raw.get("symbol")
        self.side: Optional[str] = raw.get("side")
        self.order_type: Optional[str] = raw.get("type")
        self.orig_qty: Optional[str] = raw.get("origQty")
        self.price: Optional[str] = raw.get("price")

    def summary(self) -> str:
        """Return a human-friendly one-liner."""
        if not self.success:
            return f"[FAILED] {self.error}"
        return (
            f"[OK] orderId={self.order_id} | status={self.status} "
            f"| executedQty={self.executed_qty} | avgPrice={self.avg_price}"
        )


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
    time_in_force: str = "GTC",
) -> OrderResult:
    """
    Validate inputs and place a futures order via *client*.

    Args:
        client:        Initialised BinanceFuturesClient.
        symbol:        Raw symbol string from CLI.
        side:          Raw side string from CLI.
        order_type:    Raw order-type string from CLI.
        quantity:      Raw quantity value from CLI.
        price:         Raw price value (optional).
        stop_price:    Raw stop-price value (for STOP_MARKET).
        time_in_force: Time-in-force for LIMIT orders.

    Returns:
        OrderResult describing success or failure.
    """
    try:
        # --- Validate ---
        sym = validate_symbol(symbol)
        sd = validate_side(side)
        ot = validate_order_type(order_type)
        qty = validate_quantity(quantity)
        prc = validate_price(price, ot)
        stp = validate_stop_price(stop_price, ot)
    except ValueError as exc:
        _log.warning("Validation error: %s", exc)
        return OrderResult(success=False, raw={}, error=str(exc))

    _log.info(
        "Placing %s %s order | symbol=%s qty=%s price=%s stop=%s",
        sd, ot, sym, qty, prc, stp,
    )

    try:
        raw = client.place_order(
            symbol=sym,
            side=sd,
            order_type=ot,
            quantity=qty,
            price=prc,
            stop_price=stp,
            time_in_force=time_in_force,
        )
        _log.info("Order placed successfully | %s", raw)
        return OrderResult(success=True, raw=raw)

    except Exception as exc:  # noqa: BLE001
        _log.error("Order placement failed: %s", exc)
        return OrderResult(success=False, raw={}, error=str(exc))
