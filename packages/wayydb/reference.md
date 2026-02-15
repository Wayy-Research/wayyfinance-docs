# wayy-db -- API Reference

> Version: 0.1.0 | Python >=3.9 | Install: `pip install wayy-db`

High-performance columnar time-series database with a C++20 engine, Python bindings via pybind11, and kdb+-style temporal joins. Designed for quantitative finance workflows where as-of joins, window aggregations, and zero-copy NumPy interop matter.

Requires a C++ compiler (GCC 10+ or Clang 13+) and CMake for building native extensions. numpy >=1.20 is the only runtime dependency.

```bash
pip install wayy-db               # Core library
pip install wayy-db[api]          # + FastAPI streaming server
pip install wayy-db[bench]        # + Benchmark suite (pandas, polars, duckdb)
```

---

## Quick Start

```python
import wayy_db
import numpy as np

# Create tables from dicts of numpy arrays
trades = wayy_db.from_dict({
    "time": np.array([1, 2, 3, 4, 5], dtype=np.int64),
    "price": np.array([100.0, 101.5, 99.8, 102.0, 103.5]),
    "size": np.array([10, 20, 15, 30, 5], dtype=np.int64),
}, name="trades", sorted_by="time")

quotes = wayy_db.from_dict({
    "time": np.array([1, 3, 5], dtype=np.int64),
    "bid": np.array([99.5, 99.0, 102.5]),
    "ask": np.array([100.5, 100.0, 103.5]),
}, name="quotes", sorted_by="time")

# As-of join: get the latest quote at each trade time
result = wayy_db.ops.aj(trades, quotes, on=[], as_of="time")

# Zero-copy column access
prices = result["price"].to_numpy()  # No data copied
spreads = result["ask"].to_numpy() - result["bid"].to_numpy()

# SIMD-accelerated aggregation
avg_price = wayy_db.ops.avg(trades["price"])
total_volume = wayy_db.ops.sum(trades["size"])
```

---

## Core API

### Convenience Constructors

These are the primary ways to create tables. All live at the top-level `wayy_db` module.

#### `wayy_db.from_dict(data, name="", sorted_by=None) -> Table`

Create a Table from a dictionary mapping column names to numpy arrays.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `dict[str, np.ndarray]` | required | Column name to array mapping |
| `name` | `str` | `""` | Table name (used in Database lookups) |
| `sorted_by` | `str \| None` | `None` | Column to mark as sorted index |

Supported dtypes: `int64` -> `DType.Int64`, `float64` -> `DType.Float64`, `uint32` -> `DType.Symbol`, `uint8` -> `DType.Bool`. Integer and float subtypes are auto-cast to `int64` / `float64`. Other dtypes raise `ValueError`.

```python
import wayy_db
import numpy as np

ohlcv = wayy_db.from_dict({
    "timestamp": np.arange(1000, dtype=np.int64),
    "open":  np.random.uniform(99, 101, 1000),
    "high":  np.random.uniform(100, 102, 1000),
    "low":   np.random.uniform(98, 100, 1000),
    "close": np.random.uniform(99, 101, 1000),
    "volume": np.random.randint(100, 10000, 1000).astype(np.int64),
}, name="SPY_1m", sorted_by="timestamp")

print(ohlcv.num_rows)      # 1000
print(ohlcv.num_columns)   # 6
print(ohlcv.column_names()) # ['timestamp', 'open', 'high', 'low', 'close', 'volume']
```

#### `wayy_db.from_pandas(df, name="", sorted_by=None) -> Table`

Create a Table from a pandas DataFrame. Internally calls `df[col].values` for each column, then delegates to `from_dict`.

```python
import pandas as pd
import wayy_db

df = pd.DataFrame({"time": [1, 2, 3], "price": [100.0, 101.5, 99.8]})
table = wayy_db.from_pandas(df, name="prices", sorted_by="time")
```

#### `wayy_db.from_polars(df, name="", sorted_by=None) -> Table`

