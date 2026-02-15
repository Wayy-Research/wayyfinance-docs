# Data Providers Reference

> Complete reference for all 32+ data providers supported by wrdata. Includes rate limits, authentication requirements, supported assets, and provider auto-selection behavior.

## Historical Data -- Free (No Key)

These providers work immediately with no signup or configuration.

| Provider | Assets | Rate Limit | Notes |
|----------|--------|------------|-------|
| Yahoo Finance | Stocks, ETFs, crypto, forex, indices | ~2,000/hr | Best general-purpose free provider. Covers most research needs. |
| Coinbase | 100+ crypto pairs | Generous | Reliable crypto history and real-time streaming. |
| CoinGecko | 10,000+ crypto assets | 30/min (free tier) | Largest crypto coverage. Requires `User-Agent` header (wrdata handles this). |
| Kraken | 300+ crypto pairs | Generous | Professional-grade crypto data. Good for less common pairs. |
| CCXT | 100+ exchanges unified | Varies by exchange | Meta-provider: wrdata uses CCXT to access KuCoin, OKX, and others through a unified interface. |
| Binance US | Major crypto pairs | Generous | 1,000-bar historical via REST. Primary crypto streaming source. Note: `binance.com` is geoblocked from US -- wrdata uses `api.binance.us`. |

```python
from wrdata import DataStream

stream = DataStream()

# All of these work without any API keys
stocks = stream.get("AAPL", start="2024-01-01")                    # Yahoo Finance
crypto = stream.get("BTC-USD", start="2024-01-01")                 # Coinbase
forex  = stream.get("EUR-USD", start="2024-01-01")                 # Yahoo Finance
etf    = stream.get("SPY", start="2024-01-01")                     # Yahoo Finance
```

## Historical Data -- Free (Key Required)

Free tiers that require registration. See [API Keys Guide](api-keys.md) for signup links.

