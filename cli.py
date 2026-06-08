#!/usr/bin/env python3
"""
cli.py — Command-line interface for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY (real testnet)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Limit SELL (real testnet)
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3000

# Stop-Market BUY (bonus order type)
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 95000

# Any order in MOCK mode (no API keys needed, no internet needed)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --mock

API credentials are read from environment variables:
    BINANCE_API_KEY
    BINANCE_API_SECRET

Or pass them directly with --api-key / --api-secret flags.
In --mock mode, credentials are not required.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

from bot.logging_config import setup_logging
from bot.orders import place_order

# Initialise logging early
logger = setup_logging()


# ── ANSI colour helpers (degrade gracefully on Windows) ──────────────────────
_USE_COLOUR = sys.stdout.isatty()

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text

GREEN  = lambda t: _c(t, "32")   # noqa: E731
RED    = lambda t: _c(t, "31")   # noqa: E731
YELLOW = lambda t: _c(t, "33")   # noqa: E731
CYAN   = lambda t: _c(t, "36")   # noqa: E731
BOLD   = lambda t: _c(t, "1")    # noqa: E731
DIM    = lambda t: _c(t, "2")    # noqa: E731


# ── CLI definition ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            ╔══════════════════════════════════════════════╗
            ║  Binance Futures Testnet — Trading Bot CLI   ║
            ╚══════════════════════════════════════════════╝

            Place MARKET, LIMIT, or STOP_MARKET orders on the
            Binance USDT-M Futures Testnet.

            Credentials (choose one method):
              1. Set env vars  BINANCE_API_KEY  /  BINANCE_API_SECRET
              2. Pass --api-key / --api-secret flags
              3. Use --mock mode (no credentials needed)
            """
        ),
        epilog=textwrap.dedent(
            """\
            Examples:
              python cli.py --symbol BTCUSDT --side BUY  --type MARKET     --quantity 0.01
              python cli.py --symbol ETHUSDT --side SELL --type LIMIT       --quantity 0.1  --price 3000
              python cli.py --symbol BTCUSDT --side BUY  --type STOP_MARKET --quantity 0.01 --stop-price 95000
              python cli.py --symbol BTCUSDT --side BUY  --type MARKET      --quantity 0.01 --mock
            """
        ),
    )

    # ── Credentials ──
    cred = parser.add_argument_group("credentials")
    cred.add_argument("--api-key",    default=os.getenv("BINANCE_API_KEY"),    help="Binance testnet API key (or set BINANCE_API_KEY env var)")
    cred.add_argument("--api-secret", default=os.getenv("BINANCE_API_SECRET"), help="Binance testnet API secret (or set BINANCE_API_SECRET env var)")

    # ── Order parameters ──
    order = parser.add_argument_group("order parameters")
    order.add_argument("--symbol",     required=True,  help="Trading pair, e.g. BTCUSDT")
    order.add_argument("--side",       required=True,  choices=["BUY", "SELL"], type=str.upper, help="Order side")
    order.add_argument("--type",       required=True,  choices=["MARKET", "LIMIT", "STOP_MARKET"], type=str.upper, dest="order_type", help="Order type")
    order.add_argument("--quantity",   required=True,  type=float, help="Order quantity (base asset)")
    order.add_argument("--price",      default=None,   type=float, help="Limit price (required for LIMIT orders)")
    order.add_argument("--stop-price", default=None,   type=float, dest="stop_price", help="Stop trigger price (required for STOP_MARKET)")
    order.add_argument("--tif",        default="GTC",  choices=["GTC", "IOC", "FOK"], help="Time-in-force for LIMIT orders (default: GTC)")

    # ── Misc ──
    parser.add_argument("--mock",  action="store_true", help="Run in mock mode — simulate orders locally without API keys or internet")
    parser.add_argument("--json",  action="store_true", help="Print raw JSON response instead of formatted output")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG-level console output")

    return parser


# ── Formatting helpers ────────────────────────────────────────────────────────

def _print_request_summary(args: argparse.Namespace) -> None:
    print()
    mock_tag = DIM("  [MOCK MODE]") if args.mock else ""
    print(BOLD("┌─ Order Request ────────────────────────────────┐") + mock_tag)
    print(f"│  Symbol     : {CYAN(args.symbol.upper())}")
    print(f"│  Side       : {GREEN(args.side) if args.side == 'BUY' else RED(args.side)}")
    print(f"│  Type       : {YELLOW(args.order_type)}")
    print(f"│  Quantity   : {args.quantity}")
    if args.price:
        print(f"│  Price      : {args.price}")
    if args.stop_price:
        print(f"│  Stop Price : {args.stop_price}")
    if args.order_type == "LIMIT":
        print(f"│  TIF        : {args.tif}")
    if args.mock:
        print(f"│  Mode       : {DIM('MOCK (simulated, no real order placed)')}")
    print(BOLD("└────────────────────────────────────────────────┘"))
    print()


def _print_response(result, raw_json: bool) -> None:
    if raw_json:
        print(json.dumps(result.raw, indent=2))
        return

    if result.success:
        print(GREEN(BOLD("✔  Order placed successfully")))
        print()
        print(BOLD("┌─ Order Response ───────────────────────────────┐"))
        print(f"│  Order ID     : {result.order_id}")
        print(f"│  Symbol       : {result.symbol}")
        print(f"│  Side         : {result.side}")
        print(f"│  Type         : {result.order_type}")
        print(f"│  Status       : {YELLOW(result.status)}")
        print(f"│  Orig Qty     : {result.orig_qty}")
        print(f"│  Executed Qty : {result.executed_qty}")
        print(f"│  Avg Price    : {result.avg_price}")
        if result.price and result.price != "0":
            print(f"│  Limit Price  : {result.price}")
        print(BOLD("└────────────────────────────────────────────────┘"))
    else:
        print(RED(BOLD("✘  Order failed")))
        print()
        print(f"  Error: {RED(result.error)}")

    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Bump console log level if --debug
    if args.debug:
        import logging
        logging.getLogger("trading_bot").setLevel(logging.DEBUG)
        for h in logging.getLogger("trading_bot").handlers:
            h.setLevel(logging.DEBUG)

    # ── Pick the right client ──────────────────────────────────────────────
    if args.mock:
        from bot.mock_client import MockBinanceFuturesClient
        client = MockBinanceFuturesClient()
        print(DIM("\n  ⚙  Running in MOCK mode — no real orders will be placed.\n"))
    else:
        # Real mode requires credentials
        if not args.api_key or not args.api_secret:
            parser.error(
                "API credentials missing.\n"
                "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
                "pass --api-key / --api-secret, or use --mock for offline simulation."
            )
        from bot.client import BinanceFuturesClient
        try:
            client = BinanceFuturesClient(
                api_key=args.api_key,
                api_secret=args.api_secret,
            )
        except ValueError as exc:
            print(RED(f"Configuration error: {exc}"))
            sys.exit(1)

    _print_request_summary(args)

    # Place order
    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
        time_in_force=args.tif,
    )

    _print_response(result, raw_json=args.json)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