Create a Table from a polars DataFrame. Internally calls `df[col].to_numpy()` for each column, then delegates to `from_dict`.

```python
import polars as pl
import wayy_db

df = pl.DataFrame({"time": [1, 2, 3], "price": [100.0, 101.5, 99.8]})
table = wayy_db.from_polars(df, name="prices", sorted_by="time")
```

---

### `Table`

Columnar table backed by typed arrays. Supports indexing by column name, persistence, and memory-mapping.

```python
from wayy_db import Table
```

#### Construction

```python
table = Table(name="")  # Empty table, add columns with add_column_from_numpy()
```

In practice, use `from_dict`, `from_pandas`, or `from_polars` instead.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Table name |
| `num_rows` | `int` | Number of rows |
| `num_columns` | `int` | Number of columns |
| `sorted_by` | `str \| None` | Name of the sorted index column, or `None` |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__len__` | `() -> int` | Same as `num_rows` |
| `__getitem__` | `(name: str) -> Column` | Get column by name. Raises `ColumnNotFound`. |
| `column` | `(name: str) -> Column` | Same as `__getitem__` |
| `has_column` | `(name: str) -> bool` | Check if column exists |
| `column_names` | `() -> list[str]` | All column names in insertion order |
| `set_sorted_by` | `(col: str) -> None` | Mark a column as the sorted index |
| `add_column_from_numpy` | `(name: str, array: np.ndarray, dtype: DType) -> None` | Add a column from a numpy array |
| `to_dict` | `() -> dict[str, np.ndarray]` | Export all columns as `{name: array}` |
| `save` | `(path: str) -> None` | Persist table to disk |
| `Table.load` | `(path: str) -> Table` | Load table from disk (static method) |
| `Table.mmap` | `(path: str) -> Table` | Memory-map table from disk (static method, near-instant) |

---

### `Column`

A typed, named column backed by a contiguous array. Accessed via `table["column_name"]`.

| Property/Method | Type | Description |
|----------------|------|-------------|
| `name` | `str` | Column name |
| `dtype` | `DType` | Column data type |
| `size` | `int` | Number of elements |
| `__len__` | `int` | Same as `size` |
| `to_numpy()` | `np.ndarray` | Zero-copy view (mmap) or copy of the underlying data |

```python
col = table["price"]
print(col.name)        # 'price'
print(col.dtype)       # DType.Float64
print(len(col))        # 1000
arr = col.to_numpy()   # numpy array, zero-copy when memory-mapped
```

---

### `Database`

Persistent container that manages multiple tables on disk.

```python
from wayy_db import Database

# In-memory database
db = Database()

# Persistent database at a directory path
db = Database("/tmp/my_market_data")
```

| Property/Method | Signature | Description |
|----------------|-----------|-------------|
| `path` | `str` | Database directory path |
| `is_persistent` | `bool` | `True` if backed by a directory |
| `tables` | `() -> list[str]` | List all table names |
| `has_table` | `(name: str) -> bool` | Check if table exists |
| `__getitem__` | `(name: str) -> Table` | Get table by name |
| `table` | `(name: str) -> Table` | Same as `__getitem__` |
| `create_table` | `(name: str) -> Table` | Create a new empty table |
| `drop_table` | `(name: str) -> None` | Remove a table |
| `save` | `() -> None` | Persist all tables to disk |
| `refresh` | `() -> None` | Reload tables from disk |

---

### `DType`

Type enum for columns. All storage is fixed-width for SIMD alignment.

| Variant | Storage | Description |
|---------|---------|-------------|
| `DType.Int64` | 8 bytes | 64-bit signed integer |
| `DType.Float64` | 8 bytes | 64-bit IEEE double |
| `DType.Timestamp` | 8 bytes | Alias for Int64 (semantic marker) |
| `DType.Symbol` | 4 bytes | Interned string (max 4 bytes, dictionary encoded) |
| `DType.Bool` | 1 byte | Boolean |

---

### Operations (`wayy_db.ops`)

All operations are implemented in C++. Aggregations use AVX2 SIMD intrinsics (processing 4 doubles per cycle). Joins use binary search on sorted indices.

```python
from wayy_db import ops
# or
import wayy_db
wayy_db.ops.sum(...)
```

#### Aggregations

All aggregation functions take a `Column` and return a `float`.

| Function | Signature | Description |
|----------|-----------|-------------|
| `ops.sum(col)` | `(Column) -> float` | Sum of all values (SIMD) |
| `ops.avg(col)` | `(Column) -> float` | Arithmetic mean (SIMD) |
| `ops.min(col)` | `(Column) -> float` | Minimum value (SIMD) |
| `ops.max(col)` | `(Column) -> float` | Maximum value (SIMD) |
| `ops.std(col)` | `(Column) -> float` | Standard deviation (SIMD) |

```python
import wayy_db

