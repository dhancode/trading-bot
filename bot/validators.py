"""
Input validation for trading bot CLI arguments.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a trading symbol.

    Rules:
        - Must be a non-empty string.
        - Converted to uppercase.
        - Must end with 'USDT' for USDT-M futures (loosely checked).
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol must not be empty.")
    symbol = symbol.strip().upper()
    if len(symbol) < 5:
        raise ValidationError(
            f"Symbol '{symbol}' looks too short. Expected something like 'BTCUSDT'."
        )
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY / SELL)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type (MARKET / LIMIT / STOP_MARKET)."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """
    Validate order quantity.

    Args:
        quantity: Raw quantity value (string or float).

    Returns:
        Positive Decimal quantity.
    """
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate order price.

    - Required for LIMIT and STOP_MARKET orders.
    - Ignored (and should be None) for MARKET orders.

    Args:
        price:      Raw price value or None.
        order_type: Normalised order type string.

    Returns:
        Positive Decimal price, or None for MARKET orders.
    """
    order_type = order_type.upper()

    if order_type == "MARKET":
        if price is not None:
            # Not an error — just ignore the price for market orders.
            pass
        return None

    # LIMIT / STOP_MARKET require a price
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValidationError(f"Price '{price}' is not a valid number.")

    if p <= 0:
        raise ValidationError(f"Price must be greater than zero, got {p}.")

    return p


def validate_stop_price(
    stop_price: Optional[str | float], order_type: str
) -> Optional[Decimal]:
    """
    Validate stop price — required only for STOP_MARKET orders.
    """
    if order_type.upper() != "STOP_MARKET":
        return None

    if stop_price is None:
        raise ValidationError("Stop price (--stop-price) is required for STOP_MARKET orders.")

    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValidationError(f"Stop price '{stop_price}' is not a valid number.")

    if sp <= 0:
        raise ValidationError(f"Stop price must be greater than zero, got {sp}.")

    return sp
