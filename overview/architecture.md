# Architecture & Data Flow

> How the wayyFinance packages connect, what conventions they share, and how data moves between them.

## Data Flow

The packages form a pipeline. Data flows left to right, with visualization available at every stage:

```
                          +------------------+
                     +--> | fractime         | --+
                     |    | (forecast)       |   |
                     |    +------------------+   |
                     |                           v
+------------------+ |    +------------------+   +------------------+
| wrdata           | +--> | wrtrade          | ->| wrchart          |
| (collect)        | |    | (backtest/trade) |   | (visualize)      |
+------------------+ |    +------------------+   +------------------+
                     |                           ^
                     |    +------------------+   |
                     +--> | wayy-db          | --+
                          | (store/query)    |
                          +------------------+
```

### Concrete paths through the system

**Forecast workflow**:
```
wrdata.get("AAPL") --> Polars DataFrame
    --> df["close"].to_numpy() --> NumPy array
    --> fractime.forecast(prices) --> ForecastResult
    --> fractime.plot_forecast(prices, result) --> wrchart figure
```

**Backtest workflow**:
```
wrdata.get("AAPL") --> Polars DataFrame
    --> wrtrade.Backtest(data, strategy) --> Result
    --> result.plot() --> wrchart equity curve
```

**Store-and-analyze workflow**:
```
wrdata.get("AAPL") --> Polars DataFrame
    --> df.to_numpy() --> wayy-db Table
    --> wayy-db as-of join (trades + quotes)
    --> table.to_numpy() --> fractime or wrtrade
```

## Package Dependency Graph

```
wrdata        (standalone -- no wayyFinance deps)
fractime      (depends on wrchart for plotting)
wrtrade       (depends on wrchart for plotting)
wrchart       (standalone -- no wayyFinance deps)
@wayy/wrchart (standalone -- React/JS ecosystem)
wayy-db       (standalone -- no wayyFinance deps)
```

Three packages are fully standalone: wrdata, wrchart, and wayy-db. They have no dependencies on other wayyFinance packages. fractime and wrtrade both depend on wrchart for their built-in plotting functions.

## Shared Conventions

### DataFrame library: Polars

Polars is the primary DataFrame library across the Python packages. wrdata returns Polars DataFrames. wrtrade accepts Polars DataFrames and Series. wrchart renders from Polars DataFrames.

```python
import polars as pl

# wrdata output is Polars
df = stream.get("AAPL", start="2024-01-01")
type(df)  # polars.DataFrame

# wrtrade accepts Polars
backtest = Backtest(data=df, strategy=my_strategy)

# wrchart accepts Polars
chart = Chart(df)
```

### Numerical arrays: NumPy

fractime and wayy-db work with NumPy arrays for numerical computation. Converting between Polars and NumPy is a one-liner:

```python
# Polars column to NumPy (zero-copy when possible)
prices = df["close"].to_numpy()

# NumPy back to Polars
result_df = pl.DataFrame({"forecast": forecast_array})
```

### OHLCV column naming

All packages expect the same column names for price data:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` or `time` | datetime | Bar timestamp (UTC) |
| `open` | float | Opening price |
| `high` | float | High price |
| `low` | float | Low price |
| `close` | float | Closing price |
| `volume` | float/int | Volume traded |

wrdata outputs these columns by default. If your data source uses different names, rename before passing to other packages:

```python
df = df.rename({"Date": "timestamp", "Open": "open", "High": "high",
                "Low": "low", "Close": "close", "Volume": "volume"})
```

### Timestamps: UTC everywhere

All packages store and process timestamps in UTC. Convert to local time only for display:

```python
import datetime

# Internal: always UTC
utc_time = datetime.datetime(2024, 6, 15, 14, 30, tzinfo=datetime.timezone.utc)

# Display: convert at the boundary
eastern = utc_time.astimezone(datetime.timezone(datetime.timedelta(hours=-5)))
```

This prevents an entire class of timezone bugs. See [Quant Pitfalls](../guides/quant-pitfalls.md) for more.

### Precision: Decimal for prices in broker integration

When real money is involved (wrtrade broker deployment), use `Decimal` for prices and position sizes. Floats are acceptable for returns, ratios, and analytical calculations:

```python
from decimal import Decimal

# Broker orders: Decimal
order_price = Decimal("152.35")
shares = Decimal("100")

# Analytics: float is fine
daily_return = 0.0127
sharpe_ratio = 1.85
```

## Type Conversion Patterns

### Polars to NumPy

```python
# Single column
prices = df["close"].to_numpy()

# Multiple columns as 2D array
import numpy as np
ohlc = np.column_stack([
    df["open"].to_numpy(),
    df["high"].to_numpy(),
    df["low"].to_numpy(),
    df["close"].to_numpy(),
])
```

### NumPy to Polars

```python
import polars as pl
import numpy as np

# From a forecast result back to a DataFrame
forecast_df = pl.DataFrame({
    "step": np.arange(1, len(result.mean) + 1),
    "forecast": result.mean,
    "lower": result.lower,
    "upper": result.upper,
})
```

### wayy-db to NumPy

```python
# wayy-db columns are NumPy-backed
table = db.query("SELECT time, close FROM prices WHERE symbol = 'AAPL'")
times = table["time"].to_numpy()
closes = table["close"].to_numpy()
```

### Cross-package example

Putting it all together -- data flows from wrdata through fractime and into wrchart:

```python
from wrdata import DataStream
import fractime as ft
import numpy as np

# Step 1: Collect (wrdata -> Polars DataFrame)
stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")

# Step 2: Convert (Polars -> NumPy)
prices = df["close"].to_numpy()

# Step 3: Forecast (NumPy -> ForecastResult)
result = ft.forecast(prices, horizon=30)

# Step 4: Visualize (NumPy + ForecastResult -> wrchart figure)
fig = ft.plot_forecast(prices[-100:], result)
fig.show()
```

## Runtime Requirements

| Package | Python | Node | C++ Compiler |
|---------|--------|------|--------------|
| wrdata | 3.10+ | -- | -- |
| fractime | 3.10+ | -- | -- |
| wrtrade | 3.8+ | -- | -- |
| wrchart | 3.9+ | -- | -- |
| @wayy/wrchart | -- | 18+ | -- |
| wayy-db | 3.9+ | -- | Required (CMake + pybind11) |

See the [Installation Guide](installation.md) for full setup instructions.

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