| Provider | Assets | Rate Limit | Signup |
|----------|--------|------------|--------|
| FRED | 800,000+ economic series (GDP, CPI, yields, employment) | Effectively unlimited | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) |
| Finnhub | US stocks, real-time quotes | 60/min | [finnhub.io](https://finnhub.io) |
| Alpaca | US stocks (IEX real-time) | Unlimited (market data) | [alpaca.markets](https://alpaca.markets) |
| Alpha Vantage | Stocks, forex, crypto | 5/min, 500/day | [alphavantage.co](https://www.alphavantage.co) |
| TwelveData | Stocks, forex, crypto | 800/day, 8/min | [twelvedata.com](https://twelvedata.com) |

```python
# These require API keys in your environment
stream = DataStream()

# Economic data from FRED
gdp = stream.get("GDP", provider="fred")
cpi = stream.get("CPIAUCSL", provider="fred")
yields = stream.get("DGS10", provider="fred")  # 10-year Treasury

# Stocks from Finnhub
aapl = stream.get("AAPL", provider="finnhub")
```

## Historical Data -- Paid

Professional-grade data for production use.

| Provider | Assets | Notes |
|----------|--------|-------|
| Polygon.io | US stocks, options, forex, crypto | Tick-level data available. Tiered pricing from $29/mo. |
| Interactive Brokers | Global markets (stocks, options, futures, forex) | Requires TWS or IB Gateway running locally. Trading account required. Best global coverage. |
| Tradier | US options chains | Options-focused. Good for chain snapshots and Greeks. |
| IEX Cloud | US stocks | Clean API, usage-based pricing. Good for building applications. |

```python
# Paid providers
stream = DataStream()

# Polygon (professional US data)
aapl = stream.get("AAPL", provider="polygon")

# Interactive Brokers (requires TWS running)
es = stream.get("ES", provider="ibkr")  # E-mini S&P futures
```

## Streaming (WebSocket)

Real-time data via persistent WebSocket connections.

| Provider | Auth Required | Supported Streams | Notes |
|----------|--------------|-------------------|-------|
| Binance US | No | Ticker, kline, trades, orderbook, whale detection | Primary crypto streaming source. Free, no key needed for market data. |
| Coinbase | No | Ticker, matches, L2 orderbook | Reliable, clean WebSocket API. |
| Kraken | No | OHLC, ticker, trades, orderbook | Good for less common crypto pairs. |
| Finnhub | Key | Ticker, trade data (US stocks) | 60 calls/min on free tier. |
| Alpaca | Key | US stocks (real-time IEX) | Unlimited streaming on free tier. |
| Polygon | Paid | Stocks, options, crypto | Tick-level streaming. Professional. |
| Interactive Brokers | TWS | Global markets, options, futures | Lowest latency for production trading. |

```python
from wrdata import DataStream

stream = DataStream()

# Crypto streaming (no auth needed)
async for tick in stream.stream("BTC-USD", provider="binance"):
    print(f"{tick.timestamp} | {tick.price} | {tick.volume}")

# Stock streaming (requires Finnhub key)
async for tick in stream.stream("AAPL", provider="finnhub"):
    print(f"{tick.timestamp} | {tick.price}")
```

## Provider Auto-Selection

When you call `stream.get("AAPL")` without specifying a provider, wrdata selects the best available provider based on asset type and configured API keys.

### Selection Order by Asset Type

**Equities (stocks, ETFs)**:
```
ibkr --> alpaca --> finnhub --> alphavantage --> yfinance
```
Interactive Brokers is preferred when available (best data quality). Falls through to Yahoo Finance as the no-key default.

**Crypto**:
```
coinbase --> kraken --> ccxt_kucoin --> ccxt_okx --> yfinance --> coingecko
```
Coinbase is preferred for major pairs. CCXT exchanges provide coverage for altcoins. CoinGecko is the broadest fallback.

**Economic Data**:
```
fred
```
FRED is the only provider for economic indicators. Requires a free API key.

### Overriding Auto-Selection

Force a specific provider with the `provider=` parameter:

```python
stream = DataStream()

# Auto-select (uses the first available provider for equities)
df = stream.get("AAPL", start="2024-01-01")

# Force Yahoo Finance specifically
df = stream.get("AAPL", start="2024-01-01", provider="yfinance")

# Force Finnhub (requires FINNHUB_API_KEY)
df = stream.get("AAPL", start="2024-01-01", provider="finnhub")
```

## Provider-Specific Notes

### Yahoo Finance

- No key needed, but rate limits are informal (~2,000 requests/hour before throttling)
- Returns adjusted close prices by default (split and dividend adjusted)
- Covers US and international stocks, ETFs, mutual funds, indices, crypto, and forex
- Best free provider for general research

### CoinGecko

- Free tier: 30 requests/minute
- Requires `User-Agent` header or requests get HTTP 400 (wrdata handles this)
- OHLC candle granularity depends on the `days` parameter, not a separate interval: 1-2 days gives 30-min candles, 3-30 days gives 4-hour candles, 31-90 days gives daily, 91+ gives 3-day
- Largest crypto asset coverage (10,000+)

### Binance US

- Use `api.binance.us`, not `binance.com` (geoblocked from US, returns HTTP 451)
- 1,000 bars per historical REST request
- Free WebSocket streaming with no authentication for market data
- Supports whale detection (large trade alerts) via streaming

### TwelveData

- Returns HTTP 200 with `{"code": 429}` in the response body when rate limited (not a proper HTTP 429)
- wrdata detects this and retries with backoff
- Free tier: 8 calls/minute, 800 calls/day

### FRED

- 800,000+ economic series: treasuries, GDP, CPI, unemployment, PMI, and more
- Free API key, effectively unlimited rate limits for normal use
- Returns `"."` for missing values -- wrdata filters these out

### Interactive Brokers

- Requires TWS (Trader Workstation) or IB Gateway running locally
- Best data quality and global coverage (stocks, options, futures, forex across 150+ markets)
- Not a REST API -- connects via socket to local TWS process
- Default gateway port: 7497 (paper), 7496 (live)

## Provider Comparison Matrix

| Feature | Yahoo | Coinbase | Finnhub | Alpaca | Polygon | IBKR |
|---------|-------|----------|---------|--------|---------|------|
| Free | Yes | Yes | Yes | Yes | No | No |
| Key needed | No | No | Yes | Yes | Yes | TWS |
| US stocks | Yes | -- | Yes | Yes | Yes | Yes |
| Crypto | Yes | Yes | -- | Yes | Yes | Yes |
| Forex | Yes | -- | Yes | -- | Yes | Yes |
| Options | -- | -- | -- | -- | Yes | Yes |
| Futures | -- | -- | -- | -- | -- | Yes |
| Economic | -- | -- | -- | -- | -- | -- |
| Streaming | -- | Yes | Yes | Yes | Yes | Yes |
| Tick data | -- | -- | -- | -- | Yes | Yes |

FRED is the sole provider for economic data and is not included in this comparison.

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
