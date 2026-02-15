# wrdata -- API Reference

> Version: 0.1.6 | Python: 3.10+ | Install: `pip install wrdata`

Universal market data from 32+ providers through a single interface. Stocks, crypto, forex, options, economic indicators, and prediction markets. Returns Polars DataFrames.

---

## Quick Start

```python
from wrdata import DataStream

stream = DataStream()                                    # Zero config -- uses free providers
df = stream.get("AAPL", start="2024-01-01")              # Daily OHLCV as Polars DataFrame
df = stream.get("BTCUSDT")                               # Crypto auto-detected from symbol
chain = stream.options("SPY", expiry="2025-03-21")       # Options chain with Greeks
```

---

## Core API

### `DataStream`

The single entry point for all data operations.

#### Constructor

```python
DataStream(
    # Free providers (no key required)
    # -- yfinance, coinbase, coingecko, kraken, ccxt exchanges, polymarket

    # Economic data
    fred_key: str | None = None,

    # Equities (free tier + WebSocket)
    finnhub_key: str | None = None,

    # Broker data + trading
    alpaca_key: str | None = None,
    alpaca_secret: str | None = None,
    alpaca_paper: bool = True,

    # Interactive Brokers (requires TWS/Gateway running)
    ibkr_host: str = "127.0.0.1",
    ibkr_port: int = 7497,           # 7497=paper, 7496=live
    ibkr_client_id: int = 1,
    ibkr_readonly: bool = False,

    # Premium data
    polygon_key: str | None = None,
    alphavantage_key: str | None = None,
    twelvedata_key: str | None = None,

    # Behavior
    default_provider: str | None = None,
    fallback_enabled: bool = True,

    # Cache (future)
    cache_url: str | None = None,
    cache_token: str | None = None,
    cache_org: str | None = None,
)
```

All API keys can also be set via environment variables (`FRED_API_KEY`, `FINNHUB_API_KEY`, `ALPACA_API_KEY`, `ALPACA_API_SECRET`, `POLYGON_API_KEY`, `ALPHA_VANTAGE_API_KEY`). Constructor arguments take precedence.

---

### `DataStream.get`

Fetch historical OHLCV data for a single symbol.

```python
def get(
    symbol: str,
    start: str | None = None,       # "YYYY-MM-DD", default: 1 year ago
    end: str | None = None,          # "YYYY-MM-DD", default: today
    interval: str = "1d",            # "1m","5m","15m","1h","1d","1wk","1mo"
    asset_type: str | None = None,   # Auto-detected if omitted
    provider: str | None = None,     # Force specific provider
) -> pl.DataFrame
```

**Returns** a Polars DataFrame with columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`.

```python
# Daily equity data (default 1-year range)
df = stream.get("AAPL")

# Specific date range
df = stream.get("MSFT", start="2024-06-01", end="2024-12-31")

# Intraday
df = stream.get("AAPL", interval="5m", start="2024-11-07")

# Crypto (auto-detected from symbol)
df = stream.get("BTCUSDT")

# Economic data (requires FRED key)
df = stream.get("GDP", asset_type="economic")

# Force a specific provider
df = stream.get("ETH-USD", provider="coinbase")
```

---

### `DataStream.fast_get`

Parallel async fetch for large historical data. 5-20x faster than `get()` for long date ranges or fine-grained intervals.

```python
def fast_get(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
    provider: str = "coinbase",
    max_concurrent: int = 10,
) -> pl.DataFrame
```

**Returns** the same `pl.DataFrame` schema as `get()`.

Supported providers: `coinbase` (fastest for USD pairs), `kraken`, `binance` (requires non-US IP), `okx`, `kucoin`, `gateio`, `bybit`.

```python
# 1 year of 1-minute BTC data in seconds, not minutes
df = stream.fast_get("BTC-USD", interval="1m")

# Specific range from Kraken
df = stream.fast_get("ETH-USD", start="2024-01-01", end="2024-12-31", provider="kraken")
```

---

### `DataStream.get_many`

Fetch multiple symbols into a single DataFrame with a `symbol` column.

```python
def get_many(
    symbols: list[str],
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
    asset_type: str = "equity",
    provider: str | None = None,
    min_coverage: float = 0.70,      # Exclude symbols with <70% data
    forward_fill: bool = True,       # Fill gaps
    drop_low_coverage: bool = True,  # Drop sparse symbols
) -> pl.DataFrame
```

**Returns** a Polars DataFrame with columns: `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`.

```python
df = stream.get_many(
    ["AAPL", "GOOGL", "MSFT", "AMZN"],
    start="2024-01-01",
)