table = wayy_db.from_dict({
    "price": np.array([100.0, 101.5, 99.8, 102.0, 103.5]),
}, name="prices")

total = wayy_db.ops.sum(table["price"])     # 506.8
mean  = wayy_db.ops.avg(table["price"])     # 101.36
lo    = wayy_db.ops.min(table["price"])     # 99.8
hi    = wayy_db.ops.max(table["price"])     # 103.5
vol   = wayy_db.ops.std(table["price"])     # ~1.39
```

#### Temporal Joins

##### `ops.aj(left, right, on, as_of) -> Table`

As-of join. For each row in `left`, finds the most recent matching row in `right` where `right.as_of <= left.as_of`. O(n log m) via binary search on the sorted as-of column.

| Parameter | Type | Description |
|-----------|------|-------------|
| `left` | `Table` | Left table (drives the join) |
| `right` | `Table` | Right table (looked up) |
| `on` | `Sequence[str]` | Exact-match columns (e.g., `["symbol"]`). Pass `[]` for no grouping. |
| `as_of` | `str` | Temporal column name. Must exist in both tables. Both tables must be `sorted_by` this column. |

Returns a new `Table` with all columns from `left` plus all non-key columns from `right`.

```python
import wayy_db
import numpy as np

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

# For trade at time=10, gets quote at time=5
# For trade at time=20, gets quote at time=15
# For trade at time=30, gets quote at time=15 (most recent)
# For trade at time=40, gets quote at time=35
result = wayy_db.ops.aj(trades, quotes, on=[], as_of="time")
```

##### `ops.wj(left, right, on, as_of, window_before, window_after) -> Table`

Window join. For each row in `left`, collects all rows from `right` within a time window `[left.as_of - window_before, left.as_of + window_after]`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `left` | `Table` | Left table |
| `right` | `Table` | Right table |
| `on` | `Sequence[str]` | Exact-match columns |
| `as_of` | `str` | Temporal column name |
| `window_before` | `int` | Lookback window (same units as `as_of` column) |
| `window_after` | `int` | Lookahead window |

```python
# Get all quotes within +/- 5 time units of each trade
result = wayy_db.ops.wj(
    trades, quotes,
    on=[], as_of="time",
    window_before=5, window_after=5,
)
```

#### Moving / Window Functions

All moving functions take a `Column` and `window: int`, returning a `np.ndarray[float64]`. The first `window - 1` values are `NaN`.

| Function | Signature | Description |
|----------|-----------|-------------|
| `ops.mavg(col, window)` | `(Column, int) -> np.ndarray` | Moving average |
| `ops.msum(col, window)` | `(Column, int) -> np.ndarray` | Moving sum |
| `ops.mstd(col, window)` | `(Column, int) -> np.ndarray` | Moving standard deviation |
| `ops.mmin(col, window)` | `(Column, int) -> np.ndarray` | Moving minimum |
| `ops.mmax(col, window)` | `(Column, int) -> np.ndarray` | Moving maximum |

```python
prices = table["close"]
sma_20 = wayy_db.ops.mavg(prices, 20)   # 20-period SMA
bb_std = wayy_db.ops.mstd(prices, 20)   # For Bollinger Bands
```

#### Other Column Operations

| Function | Signature | Description |
|----------|-----------|-------------|
| `ops.ema(col, alpha)` | `(Column, float) -> np.ndarray` | Exponential moving average. `alpha` is the smoothing factor (0 < alpha <= 1). |
| `ops.diff(col, periods=1)` | `(Column, int) -> np.ndarray` | First difference. `diff[i] = col[i] - col[i - periods]`. |
| `ops.pct_change(col, periods=1)` | `(Column, int) -> np.ndarray` | Percent change. `pct[i] = (col[i] - col[i-periods]) / col[i-periods]`. |
| `ops.shift(col, n)` | `(Column, int) -> np.ndarray` | Shift values by `n` positions. Positive shifts forward (introduces leading NaN). |

```python
# 12-period EMA (alpha = 2 / (12 + 1))
ema_12 = wayy_db.ops.ema(table["close"], alpha=2/13)

