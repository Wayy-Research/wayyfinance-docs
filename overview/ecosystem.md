# wayyFinance Ecosystem

> Six open-source libraries for quantitative finance -- data, forecasting, backtesting, charting, and storage.

## The Libraries

| Package | Version | What It Does | Primary I/O |
|---------|---------|--------------|-------------|
| [wrdata](../packages/wrdata/) | 0.1.6 | Unified market data from 32+ providers (stocks, crypto, forex, options, economic) | Config in, Polars DataFrame out |
| [fractime](../packages/fractime/) | 0.7.0 | Fractal forecasting, Hurst exponent analysis, regime detection | NumPy array in, ForecastResult out |
| [wrtrade](../packages/wrtrade/) | 2.1.1 | Backtesting engine, Kelly criterion optimization, permutation testing, broker deployment | Polars Series in, Result out |
| [wrchart](../packages/wrchart/) | 0.2.0 | Interactive financial charts (candlestick, Renko, Kagi) for Python and Jupyter | Polars DataFrame in, HTML/Jupyter out |
| [@wayy/wrchart](../packages/wrchart-js/) | 0.2.0 | React charting components built on TradingView Lightweight Charts | Props in, JSX out |
| [wayy-db](../packages/wayydb/) | 0.1.0 | Columnar time-series database with kdb+-style as-of joins | NumPy arrays in, Table/Column out |

All packages are MIT licensed.

## Which Package Do I Need?

Start with what you are trying to do:

```
Need market data?
  --> wrdata
      Stocks, crypto, forex, options, economic indicators.
      32+ providers, one interface. Returns Polars DataFrames.

Need to forecast prices?
  --> fractime
      Fractal geometry + chaos theory approach.
      Hurst exponent, regime detection, confidence intervals.

Need to backtest a strategy?
  --> wrtrade
      Define signals, run backtests, optimize position sizing.
      Kelly criterion, permutation tests, live deployment.

Need charts in Python?
  --> wrchart
      Candlestick, Renko, Kagi, line charts.
      Works in Jupyter notebooks and standalone HTML.

Need charts in React?
  --> @wayy/wrchart (wrchart-js)
      TradingView-style components for web applications.
      TypeScript, React 18+, Lightweight Charts under the hood.

Need a fast time-series store?
  --> wayy-db
      Columnar storage with C++ core.
      kdb+-style as-of joins for point-in-time queries.
```

## Typical Combinations

Most users need 2-3 packages working together. Here are the common stacks:

**Research workflow**: wrdata + fractime + wrchart
Fetch data, run forecasts, visualize results. The "I want to analyze a stock" stack.

**Strategy development**: wrdata + wrtrade + wrchart
Fetch data, backtest strategies, chart equity curves. The "I want to test a trading idea" stack.

**Production pipeline**: wrdata + fractime + wrtrade + wayy-db
Fetch data, store it, forecast, trade. The "I want to run this daily" stack.

**Web application**: wrdata + @wayy/wrchart
Fetch data on the backend, render charts in React. The "I want to build a dashboard" stack.

## Install the Core Stack

```bash
pip install wrdata fractime wrtrade wrchart
```

This gives you data, forecasting, backtesting, and charting in one command.

See the [Installation Guide](installation.md) for per-package options and extras.

## Links

- [Architecture & Data Flow](architecture.md) -- how the packages connect
- [Getting Started](getting-started.md) -- your first workflow in 10 lines
- [Installation Guide](installation.md) -- per-package install with extras
- [Cookbooks](../cookbooks/) -- runnable cross-package examples

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
