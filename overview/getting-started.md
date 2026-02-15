# Getting Started

> From zero to your first forecast in under 2 minutes.

## Install the core stack

```bash
pip install wrdata fractime wrtrade wrchart
```

This gives you data collection, forecasting, backtesting, and charting. See the [Installation Guide](installation.md) if you need only specific packages or optional extras.

## Your first workflow

Fetch Apple stock data, analyze its fractal properties, generate a 30-day forecast, and plot the results. Ten lines of code:

```python
from wrdata import DataStream
import fractime as ft

# Fetch daily AAPL data from 2024 onward
stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")

# Extract closing prices as a NumPy array
prices = df["close"].to_numpy()

# Generate a 30-day fractal forecast
result = ft.forecast(prices, horizon=30)

# Inspect the results
print(f"Hurst exponent: {result.hurst:.3f}")
print(f"30-day forecast (final): ${result.mean[-1]:.2f}")

# Plot the last 100 days + forecast with confidence intervals
ft.plot_forecast(prices[-100:], result).show()
```

What this does:

1. `DataStream().get("AAPL")` fetches daily OHLCV data as a Polars DataFrame
2. `df["close"].to_numpy()` extracts closing prices as a NumPy array
3. `ft.forecast(prices, horizon=30)` runs fractal analysis (Hurst exponent, regime detection) and produces a 30-step-ahead forecast with confidence intervals
4. `ft.plot_forecast()` renders an interactive chart via wrchart

## What the Hurst exponent tells you

The `result.hurst` value characterizes the memory structure of the price series:

| Hurst Value | Interpretation | Implication |
|-------------|----------------|-------------|
| H < 0.5 | Mean-reverting | Price tends to reverse direction |
| H = 0.5 | Random walk | No exploitable structure |
| H > 0.5 | Trending / persistent | Price tends to continue its direction |

This is the foundation of fractime's forecasting approach. A Hurst exponent significantly different from 0.5 suggests the series has exploitable structure.

## Next: backtest a strategy

Once you have a forecast, you can test whether it leads to profitable trades:

```python
from wrtrade import Backtest, Strategy

# Define a simple strategy using fractime signals
class HurstStrategy(Strategy):
    def on_bar(self, bar):
        prices = self.data["close"].to_numpy()
        if len(prices) < 100:
            return

        result = ft.forecast(prices[-100:], horizon=5)

        # Go long when Hurst > 0.5 and forecast is up
        if result.hurst > 0.55 and result.mean[-1] > prices[-1]:
            self.buy()
        # Exit when Hurst drops or forecast is flat
        elif result.hurst < 0.45 or result.mean[-1] < prices[-1]:
            self.sell()

# Run the backtest
bt = Backtest(data=df, strategy=HurstStrategy)
result = bt.run()
print(result)
```

## Next steps

### Cookbooks (runnable examples)

- [Data to Forecast](../cookbooks/01-data-to-forecast.py) -- wrdata + fractime + wrchart end-to-end
- [Backtest a Strategy](../cookbooks/02-backtest-strategy.py) -- wrdata + wrtrade with equity curve
- [Regime-Aware Trading](../cookbooks/03-regime-aware-trading.py) -- fractime regimes + wrtrade
- [Multi-Asset Screener](../cookbooks/08-multi-asset-screener.py) -- screen tickers by Hurst exponent

### Package references

- [wrdata API Reference](../packages/wrdata/reference.md) -- all 32+ data providers
- [fractime API Reference](../packages/fractime/reference.md) -- forecast, Hurst, regimes
- [wrtrade API Reference](../packages/wrtrade/reference.md) -- backtesting, Kelly, deployment
- [wrchart API Reference](../packages/wrchart/reference.md) -- chart types, configuration

### Guides

- [API Keys Setup](../guides/api-keys.md) -- configure provider credentials
- [Data Providers](../guides/data-providers.md) -- which providers support what
- [Quant Pitfalls](../guides/quant-pitfalls.md) -- lookahead bias, timezone bugs, float precision

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