# Daily returns
returns = wayy_db.ops.pct_change(table["close"])

# Lag by 1 for signal alignment (avoid lookahead bias)
lagged = wayy_db.ops.shift(table["close"], 1)
```

---

### Exceptions

All exceptions inherit from `WayyException`.

| Exception | When Raised |
|-----------|-------------|
| `WayyException` | Base class for all wayy-db errors |
| `ColumnNotFound` | Accessing a column that does not exist in the table |
| `TypeMismatch` | Operation on incompatible column types |
| `InvalidOperation` | General operation error (e.g., join on unsorted table) |

```python
from wayy_db import ColumnNotFound

try:
    col = table["nonexistent"]
except ColumnNotFound as e:
    print(f"Column not found: {e}")
```

---

## Common Patterns

### As-of join trades with quotes

The primary use case. Match each trade to the most recent quote at or before that trade's timestamp.

```python
import wayy_db
import numpy as np

trades = wayy_db.from_dict({
    "time": np.array([100, 200, 300, 400, 500], dtype=np.int64),
    "symbol": np.array([1, 1, 2, 1, 2], dtype=np.uint32),
    "price": np.array([50.10, 50.25, 30.50, 50.30, 30.55]),
    "qty": np.array([100, 200, 150, 300, 50], dtype=np.int64),
}, name="trades", sorted_by="time")

quotes = wayy_db.from_dict({
    "time": np.array([90, 150, 250, 350], dtype=np.int64),
    "symbol": np.array([1, 2, 1, 2], dtype=np.uint32),
    "bid": np.array([50.00, 30.40, 50.20, 30.50]),
    "ask": np.array([50.10, 30.50, 50.30, 30.60]),
}, name="quotes", sorted_by="time")

joined = wayy_db.ops.aj(trades, quotes, on=["symbol"], as_of="time")
# Each trade now has the prevailing bid/ask at the time of execution
```

### Compute indicators on price data

```python
import wayy_db
import numpy as np

prices = wayy_db.from_dict({
    "time": np.arange(500, dtype=np.int64),
    "close": np.cumsum(np.random.randn(500) * 0.5) + 100,
}, name="prices", sorted_by="time")

close = prices["close"]

sma_20  = wayy_db.ops.mavg(close, 20)
sma_50  = wayy_db.ops.mavg(close, 50)
ema_12  = wayy_db.ops.ema(close, alpha=2/13)
ema_26  = wayy_db.ops.ema(close, alpha=2/27)
macd    = ema_12 - ema_26
returns = wayy_db.ops.pct_change(close)
vol_20  = wayy_db.ops.mstd(close, 20)
```

### Persist and memory-map for fast reload

```python
import wayy_db

# Save to disk
table.save("/tmp/trades.wayy")

# Load via mmap -- near-instant regardless of size
table = wayy_db.Table.mmap("/tmp/trades.wayy")

# Or use Database for multi-table management
db = wayy_db.Database("/tmp/market_db")
db.create_table("trades")
# ... add columns, then:
db.save()

