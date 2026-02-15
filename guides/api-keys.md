# API Keys & Environment Setup

> Which providers need keys, where to get them, and how to configure your environment.

## Free Starter Kit (No Payment Required)

You can start using wayyFinance immediately without any API keys or signups. These providers work out of the box:

| Provider | Assets | Key Required | Notes |
|----------|--------|-------------|-------|
| Yahoo Finance | Stocks, ETFs, crypto, forex | No | Best general-purpose free provider. Covers most use cases. |
| Coinbase | 100+ crypto pairs | No | Good for crypto history and streaming. |
| Kraken | 300+ crypto pairs | No | Professional-grade crypto data. |
| Binance US | Crypto | No (for market data) | WebSocket streaming, 1000-bar historical. |

```python
from wrdata import DataStream

# These all work with zero configuration
stream = DataStream()

# Stocks (Yahoo Finance, automatic)
aapl = stream.get("AAPL", start="2024-01-01")

# Crypto (Coinbase, automatic)
btc = stream.get("BTC-USD", start="2024-01-01")

# No API keys needed for any of the above
```

## Free with API Key

These providers offer free tiers but require registration:

### FRED (Federal Reserve Economic Data)

Economic indicators, treasury yields, GDP, CPI, unemployment -- 800,000+ series.

- **Rate limit**: Effectively unlimited for normal use
- **Signup**: [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
- **How long**: 30 seconds, email verification

### Finnhub

US stocks, real-time quotes, WebSocket streaming.

- **Rate limit**: 60 calls/minute
- **Signup**: [finnhub.io](https://finnhub.io)
- **How long**: 1 minute, free tier is generous

### Alpaca

US stocks, real-time IEX data, paper trading.

- **Rate limit**: Unlimited for market data
- **Signup**: [alpaca.markets](https://alpaca.markets)
- **How long**: 2-3 minutes, requires identity for trading (paper trading is instant)
- **Note**: Also provides a paper trading API for testing strategies

### Alpha Vantage

Stocks, forex, crypto, technical indicators.

- **Rate limit**: 5 calls/minute, 500/day
- **Signup**: [alphavantage.co](https://www.alphavantage.co)
- **How long**: 30 seconds

### TwelveData

Stocks, forex, crypto, technical indicators.

- **Rate limit**: 800 calls/day, 8 calls/minute
- **Signup**: [twelvedata.com](https://twelvedata.com)
- **How long**: 1 minute
- **Gotcha**: Returns HTTP 200 with `{"code": 429}` in the body when rate limited (not HTTP 429). wrdata handles this internally.

## Paid / Premium

For professional use, higher rate limits, or specialized data:

| Provider | Assets | Notes | Signup |
|----------|--------|-------|--------|
| Polygon.io | US stocks, options, forex | Professional-grade US market data. Tiered pricing. | [polygon.io](https://polygon.io) |
| Interactive Brokers | Global markets, options, futures | Requires TWS or IB Gateway running locally. Trading account required. | [interactivebrokers.com](https://www.interactivebrokers.com) |
| Tradier | US options chains | Options-focused provider. Good for options analysis. | [tradier.com](https://tradier.com) |
| IEX Cloud | US stocks | Clean API, good documentation. Usage-based pricing. | [iexcloud.io](https://iexcloud.io) |

## Environment File Template

Create a `.env` file in your project root or at `~/.wrdata.env`:

```bash
# ============================================================
# wayyFinance Environment Configuration
# ============================================================
# Only fill in the providers you plan to use.
# Providers without keys will be skipped during auto-selection.

# --- Free Tier (Key Required) ---
FRED_API_KEY=
FINNHUB_API_KEY=
ALPACA_API_KEY=
ALPACA_API_SECRET=
ALPACA_PAPER=true
ALPHA_VANTAGE_API_KEY=
TWELVEDATA_API_KEY=

# --- Premium ---
POLYGON_API_KEY=
IBKR_GATEWAY_PORT=7497

# --- Crypto (optional, for private endpoints) ---
BINANCE_API_KEY=
BINANCE_API_SECRET=
COINBASE_KEY=
COINBASE_PRIVATE_KEY=
```

## Environment File Resolution

wrdata looks for credentials in this order, first match wins:

1. **Environment variables** -- Explicit `os.environ` values (highest priority)
2. **WRDATA_ENV_FILE** -- Path specified by this environment variable
3. **~/.wrdata.env** -- User-level config in home directory
4. **~/.config/wrdata/.env** -- XDG-style config directory
5. **.env in cwd** -- Project-level config (lowest priority)

This means you can set keys globally in `~/.wrdata.env` and override per-project with a local `.env` file.

## Passing Keys Directly

You can also pass API keys directly to the `DataStream` constructor, bypassing environment files entirely:

```python
from wrdata import DataStream

stream = DataStream(
    finnhub_api_key="your_key_here",
    alpaca_api_key="your_key_here",
    alpaca_api_secret="your_secret_here",
)

# This stream will use Finnhub and Alpaca regardless of .env files
df = stream.get("AAPL", provider="finnhub")
```

This is useful for notebooks, one-off scripts, and environments where file-based configuration is inconvenient.

## Verifying Your Setup

Check which providers are available in your current environment:

```python
from wrdata import DataStream

stream = DataStream()

# Try fetching from a specific provider
try:
    df = stream.get("AAPL", provider="finnhub")
    print("Finnhub: configured")
except Exception as e:
    print(f"Finnhub: not configured ({e})")
```

## Security Notes

- Never commit `.env` files to version control. Add `.env` to your `.gitignore`.
- Use environment variables in CI/CD pipelines, not files.
- Rotate keys if you accidentally expose them.
- Paper trading keys (Alpaca, IBKR) are safe to experiment with -- they cannot execute real trades.

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
