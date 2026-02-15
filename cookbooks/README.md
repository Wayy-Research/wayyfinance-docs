# Cookbooks

Runnable cross-package examples demonstrating real workflows. Each `.py` file is a standalone script. Select cookbooks also have `.ipynb` notebook versions.

| # | Name | Packages Used | Description |
|---|------|---------------|-------------|
| 01 | [Data to Forecast](01-data-to-forecast.py) | wrdata, fractime, wrchart | Fetch AAPL, Hurst analysis, 30-day forecast, plot |
| 02 | [Backtest Strategy](02-backtest-strategy.py) | wrdata, wrtrade | MA crossover on BTC, backtest, equity curve |
| 03 | [Regime-Aware Trading](03-regime-aware-trading.py) | wrdata, fractime, wrtrade | HurstRegimeAnalyzer, adaptive allocation, backtest |
| 04 | [Realtime Streaming](04-realtime-streaming.py) | wrdata | Stream live BTC from Binance, build 1-minute candles |
| 05 | [Whale Detection](05-whale-detection.py) | wrdata | Monitor Binance for top 1% volume trades |
| 06 | [Options Analysis](06-options-analysis.py) | wrdata, fractime | Fetch SPY options chain, IV analysis |
| 07 | [TimeSeries DB](07-timeseries-db.py) | wrdata, wayy-db | Ingest ticks into wayyDB, as-of join trades/quotes |
| 08 | [Multi-Asset Screener](08-multi-asset-screener.py) | wrdata, fractime | Screen stocks/crypto/forex for Hurst + regime |

## Requirements

```bash
pip install wrdata fractime wrtrade wrchart wayy-db
```

Some cookbooks require API keys. See [../guides/api-keys.md](../guides/api-keys.md) for setup.

## Running

```bash
python cookbooks/01-data-to-forecast.py
```

Or open the `.ipynb` versions in Jupyter.
