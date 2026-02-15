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

# WRONG: backtest without costs
bt = Backtest(data=df, strategy=s)               # Costless fantasy
# RIGHT: include transaction costs
bt = Backtest(data=df, strategy=s, commission=0.001, slippage=0.0005)
```

## The 6 Packages

| Package | Version | What It Does | I/O |
|---------|---------|--------------|-----|
| [wrdata](packages/wrdata/) | 0.1.6 | Unified data from 32+ providers (stocks, crypto, forex, options, economic) | Config in, Polars DataFrame out |
| [fractime](packages/fractime/) | 0.7.0 | Fractal forecasting, Hurst exponent, regime detection (HMMs). Risk assessment, not price prediction. | NumPy array in, ForecastResult out |
| [wrtrade](packages/wrtrade/) | 2.1.1 | Backtesting, Kelly optimization, permutation testing, broker deployment (Alpaca, Robinhood) | Polars DataFrame in, Result out |
| [wrchart](packages/wrchart/) | 0.2.0 | Interactive charts: candlestick, Renko, Kagi, P&F. Jupyter + standalone HTML. | Polars DataFrame in, HTML out |
| [@wayy/wrchart](packages/wrchart-js/) | 0.2.0 | React charting on TradingView Lightweight Charts. TypeScript, React 18+. | Props in, JSX out |
| [wayy-db](packages/wayydb/) | 0.1.0 | C++20 columnar time-series DB. kdb+-style as-of joins, SIMD (AVX2), memory-mapped, zero-copy NumPy. | NumPy in, Table out |

## Data Flow

```
wrdata (collect) --> fractime (forecast) / wrtrade (backtest) / wayy-db (store) --> wrchart (visualize)
```

Polars DataFrame is the interchange format. `fractime` and `wayy-db` accept NumPy arrays (one-liner: `df["close"].to_numpy()`).

**Dependencies within the ecosystem:**
- wrdata, wrchart, @wayy/wrchart, wayy-db: standalone (no wayyFinance deps)
- fractime, wrtrade: depend on wrchart (for built-in plotting)

## Three Canonical Workflows

**Research**: `wrdata` --> `fractime` --> `wrchart` (fetch, forecast, visualize)
**Strategy dev**: `wrdata` --> `wrtrade` --> `wrchart` (fetch, backtest, plot equity)
**Production**: `wrdata` --> `wayy-db` --> `fractime` --> `wrtrade` (fetch, store, forecast, trade)

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

## Critical Quant Rules

1. Always `shift(1)` before computing signals -- prevents lookahead bias
2. Walk-forward validation only -- never train and test on the same data
3. Use `Decimal` for broker orders -- floats lose money over thousands of trades
4. Store UTC, display local -- `wrdata` returns UTC, do not convert until rendering
5. Validate OHLCV: `high >= max(open, close)`, `low <= min(open, close)`, `volume >= 0`
6. Always include transaction costs in backtests -- costless backtests are fantasy
7. Run permutation tests -- if randomized data produces similar results, your edge is not real

See [guides/quant-pitfalls.md](guides/quant-pitfalls.md) for detailed examples and fixes.

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
