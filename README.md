# wayyfinance-docs

Central documentation hub for the wayyFinance ecosystem -- 6 open-source quant finance libraries built by [Wayy Research](https://wayy.pro) (Buffalo NY, Est. 2024). 9 years of institutional experience, pip-installable.

**If you are an LLM/AI agent**: read this file first, then [`llms.txt`](llms.txt) (~500 tokens) for navigation, or [`llms-full.txt`](llms-full.txt) (~15K tokens) for complete API reference across all packages. See [guides/for-llms.md](guides/for-llms.md) for prompting tips.

## Core Conventions (read this before writing any code)

1. **Polars-first.** All Python packages use Polars DataFrames as the primary data structure. Not pandas. `wrdata` returns Polars. `wrtrade` accepts Polars. `wrchart` renders from Polars. Zero-copy to NumPy via `df["close"].to_numpy()`.

2. **OHLCV column standard.** All packages expect: `timestamp` (or `time`), `open`, `high`, `low`, `close`, `volume`. Lowercase. `wrdata` outputs these by default. Rename non-standard columns before passing to other packages.

3. **UTC everywhere.** All timestamps are stored and processed in UTC. Convert to local time only at display boundaries. `wrdata` returns UTC. Do not convert until rendering.

4. **Decimal for real money.** Use `Decimal` for prices and position sizes in broker orders. Floats are fine for returns, ratios, Sharpe, Hurst, and analytical values.

5. **Free-tier first.** `wrdata` works with zero API keys (Yahoo Finance, Coinbase, Kraken). Premium providers are optional.

## What NOT To Do

```python
# WRONG: pandas
import pandas as pd
df = pd.read_csv(...)         # Use wrdata + Polars instead

# WRONG: no shift -- lookahead bias
signal = pl.col("close") > pl.col("close").rolling_mean(20)
# RIGHT: shift(1) so you only use yesterday's data
signal = pl.col("close").shift(1) > pl.col("close").shift(1).rolling_mean(20)

# WRONG: naive datetime
dt = datetime(2024, 6, 15, 16, 0, 0)           # No timezone!
# RIGHT: always UTC
dt = datetime(2024, 6, 15, 20, 0, 0, tzinfo=timezone.utc)

# WRONG: floats for broker orders
price = 152.35                                   # Float precision error
# RIGHT: Decimal
price = Decimal("152.35")

# WRONG: backtest without risk controls
result = wrt.backtest(my_signal, prices)          # No stop loss, no position limits

# RIGHT: use Portfolio with risk controls and validate before trusting
portfolio = wrt.Portfolio(my_signal, stop_loss=0.03, take_profit=0.10, max_position=0.5)
result = portfolio.backtest(prices)
p_value = portfolio.validate(prices)              # Permutation test -- is the edge real?
```

## The 6 Packages

| Package | Version | What It Does | I/O |
|---------|---------|--------------|-----|
| [wrdata](packages/wrdata/) | 0.1.6 | Unified data from 32+ providers (stocks, crypto, forex, options, economic) | Config in, Polars DataFrame out |
| [fractime](packages/fractime/) | 0.7.0 | Fractal forecasting, Hurst exponent, regime detection (HMMs). Risk assessment, not price prediction. | NumPy array in, ForecastResult out |
| [wrtrade](packages/wrtrade/) | 2.1.1 | Backtesting, Kelly optimization, permutation testing, broker deployment (Alpaca, Robinhood) | Polars DataFrame in, Result out |
| [wrchart](packages/wrchart/) | 0.2.0 | Interactive charts: candlestick, Renko, Kagi, P&F. Jupyter + standalone HTML. | Polars DataFrame in, HTML out |
| [@wayy/wrchart](packages/wrchart-js/) | 0.2.0 | React charting on TradingView Lightweight Charts. TypeScript, React 18+. | Props in, JSX out |
| [wayy-db](packages/wayydb/) | 0.1.0 | C++20 columnar time-series DB. kdb+-style as-of joins, SIMD (AVX2), memory-mapped, zero-copy NumPy. `pip install wayy-db`, `import wayy_db`. | NumPy in, Table out |

## Data Flow

```
wrdata (collect) --> fractime (forecast) / wrtrade (backtest) / wayy-db (store) --> wrchart (visualize)
```

Polars DataFrame is the interchange format. `fractime` and `wayy-db` accept NumPy arrays (one-liner: `df["close"].to_numpy()`).

**Dependencies within the ecosystem:**
- wrdata, wrchart, @wayy/wrchart, wayy-db: standalone (no wayyFinance deps)
- fractime, wrtrade: depend on wrchart (for built-in plotting)

## Quick Start

```bash
pip install wrdata fractime wrtrade wrchart
```

```python
from wrdata import DataStream
import fractime as ft

stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")  # Polars DataFrame, UTC timestamps

prices = df["close"].to_numpy()               # Zero-copy to NumPy
result = ft.forecast(prices, horizon=30)
ft.plot_forecast(prices[-100:], result).show()
```

## Three Canonical Workflows (with full examples)

### Workflow 1: Research -- fetch, analyze, forecast, visualize

Use this when you want to understand a market's fractal structure and generate a probabilistic forecast.

```python
from wrdata import DataStream
import fractime as ft
import wrchart as wrc

# Step 1: Fetch data (free, no API key)
stream = DataStream()
df = stream.get("AAPL", start="2023-01-01", interval="1d")
prices = df["close"].to_numpy()

# Step 2: Analyze fractal properties (method="dfa" is explicit -- default is "rs")
analyzer = ft.Analyzer(prices, method="dfa")
print(f"Hurst: {analyzer.hurst}")         # Metric object, float(analyzer.hurst) for value
print(f"Regime: {analyzer.regime}")        # "trending", "random", or "mean_reverting"

# Step 3: Decide if the market is forecastable
lower, upper = analyzer.hurst.ci(0.95)    # Bootstrap confidence interval
if lower > 0.55:
    print("Persistent trending -- fractal forecast may add value")
elif upper < 0.45:
    print("Mean-reverting -- consider contrarian signals")
else:
    print("Near random walk -- forecast unlikely to help")

# Step 4: Generate probabilistic forecast
model = ft.Forecaster(prices, method="dfa")
result = model.predict(steps=30, n_paths=2000)
lo, hi = result.ci(0.90)
print(f"30-day forecast: {result.forecast[-1]:.2f}")
print(f"90% CI: [{lo[-1]:.2f}, {hi[-1]:.2f}]")

# Step 5: Visualize forecast with Monte Carlo density
wrc.forecast(
    paths=result.paths,
    historical=prices[-100:],
    probabilities=result.probabilities,
    title="AAPL 30-Day Fractal Forecast",
).show()
```

### Workflow 2: Strategy Development -- fetch, build signal, backtest, validate

Use this when developing and testing a trading strategy.

```python
from wrdata import DataStream
import wrtrade as wrt
import polars as pl

# Step 1: Fetch data
stream = DataStream()
df = stream.get("BTC-USD", start="2022-01-01", interval="1d")
prices = df["close"]   # Polars Series -- no conversion needed for wrtrade

# Step 2: Define signal function (must return pl.Series of -1, 0, or 1)
def sma_crossover(prices: pl.Series) -> pl.Series:
    """Buy when 10-day MA > 30-day MA, flat otherwise."""
    fast = prices.rolling_mean(window_size=10)
    slow = prices.rolling_mean(window_size=30)
    return (fast > slow).cast(pl.Int8).fill_null(0)

# Step 3: One-line backtest
result = wrt.backtest(sma_crossover, prices)
print(f"Sortino: {result.sortino:.2f}")
print(f"Sharpe:  {result.sharpe:.2f}")
print(f"Max DD:  {result.max_drawdown:.2%}")
print(f"Total:   {result.total_return:.2%}")

# Step 4: Validate with permutation testing (is the edge real?)
p_value = wrt.validate(sma_crossover, prices, n_permutations=1000)
print(f"p-value: {p_value:.4f}")
if p_value < 0.05:
    print("Statistically significant edge")
else:
    print("May be overfitting -- do not deploy")

# Step 5: Optimize position sizing with Kelly criterion
optimal = wrt.optimize(sma_crossover, prices)
print(f"Optimal Kelly fraction: {optimal['kelly_fraction']:.2f}")

# Step 6: Print full tear sheet
result.tear_sheet()

# Step 7: Plot equity curve
result.plot().show()
```

### Workflow 3: Production -- store, analyze, trade

Use this for persistent storage, point-in-time data reconstruction, and live deployment.

```python
from wrdata import DataStream
import wayy_db
import fractime as ft
import wrtrade as wrt
import numpy as np
import polars as pl

# Step 1: Fetch and store in wayyDB for fast replay
stream = DataStream()
df = stream.get("AAPL", start="2020-01-01", interval="1d")
table = wayy_db.from_polars(df, name="AAPL_daily", sorted_by="timestamp")
table.save("/data/aapl.wayy")

# Step 2: Memory-map for instant reload (zero-copy, any size)
table = wayy_db.Table.mmap("/data/aapl.wayy")
prices_np = table["close"].to_numpy()      # Zero-copy numpy view

# Step 3: Compute indicators at C++ speed
sma_20 = wayy_db.ops.mavg(table["close"], 20)
sma_50 = wayy_db.ops.mavg(table["close"], 50)
returns = wayy_db.ops.pct_change(table["close"])

# Step 4: Detect regime with fractime
detector = ft.RegimeDetector(n_regimes=2)
detector.fit(returns[~np.isnan(returns)])
regime, prob = detector.get_current_regime(returns[~np.isnan(returns)])
print(f"Current regime: {regime} ({prob:.1%} confidence)")

# Step 5: Build regime-aware portfolio
def trend_signal(prices: pl.Series) -> pl.Series:
    fast = prices.rolling_mean(window_size=10)
    slow = prices.rolling_mean(window_size=50)
    return (fast > slow).cast(pl.Int8).fill_null(0)

def reversion_signal(prices: pl.Series) -> pl.Series:
    z = (prices - prices.rolling_mean(20)) / prices.rolling_std(20)
    return pl.when(z < -2).then(1).when(z > 2).then(-1).otherwise(0).fill_null(0).cast(pl.Int8)

# Weight signals based on detected regime
portfolio = wrt.Portfolio([
    ("trend", trend_signal, 0.8 if regime == "bull" else 0.3),
    ("reversion", reversion_signal, 0.2 if regime == "bull" else 0.7),
], stop_loss=0.03, take_profit=0.10)

prices_pl = pl.Series(prices_np)
result = portfolio.backtest(prices_pl)
p_value = portfolio.validate(prices_pl)

# Step 6: Deploy to paper trading if validated (async context required)
import asyncio

async def deploy_if_valid():
    if p_value < 0.05 and result.sortino > 1.0:
        deployment_id = await wrt.deploy(
            portfolio,
            symbols={"trend": "AAPL", "reversion": "AAPL"},
            config=wrt.DeployConfig(broker="alpaca", paper=True),
        )
        print(f"Deployed: {deployment_id}")

asyncio.run(deploy_if_valid())
```

## Best Practice Examples

### Fetching data (wrdata)

```python
from wrdata import DataStream

stream = DataStream()  # Zero config, uses free providers

# Single symbol -- daily equity (default: 1 year)
df = stream.get("AAPL")

# Specific date range
df = stream.get("MSFT", start="2024-06-01", end="2024-12-31")

# Intraday data
df = stream.get("AAPL", interval="5m", start="2024-11-07")

# Crypto (auto-detected from symbol format)
df = stream.get("BTC-USD")
df = stream.get("BTCUSDT")      # Binance format -- routed to Coinbase/Kraken for US users

# Multi-symbol fetch with coverage filter
df = stream.get_many(
    ["AAPL", "GOOGL", "MSFT", "AMZN"],
    start="2024-01-01",
    min_coverage=0.80,           # Drop symbols with <80% data
)
# Result has a "symbol" column -- pivot for correlation:
pivot = df.pivot(values="close", index="timestamp", on="symbol")

# Fast parallel crypto fetch (5-20x faster for large date ranges)
df = stream.fast_get("BTC-USD", interval="1m", start="2024-06-01", end="2024-06-30")

# Options chain with Greeks
chain = stream.options("SPY", expiry="2025-03-21")           # Both calls and puts
calls = chain.filter(chain["option_type"] == "call")          # Filter to calls
# Or fetch calls directly: stream.options("SPY", expiry="2025-03-21", option_type="call")

# Symbol discovery (useful when you don't know the exact ticker)
results = stream.search_symbol("bitcoin")         # -> [{'symbol': 'BTC-USD', 'name': ...}]
results = stream.search_symbol("apple", limit=5)  # -> [{'symbol': 'AAPL', 'name': ...}]

# Economic data (requires FRED key)
stream_econ = DataStream(fred_key="your_key")
gdp = stream_econ.get("GDP", asset_type="economic")

# Real-time streaming
import asyncio

async def monitor():
    async for tick in stream.stream("BTCUSDT"):
        print(f"BTC: ${tick.price:,.2f} at {tick.timestamp}")

asyncio.run(monitor())

# Provider priority (first available wins):
# equity:  ibkr > alpaca > finnhub > alphavantage > yfinance
# crypto:  coinbase > kraken > ccxt_kucoin > ccxt_okx > yfinance > coingecko
# options: ibkr > polygon_options
```

### Fractal analysis & forecasting (fractime)

```python
import fractime as ft
import numpy as np

# --- Hurst exponent analysis ---
# Note: default method is "rs" (Rescaled Range). "dfa" is explicitly chosen here.
# Pass dates= to the Analyzer if you need .rolling (otherwise it raises ValueError).
dates = df["timestamp"].to_numpy()
analyzer = ft.Analyzer(prices, dates=dates, method="dfa", window=63)  # ~3 months rolling
print(f"Hurst: {analyzer.hurst.value:.4f}")               # Point estimate
print(f"95% CI: {analyzer.hurst.ci(0.95)}")               # Bootstrap interval
print(f"Std: {analyzer.hurst.std:.4f}")                    # Standard error
print(f"Regime: {analyzer.regime}")                        # "trending"/"random"/"mean_reverting"

# Rolling Hurst over time (returns pl.DataFrame with date, value columns)
rolling_df = analyzer.hurst.rolling

# Hurst interpretation:
# H > 0.55 = trending (persistent) -- momentum strategies may work
# H ~ 0.50 = random walk           -- hard to forecast
# H < 0.45 = mean-reverting        -- contrarian strategies may work

# --- Forecasting ---
model = ft.Forecaster(prices, method="dfa", lookback=252)
result = model.predict(steps=30, n_paths=2000)

result.forecast      # Primary forecast (weighted median), shape: (30,)
result.mean          # Weighted mean, shape: (30,)
result.lower         # 5th percentile, shape: (30,)
result.upper         # 95th percentile, shape: (30,)
result.paths         # All Monte Carlo paths, shape: (2000, 30)
result.probabilities # Path weights, shape: (2000,)
result.ci(0.90)      # (lower_array, upper_array) at 90% confidence

# Convert to DataFrame for easy export
forecast_df = result.to_frame()  # Columns: step, forecast, lower, upper, mean, std

# --- Regime detection with HMMs ---
detector = ft.RegimeDetector(n_regimes=2)
detector.fit(returns)
regimes = detector.predict(returns)           # Array of regime labels per timestep
regime, prob = detector.get_current_regime(returns)
print(f"Current: {regime} ({prob:.1%})")      # "bull (87.3%)"

# --- Advanced analytics ---
beta = ft.compute_dtw_beta(stock_prices, index_prices)   # DTW-corrected beta
levels = ft.compute_qpl(prices)                           # Quantum price levels (support/resistance)
h_wavelet = ft.compute_wavelet_hurst(prices)              # Alternative Hurst method
```

### Backtesting & trading (wrtrade)

```python
import wrtrade as wrt
import polars as pl

# --- Signal function contract ---
# Input:  pl.Series of prices
# Output: pl.Series of -1 (short), 0 (flat), or 1 (long)
# wrtrade automatically shifts positions by 1 bar to prevent lookahead bias

def momentum(prices: pl.Series) -> pl.Series:
    ret_20 = prices.pct_change(20)
    return (ret_20 > 0).cast(pl.Int8).fill_null(0)

def mean_reversion(prices: pl.Series) -> pl.Series:
    z = (prices - prices.rolling_mean(20)) / prices.rolling_std(20)
    return pl.when(z < -2).then(1).when(z > 2).then(-1).otherwise(0).fill_null(0).cast(pl.Int8)

# --- Quick one-liner backtest ---
result = wrt.backtest(momentum, prices)
result.tear_sheet()

# --- Multi-signal portfolio ---
portfolio = wrt.Portfolio([
    ("trend", momentum, 0.6),
    ("reversion", mean_reversion, 0.4),
], max_position=0.5, stop_loss=0.03)

result = portfolio.backtest(prices, benchmark=True)
print(f"Sortino: {result.sortino:.2f}")
print(f"Excess return: {result.excess_return:.2%}")

# Per-signal attribution
for name, contrib in result.attribution.items():
    print(f"  {name}: {contrib:.4f}")

# --- Permutation testing (required before deployment) ---
p_value = wrt.validate(momentum, prices, n_permutations=1000)
# p < 0.05 = statistically significant edge
# p > 0.05 = likely overfit, do NOT deploy

# --- Kelly criterion position sizing ---
optimizer = wrt.KellyOptimizer()
full_kelly = optimizer.calculate_discrete_kelly(result.returns)
quarter_kelly = optimizer.calculate_fractional_kelly(result.returns, fraction=0.25)
print(f"Full Kelly: {full_kelly:.1%} -- Quarter Kelly: {quarter_kelly:.1%}")
# Always use fractional Kelly. Full Kelly tolerates 50%+ drawdowns.

# --- Deploy to paper trading (async context required) ---
import asyncio

async def deploy():
    deployment_id = await wrt.deploy(
        portfolio,
        symbols={"trend": "AAPL", "reversion": "AAPL"},
        config=wrt.DeployConfig(
            broker="alpaca",         # or "robinhood"
            paper=True,              # Always paper-test first
            max_position_pct=0.10,
            max_daily_loss_pct=0.05,
            validate=True,           # Enforces min_sortino check
            min_sortino=1.0,
        ),
    )
    print(f"Deployed: {deployment_id}")

asyncio.run(deploy())
```

### Charting & visualization (wrchart)

```python
import wrchart as wrc

# --- One-liners ---
wrc.candlestick(df).show()                              # OHLCV candlestick
wrc.line(df, title="Close Price").show()                 # Line chart
wrc.area(df).show()                                      # Area chart

# --- Method chaining with indicators ---
from wrchart.indicators import sma, ema, rsi, bollinger_bands

chart = (
    wrc.Chart(width=1000, height=600, theme="dark", title="AAPL")
    .add_candlestick(df)
    .add_volume(df)
    .add_line(sma_df, color="#2196F3", title="SMA 20")
    .add_horizontal_line(150.0, color="red", label="Support")
    .add_marker("2024-06-15", shape="arrowUp", color="green", text="Buy")
)
chart.show()

# --- Alternative chart types (transforms) ---
renko_df = wrc.to_renko(df, brick_size=2.0)
wrc.candlestick(renko_df, title="Renko").show()

ha_df = wrc.to_heikin_ashi(df)
wrc.candlestick(ha_df, title="Heikin-Ashi").show()

# --- Multi-panel dashboard ---
wrc.dashboard([price_df, volume_df, rsi_df], cols=1, title="Analysis").show()

# --- Forecast visualization (from fractime) ---
wrc.forecast(result.paths, prices, result.probabilities, title="Forecast").show()

# --- Backtest visualization (from wrtrade) ---
wrc.equity_curve(backtest_result.returns).show()
wrc.drawdown_chart(backtest_result.returns).show()
wrc.rolling_sharpe(backtest_result.returns, window=63).show()

# --- Themes ---
# Passing data to Chart() auto-detects chart type and renders it.
# Use the builder pattern (no data, explicit .add_* calls) for multi-series charts.
wrc.Chart(df, theme="dark")     # Dark background (default for financial)
wrc.Chart(df, theme="wayy")     # White, Wayy brand
wrc.Chart(df, theme="light")    # Gray

# --- Streamlit integration ---
chart = wrc.candlestick(df, theme="dark")
chart.streamlit(height=500)
```

### Time-series database (wayy-db)

```python
import wayy_db
import numpy as np

# --- Create tables from NumPy arrays ---
trades = wayy_db.from_dict({
    "time": np.array([10, 20, 30, 40, 50], dtype=np.int64),
    "price": np.array([100.0, 101.5, 99.8, 102.0, 103.5]),
    "size": np.array([10, 20, 15, 30, 5], dtype=np.int64),
}, name="trades", sorted_by="time")

quotes = wayy_db.from_dict({
    "time": np.array([5, 15, 35], dtype=np.int64),
    "bid": np.array([99.5, 100.5, 101.0]),
    "ask": np.array([100.5, 101.5, 102.0]),
}, name="quotes", sorted_by="time")

# --- As-of join (kdb+-style): latest quote at each trade time ---
joined = wayy_db.ops.aj(trades, quotes, on=[], as_of="time")
# Trade at time=20 gets quote from time=15 (most recent before)

# --- Window join: all quotes within a time window ---
windowed = wayy_db.ops.wj(trades, quotes, on=[], as_of="time",
                           window_before=10, window_after=0)

# --- SIMD-accelerated aggregations ---
avg = wayy_db.ops.avg(trades["price"])   # Mean
vol = wayy_db.ops.std(trades["price"])   # Std dev

# --- Moving windows (return np.ndarray) ---
sma = wayy_db.ops.mavg(trades["price"], 20)   # 20-period SMA
ema = wayy_db.ops.ema(trades["price"], alpha=2/13)  # 12-period EMA
ret = wayy_db.ops.pct_change(trades["price"])  # Percent change

# --- Persistence & memory-mapping ---
table.save("/data/trades.wayy")
table = wayy_db.Table.mmap("/data/trades.wayy")  # Instant reload, any size
prices = table["close"].to_numpy()                 # Zero-copy view

# --- Ingest from wrdata ---
df = stream.get("AAPL", start="2020-01-01")
table = wayy_db.from_polars(df, name="AAPL_daily", sorted_by="timestamp")

# --- Multi-table Database management ---
db = wayy_db.Database("/data/markets")           # Persistent directory-backed DB
db.create_table("SPY_daily")                      # Create named tables
# ... add columns, then:
db.save()                                         # Persist all tables
# Later:
db = wayy_db.Database("/data/markets")
spy = db["SPY_daily"]                             # Retrieve by name

# CRITICAL: both tables MUST be sorted_by the as_of column for joins.
# Joins silently produce wrong results on unsorted data -- there is no runtime check.
```

### React charting (@wayy/wrchart)

```tsx
import { useRef } from 'react';
import { WayyChart, useChartData, useLivePrice, TradeHeatmap } from '@wayy/wrchart';
import type { WayyChartRef } from '@wayy/wrchart';

// --- Static candlestick chart ---
function PriceChart({ data }) {
  return <WayyChart data={data} theme="dark" showVolume height={500} />;
}

// --- Live streaming chart ---
function LiveChart({ symbol }: { symbol: string }) {
  const chartRef = useRef<WayyChartRef>(null);
  const { data, loading } = useChartData({
    symbol,
    interval: '1m',
    apiUrl: '/api/v2/ohlcv',
    wsUrl: 'wss://your-server.com/ws/ohlcv',
  });
  const { last, bid, ask, connected } = useLivePrice({
    symbol,
    wsUrl: 'wss://your-server.com/ws/market',
  });

  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <span>Last: {last} | Bid: {bid} | Ask: {ask} | {connected ? 'LIVE' : 'OFFLINE'}</span>
      <WayyChart ref={chartRef} data={data} theme="dark" height={600} />
    </div>
  );
}

// --- Trade heatmap for order flow ---
function OrderFlow({ trades, currentPrice }) {
  return (
    <TradeHeatmap
      trades={trades}
      currentPrice={currentPrice}
      tickSize={0.5}
      visibleLevels={60}
      decayTimeMs={60000}
      height={700}
    />
  );
}
```

## Cross-Package Recipes

### Screen multiple assets for Hurst, then backtest the best candidates

```python
from wrdata import DataStream
import fractime as ft
import wrtrade as wrt
import polars as pl

stream = DataStream()
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]

# Screen: find trending assets (Hurst > 0.55)
trending = []
for sym in symbols:
    df = stream.get(sym, start="2024-01-01")
    prices = df["close"].to_numpy()
    analyzer = ft.Analyzer(prices, method="dfa")
    if analyzer.hurst.value > 0.55:
        trending.append((sym, float(analyzer.hurst), df["close"]))
        print(f"  {sym}: H={analyzer.hurst.value:.3f} -- TRENDING")
    else:
        print(f"  {sym}: H={analyzer.hurst.value:.3f}")

# Backtest momentum signal on trending assets only
def momentum(prices: pl.Series) -> pl.Series:
    return (prices.pct_change(20) > 0).cast(pl.Int8).fill_null(0)

for sym, hurst, prices_pl in trending:
    result = wrt.backtest(momentum, prices_pl)
    p_value = wrt.validate(momentum, prices_pl, n_permutations=500)
    print(f"  {sym}: Sortino={result.sortino:.2f}, p={p_value:.3f}")
```

### Regime-adaptive portfolio with fractime + wrtrade

```python
import fractime as ft
import wrtrade as wrt
import polars as pl

# Detect current regime
prices_np = df["close"].to_numpy()
detector = ft.RegimeDetector(n_regimes=3)
returns = pl.Series(prices_np).pct_change().fill_null(0).to_numpy()
detector.fit(returns)
regime, prob = detector.get_current_regime(returns)

# Adapt portfolio weights to regime
def trend_signal(p: pl.Series) -> pl.Series:
    fast = p.rolling_mean(window_size=10)
    slow = p.rolling_mean(window_size=50)
    return (fast > slow).cast(pl.Int8).fill_null(0)

def reversion_signal(p: pl.Series) -> pl.Series:
    z = (p - p.rolling_mean(20)) / p.rolling_std(20)
    return pl.when(z < -2).then(1).when(z > 2).then(-1).otherwise(0).fill_null(0).cast(pl.Int8)

weights = {
    "bull":     (0.8, 0.2),   # Favor trend following
    "bear":     (0.2, 0.8),   # Favor mean reversion
    "sideways": (0.5, 0.5),   # Equal weight
}
tw, rw = weights.get(regime, (0.5, 0.5))

portfolio = wrt.Portfolio([
    ("trend", trend_signal, tw),
    ("reversion", reversion_signal, rw),
])
result = portfolio.backtest(df["close"])
print(f"Regime: {regime} ({prob:.0%}) | Sortino: {result.sortino:.2f}")
```

### Full pipeline: fetch -> store in wayyDB -> compute indicators -> backtest

```python
from wrdata import DataStream
import wayy_db
import wrtrade as wrt
import polars as pl
import numpy as np

# Ingest from wrdata into wayyDB
stream = DataStream()
df = stream.get("AAPL", start="2020-01-01")
table = wayy_db.from_polars(df, name="AAPL", sorted_by="timestamp")

# Compute indicators at C++ speed
close = table["close"]
sma_20 = wayy_db.ops.mavg(close, 20)
sma_50 = wayy_db.ops.mavg(close, 50)

# Build signal from wayyDB indicators, feed to wrtrade
def fast_sma_signal(prices: pl.Series) -> pl.Series:
    """Pre-computed from wayyDB indicators."""
    signal = np.where(sma_20 > sma_50, 1, 0).astype(np.int8)
    # Trim to match prices length
    return pl.Series(signal[:len(prices)])

result = wrt.backtest(fast_sma_signal, df["close"])
p_value = wrt.validate(fast_sma_signal, df["close"])
print(f"Sortino: {result.sortino:.2f} | p-value: {p_value:.4f}")
```

### Options analysis with IV and Hurst

```python
from wrdata import DataStream
import fractime as ft

stream = DataStream(polygon_key="...")

# Fetch underlying and options
df = stream.get("SPY", start="2024-01-01")
expirations = stream.get_expirations("SPY")
chain = stream.options("SPY", expiry=expirations[0])

# IV analysis
calls = chain.filter(chain["option_type"] == "call")
print(calls.select(["strike", "bid", "ask", "implied_volatility"]).head(10))

# Hurst on underlying to assess regime
prices = df["close"].to_numpy()
analyzer = ft.Analyzer(prices, method="dfa")
print(f"SPY Hurst: {analyzer.hurst.value:.3f} ({analyzer.regime})")
# Low Hurst + high IV = potential mean-reversion opportunity
```

## Critical Quant Rules

1. Always `shift(1)` before computing signals -- prevents lookahead bias
2. Walk-forward validation only -- never train and test on the same data
3. Use `Decimal` for broker orders -- floats lose money over thousands of trades
4. Store UTC, display local -- `wrdata` returns UTC, do not convert until rendering
5. Validate OHLCV: `high >= max(open, close)`, `low <= min(open, close)`, `volume >= 0`
6. Always include transaction costs in backtests -- costless backtests are fantasy
7. Run permutation tests -- if randomized data produces similar results, your edge is not real
8. Use fractional Kelly (0.25), never full Kelly -- full Kelly tolerates 50%+ drawdowns
9. Paper-trade before live -- `wrt.DeployConfig(paper=True)` before `paper=False`
10. Always `sorted_by=` when creating wayyDB tables for joins -- unsorted joins silently produce wrong results

See [guides/quant-pitfalls.md](guides/quant-pitfalls.md) for detailed examples and fixes.

## Key API Signatures (quick reference)

```python
# wrdata
stream = DataStream()                                      # Zero-config
results = stream.search_symbol("bitcoin")                  # -> list[dict] (symbol discovery)
df = stream.get(symbol, start=, end=, interval=)           # -> pl.DataFrame
df = stream.get_many(symbols, start=, min_coverage=0.7)    # -> pl.DataFrame with "symbol" col
df = stream.fast_get(symbol, interval="1m", provider=)     # -> pl.DataFrame (parallel async)
chain = stream.options(symbol, expiry=, option_type=)      # -> pl.DataFrame
async for tick in stream.stream(symbol):                   # -> StreamMessage

# fractime
analyzer = ft.Analyzer(prices_np, method="dfa"|"rs")       # -> .hurst, .regime, .fractal_dim
result = ft.forecast(prices_np, horizon=30)                 # -> ForecastResult
detector = ft.RegimeDetector(n_regimes=2)                   # -> .fit(returns), .predict(returns)
ft.plot_forecast(prices, result)                            # -> Interactive chart

# wrtrade
result = wrt.backtest(signal_func, prices_pl)               # -> Result (.sortino, .sharpe, .max_drawdown)
p_value = wrt.validate(signal_func, prices_pl, n_perms=)    # -> float (p-value)
portfolio = wrt.Portfolio([(name, func, weight), ...])       # -> .backtest(), .validate(), .optimize()
wrt.tear_sheet(returns)                                      # Standalone: takes pl.Series of returns
result.tear_sheet()                                          # Method on Result object (same output)

# wrchart
wrc.candlestick(df).show()                                  # One-liner (auto-detects columns)
chart = wrc.Chart(theme="dark").add_candlestick(df)         # Builder pattern (multi-series)
wrc.forecast(paths, historical, probabilities).show()        # Monte Carlo visualization

# wayy-db
table = wayy_db.from_polars(df, sorted_by="timestamp")      # Polars -> Table
joined = wayy_db.ops.aj(left, right, on=[], as_of="time")   # As-of join
sma = wayy_db.ops.mavg(table["close"], 20)                  # -> np.ndarray
table = wayy_db.Table.mmap("/path/to/data.wayy")            # Instant memory-mapped load
```

## Documentation Map

| Path | Contents |
|------|----------|
| [overview/](overview/) | Ecosystem map, architecture, getting started, installation |
| [packages/](packages/) | Per-package API reference (`reference.md` = hand-maintained, `README.md` = auto-synced) |
| [cookbooks/](cookbooks/) | 8 runnable cross-package examples (`.py` and `.ipynb`) |
| [guides/](guides/) | API keys, data providers, quant pitfalls, LLM usage |
| [llms.txt](llms.txt) | Navigable index for LLMs (~500 tokens) |
| [llms-full.txt](llms-full.txt) | Complete API reference, all packages (~15K tokens, auto-generated) |

## Tech Stack

- Python 3.10+ (most packages), `uv` for environment management
- Polars for DataFrames, NumPy for numerical compute
- TypeScript / React 18+ for `@wayy/wrchart`
- C++20 / CMake / pybind11 for `wayy-db`
- MIT licensed across all packages

## Auto-Sync

Package READMEs and examples sync weekly from source repos via [GitHub Actions](.github/workflows/sync-docs.yml). Reference docs (`reference.md`) are hand-maintained.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT -- [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
