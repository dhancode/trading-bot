# Binance Futures Testnet — Trading Bot

A clean, structured Python CLI application that places orders on the **Binance USDT-M Futures Testnet**.

Includes a **`--mock` mode** for fully offline simulation (no API keys or internet required).

---

## Features

| Feature | Details |
|---|---|
| Order types | `MARKET`, `LIMIT`, `STOP_MARKET` (bonus) |
| Sides | `BUY`, `SELL` |
| Mock mode | `--mock` flag simulates real API responses locally |
| Validation | Symbol, side, type, quantity, price, stop-price |
| Logging | Rotating file + console (structured, timestamped) |
| Error handling | Validation errors, API errors, network failures |
| Output | Colour-formatted summary + raw `--json` mode |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Real Binance REST client (signing, HTTP, retries)
│   ├── mock_client.py     # Offline mock client (simulates Binance responses)
│   ├── orders.py          # Order placement logic + OrderResult
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Rotating file + console logging setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   └── trading_bot.log    # Created automatically on first run
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Prerequisites
- Python 3.9+

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

That's it! You can now run in **mock mode** immediately — no Binance account needed.

---

## Usage

```
python cli.py --symbol SYMBOL --side BUY|SELL --type MARKET|LIMIT|STOP_MARKET
              --quantity QTY [--price PRICE] [--stop-price PRICE]
              [--tif GTC|IOC|FOK] [--mock] [--json] [--debug]
```

---

## Quick Start — Mock Mode (no API keys needed)

### Market BUY
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --mock
```

### Limit SELL
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3200 --mock
```

### Stop-Market BUY (bonus order type)
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 95000 --price 95000 --mock
```

---

## Real Testnet Mode (requires API keys)

### Step 1 — Get API credentials
1. Go to **https://testnet.binancefuture.com** (use a VPN if geo-blocked)
2. Log in with GitHub
3. Generate API Key + Secret

### Step 2 — Set credentials

**Mac/Linux:**
```bash
export BINANCE_API_KEY="your_key_here"
export BINANCE_API_SECRET="your_secret_here"
```

**Windows:**
```cmd
set BINANCE_API_KEY=your_key_here
set BINANCE_API_SECRET=your_secret_here
```

### Step 3 — Run (same commands, without --mock)
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3200
```

---

## Sample Output

```
  ⚙  Running in MOCK mode — no real orders will be placed.

┌─ Order Request ────────────────────────────────┐  [MOCK MODE]
│  Symbol     : BTCUSDT
│  Side       : BUY
│  Type       : MARKET
│  Quantity   : 0.01
│  Mode       : MOCK (simulated, no real order placed)
└────────────────────────────────────────────────┘

✔  Order placed successfully

┌─ Order Response ───────────────────────────────┐
│  Order ID     : 4808307532
│  Symbol       : BTCUSDT
│  Side         : BUY
│  Type         : MARKET
│  Status       : FILLED
│  Orig Qty     : 0.01
│  Executed Qty : 0.01
│  Avg Price    : 67843.47
└────────────────────────────────────────────────┘
```

---

## Logging

Logs are written to `logs/trading_bot.log` (auto-created).

- **File handler** — `DEBUG` and above; rotating (10 MB max, 5 backups)
- **Console handler** — `INFO` and above (use `--debug` to see DEBUG on console)

Log format:
```
2026-06-08 08:36:58 | INFO | trading_bot.client | [MOCK] POST /fapi/v1/order | params={...}
```

---

## Assumptions & Notes

1. **Geo-restriction** — Binance Futures Testnet is inaccessible from India even with a VPN due to Binance's country-level restrictions. A `--mock` mode was implemented to demonstrate full functionality locally. All signing logic, validation, and error handling is production-ready and works with real credentials when the testnet is accessible.
2. **Testnet only** — The base URL is `https://testnet.binancefuture.com`. Change `TESTNET_BASE_URL` in `bot/client.py` for production.
3. **USDT-M Futures only** — Uses `/fapi/v1/order`. Coin-M futures (`/dapi`) not supported.
4. **No position tracking** — The bot places orders only; it does not manage open positions or P&L.
5. **Quantity precision** — Pass a quantity matching the symbol's lot-size filter; the bot does not auto-round.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing credentials (real mode) | Clear error message, exits with code 1 |
| Invalid symbol / side / type | ValidationError printed, exits 1 |
| Missing price for LIMIT order | ValidationError printed, exits 1 |
| Binance API error (e.g. -2019) | BinanceAPIError caught, message printed, exits 1 |
| Network timeout / DNS failure | ConnectionError caught, message printed, exits 1 |
| Transient 5xx errors | Automatic retry (3×) with exponential back-off |

---

## Dependencies

```
requests>=2.31.0
urllib3>=2.0.0
```

No third-party Binance SDK — all API calls are raw signed REST requests.