# Pivot for correlation analysis
pivot = df.pivot(values="close", index="timestamp", on="symbol")

# Multi-symbol crypto
df = stream.get_many(
    ["BTC-USD", "ETH-USD", "SOL-USD"],
    interval="1h",
    asset_type="crypto",
    min_coverage=0.8,
)
```

---

### `DataStream.options`

Fetch options chain data.

```python
def options(
    symbol: str,
    expiry: str | date | None = None,      # "YYYY-MM-DD" or date, default: nearest
    option_type: str | None = None,         # "call", "put", or None for both
    strike_min: float | None = None,
    strike_max: float | None = None,
) -> pl.DataFrame
```

**Returns** a Polars DataFrame with contract details, Greeks, and implied volatility.

```python
chain = stream.options("SPY")
chain = stream.options("SPY", expiry="2025-03-21", option_type="call")
chain = stream.options("AAPL", strike_min=180, strike_max=200)
```

---

### `DataStream.get_expirations`

Get available options expiration dates.

```python
def get_expirations(symbol: str) -> list[date]
```

```python
expirations = stream.get_expirations("SPY")
print(expirations[:5])
# [datetime.date(2025, 2, 21), datetime.date(2025, 2, 28), ...]
```

---

### `DataStream.search_symbol`

Search for symbols across all configured providers.

```python
def search_symbol(query: str, limit: int = 10) -> list[dict]
```

Each result dict contains: `symbol`, `name`, `type`, `provider`, `exchange`.

```python
results = stream.search_symbol("bitcoin")
# [{'symbol': 'BTC-USD', 'name': 'Bitcoin USD', 'type': 'cryptocurrency', ...}]

results = stream.search_symbol("apple", limit=5)
# [{'symbol': 'AAPL', 'name': 'Apple Inc.', 'type': 'equity', ...}]
```

---

### `DataStream.status`

Check which providers are configured and available.

```python
def status() -> dict[str, dict]
```

---

### Real-Time Streaming

#### `DataStream.stream` (async generator)

```python
async def stream(
    symbol: str,
    stream_type: str = "ticker",     # "ticker" or "kline"
    interval: str = "1m",            # For kline streams
    provider: str | None = None,
) -> AsyncIterator[StreamMessage]
```

```python
import asyncio

async def main():
    stream = DataStream(finnhub_key="...")

    async for tick in stream.stream("BTCUSDT"):
        print(f"BTC: ${tick.price:.2f}")

    async for candle in stream.stream("ETHUSDT", stream_type="kline", interval="1m"):
        print(f"ETH Close: ${candle.close}")

asyncio.run(main())
```

#### `DataStream.subscribe` (callback-based)

```python
def subscribe(
    symbol: str,
    callback: Callable[[StreamMessage], None],
    stream_type: str = "ticker",
    interval: str = "1m",
    provider: str | None = None,
) -> asyncio.Task
```

```python
def on_tick(msg: StreamMessage):
    print(f"{msg.symbol}: ${msg.price}")

task = stream.subscribe("AAPL", on_tick)
```

#### `DataStream.stream_many`

```python
def stream_many(
    symbols: list[str],
    callback: Callable[[StreamMessage], None],
) -> None
```

#### `DataStream.disconnect_streams`

```python
def disconnect_streams() -> None
```

Tears down all active WebSocket connections.

---

### `StreamMessage`

Standardized message from any streaming provider.

```python
@dataclass
class StreamMessage:
    symbol: str
    timestamp: datetime
    price: float | None = None
    bid: float | None = None
    ask: float | None = None
    volume: float | None = None

    # OHLCV for kline streams
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None

    # Order book for depth streams
    bids: list | None = None
    asks: list | None = None

    # Metadata
    provider: str | None = None
    stream_type: str | None = None   # "trade", "ticker", "kline", "depth"
    raw_data: dict | None = None
```

---

### Standalone Async Functions

These work without instantiating `DataStream`:

```python
from wrdata import search_async, validate_async, resolve_async, get_metadata_async, get_economic_calendar_async