# Later:
db = wayy_db.Database("/tmp/market_db")
trades = db["trades"]
```

### Ingest wrdata output into wayyDB

```python
import wrdata
import wayy_db
import numpy as np

# Fetch OHLCV via wrdata (returns Polars DataFrame)
df = wrdata.get_ohlcv("AAPL", interval="1d", period="2y")

# Convert Polars -> wayyDB Table
table = wayy_db.from_polars(df, name="AAPL_daily", sorted_by="timestamp")

# Now use temporal operations
mavg = wayy_db.ops.mavg(table["close"], 20)
```

### Window join: all quotes around each trade

```python
# Get all quotes within 100ms of each trade
result = wayy_db.ops.wj(
    trades, quotes,
    on=["symbol"],
    as_of="time",
    window_before=100,   # 100 units before
    window_after=0,      # None after (causal)
)
```

---

## Gotchas

**C++ compiler required.** `pip install wayy-db` compiles native extensions. You need GCC 10+, Clang 13+, or MSVC 2019+ with C++20 support, plus CMake. On Ubuntu: `apt install build-essential cmake`. On macOS: `xcode-select --install`. Pre-built wheels are available for common platforms via cibuildwheel.

**Tables must be sorted for joins.** Both `aj` and `wj` require that the tables are sorted by the `as_of` column. Set this at creation time with `sorted_by="column_name"`. If you forget, joins will silently produce wrong results -- there is no runtime check for sort order.

**DType.Symbol is 4 bytes max.** The Symbol type uses 4-byte interned strings, not arbitrary-length strings. It is designed for short identifiers like ticker symbols ("AAPL", "GOOG"). For longer strings, store them separately and use integer keys.

**Zero-copy NumPy only works with mmap.** When a table is loaded via `Table.mmap()`, `column.to_numpy()` returns a zero-copy view backed by the memory-mapped file. Tables created in-memory via `from_dict()` return a copy.

**SIMD acceleration requires AVX2.** The SIMD-accelerated aggregations (`sum`, `avg`, `min`, `max`, `std`) use AVX2 instructions. This covers most x86-64 CPUs from 2013 onward. On CPUs without AVX2, the library falls back to scalar operations.

**`ops.shift` with positive n shifts forward.** `shift(col, 1)` introduces a `NaN` at position 0 and moves all values one position later. This is the correct direction for avoiding lookahead bias: `shifted_signal = ops.shift(signal, 1)` gives you yesterday's signal for today's trade.

**Column operations return numpy arrays, not Columns.** Moving functions, `ema`, `diff`, `pct_change`, and `shift` all return `np.ndarray[float64]`. To put the result back into a table, use `table.add_column_from_numpy("name", array, DType.Float64)`.

**from_pandas / from_polars copy data.** These constructors extract numpy arrays from the DataFrame. The resulting Table owns its own memory. Changes to the original DataFrame do not propagate.

**Python >=3.9.** While the `pyproject.toml` lists `>=3.9`, the convenience constructors `from_dict`, `from_pandas`, and `from_polars` use `str | None` syntax which requires `from __future__ import annotations` (included). Runtime works on 3.9+.

---

## Integration

**Data ingestion from wrdata.** Fetch market data with [wrdata](../wrdata/reference.md) (Polars DataFrames), convert to wayyDB tables with `from_polars()`, then run temporal joins and aggregations at C++ speed.

**Forecasting with fractime.** Compute indicators in wayyDB, extract numpy arrays with `col.to_numpy()`, feed them into [fractime](../fractime/reference.md) for Hurst exponent analysis or fractal forecasting.

**Backtesting with wrtrade.** Use wayyDB for point-in-time data reconstruction via as-of joins (avoiding lookahead bias), then pass clean signals to [wrtrade](../wrtrade/reference.md) for strategy evaluation.

**Benchmarking.** Run the built-in benchmark suite to compare against pandas, polars, and duckdb on your hardware:

```bash
pip install wayy-db[bench]
python -m benchmarks.benchmark --compare pandas,polars,duckdb
```

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY.
*People for research, research for people.*