results = await search_async("AAPL")
is_valid = await validate_async("AAPL")
resolved = await resolve_async("AAPL")
metadata = await get_metadata_async("AAPL")
calendar = await get_economic_calendar_async()
```

---

## Common Patterns

### 1. Research workflow: fetch, analyze, chart

```python
from wrdata import DataStream

stream = DataStream()
df = stream.get("AAPL", start="2023-01-01", end="2024-12-31")

# Ready for analysis
returns = df["close"].pct_change().drop_nulls()
print(f"Mean daily return: {returns.mean():.4f}")
print(f"Rows: {len(df)}, Columns: {df.columns}")
```

### 2. Multi-asset correlation study

```python
stream = DataStream()
df = stream.get_many(
    ["SPY", "TLT", "GLD", "USO"],
    start="2023-01-01",
)
pivot = df.pivot(values="close", index="timestamp", on="symbol")
print(pivot.head())
```

### 3. Crypto data with fast parallel fetch

```python
stream = DataStream()
df = stream.fast_get("BTC-USD", interval="1m", start="2024-06-01", end="2024-06-30")
print(f"Fetched {len(df)} 1-minute bars")
```

### 4. Options analysis pipeline

```python
stream = DataStream(polygon_key="...")
expirations = stream.get_expirations("SPY")
chain = stream.options("SPY", expiry=expirations[0])
calls = chain.filter(chain["option_type"] == "call")
print(calls.select(["strike", "bid", "ask", "implied_volatility"]).head(10))
```

### 5. Live price monitor

```python
import asyncio
from wrdata import DataStream

async def monitor():
    stream = DataStream()
    async for tick in stream.stream("BTCUSDT"):
        print(f"{tick.timestamp} | BTC: ${tick.price:,.2f}")

asyncio.run(monitor())
```

---

## Gotchas

| Pitfall | Details |
|---------|---------|
| **Output is Polars, not pandas** | All methods return `pl.DataFrame`. Convert with `df.to_pandas()` if needed. |
| **Default range is 1 year** | Omitting `start` fetches from 1 year ago to today. |
| **Intraday history is limited** | Most free providers cap 1m data at 7-30 days. Use `fast_get` for larger pulls. |
| **CoinGecko needs User-Agent** | wrdata handles this internally, but raw requests will get HTTP 400. |
| **Binance.com is geoblocked from US** | Use `api.binance.us` or let wrdata fall back to Coinbase/Kraken. |
| **FRED returns `"."` for missing values** | wrdata filters these automatically. |
| **Twelve Data silent rate limits** | Returns HTTP 200 with `{"code": 429}` in the body. wrdata retries automatically. |
| **IBKR requires TWS/Gateway running** | The provider silently skips if TWS is not running. |
| **Symbol format varies by provider** | `BTC-USD` (Coinbase), `BTCUSDT` (Binance), `XBTUSD` (Kraken). `search_symbol()` helps find the right format. |

### Asset Type Auto-Detection

wrdata infers asset type from the symbol string:

| Pattern | Detected As |
|---------|-------------|
| `*USDT`, `*USDC`, `*-USD`, `*-BTC` | crypto |
| 6-char uppercase (e.g., `EURUSD`) | forex |
| FRED series IDs | economic |
| Everything else | equity |

Override with `asset_type="crypto"` if auto-detection picks wrong.

### Provider Priority

| Asset Type | Provider Order (first available wins) |
|------------|---------------------------------------|
| equity | ibkr, alpaca, finnhub, alphavantage, yfinance |
| crypto | coinbase, kraken, ccxt_kucoin, ccxt_okx, ccxt_gateio, yfinance, coingecko |
| forex | ibkr, alphavantage, yfinance |
| options | ibkr, polygon_options |
| economic | fred |
| prediction_market | polymarket, kalshi |

---

## Integration

### wrdata -> fractime

```python
from wrdata import DataStream
import fractime as ft

stream = DataStream()
df = stream.get("^GSPC", start="2020-01-01")

prices = df["close"].to_numpy()
result = ft.forecast(prices, horizon=30)
```

### wrdata -> wrtrade

```python
from wrdata import DataStream
import wrtrade as wrt

stream = DataStream()
df = stream.get("AAPL", start="2020-01-01")

prices = df["close"]  # Polars Series, no conversion needed
result = wrt.backtest(my_signal, prices)
```

### wrdata -> wrchart

```python
from wrdata import DataStream
import wrchart as wrc

stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")

wrc.candlestick(df).show()  # Column names auto-detected
```

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY.
*People for research, research for people.*
