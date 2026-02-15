# wrchart -- API Reference

> Version: 0.2.0 | Python: 3.9+ | Install: `pip install wrchart`

Interactive financial charting library with Polars-native data handling, TradingView-style aesthetics, and support for standard and non-standard chart types (Renko, Kagi, P&F). Auto-selects rendering backend based on data size.

---

## Quick Start

```python
import wrchart as wrc
import polars as pl

df = pl.read_csv("prices.csv")
wrc.Chart(df).show()                     # Auto-detects columns and chart type

wrc.candlestick(df).show()               # Explicit candlestick
wrc.line(df, title="Close Price").show()  # Line chart
```

---

## Core API

### `Chart`

Unified chart class with automatic backend selection. This is the primary class for all charting.

```python
class Chart:
    def __init__(
        self,
        data: pl.DataFrame | list[pl.DataFrame] | dict | None = None,
        width: int = 800,
        height: int = 600,
        theme: str | Theme | None = None,    # "wayy", "dark", "light", or Theme
        title: str | None = None,
        backend: str = "auto",                # "auto","lightweight","webgl","canvas","multipanel"
    )
```

Backend auto-selection:
- Small OHLC data -> Interactive Lightweight Charts
- Large datasets (100k+ rows) -> GPU-accelerated WebGL
- Forecast paths -> Canvas density visualization
- Multiple DataFrames -> Multi-panel grid layout

#### Series Methods

All return `self` for method chaining.

```python
chart.add_candlestick(
    data: pl.DataFrame,
    time_col: str | None = None,       # All columns are auto-detected
    open_col: str | None = None,       # if not specified
    high_col: str | None = None,
    low_col: str | None = None,
    close_col: str | None = None,
) -> Chart

chart.add_line(
    data: pl.DataFrame,
    time_col: str | None = None,
    value_col: str | None = None,
    **options,                          # color, title, etc.
) -> Chart

chart.add_area(
    data: pl.DataFrame,
    time_col: str | None = None,
    value_col: str | None = None,
    **options,
) -> Chart

chart.add_histogram(
    data: pl.DataFrame,
    time_col: str | None = None,
    value_col: str | None = None,
    color_col: str | None = None,
    **options,
) -> Chart

chart.add_volume(
    data: pl.DataFrame,
    time_col: str | None = None,
    volume_col: str | None = None,
    open_col: str | None = None,
    close_col: str | None = None,
    up_color: str | None = None,
    down_color: str | None = None,
) -> Chart
```

#### Annotation Methods

```python
chart.add_marker(
    time: Any,
    position: str = "aboveBar",       # "aboveBar", "belowBar", "inBar"
    shape: str = "circle",            # "circle", "square", "arrowUp", "arrowDown"
    color: str | None = None,
    text: str = "",
    size: int = 1,
) -> Chart

chart.add_horizontal_line(
    price: float,
    color: str | None = None,
    line_width: int = 1,
    line_style: int = 0,              # 0=solid, 1=dotted, 2=dashed
    label: str = "",
    label_visible: bool = True,
) -> Chart

chart.add_drawing(drawing: BaseDrawing) -> Chart
```

#### Output Methods

```python
chart.show() -> None                  # Jupyter inline or browser
chart.streamlit(height=None) -> None  # Streamlit component
chart.to_html() -> str                # Raw HTML string
chart.to_json() -> str                # JSON configuration
```

#### Method Chaining Example

```python
chart = (
    wrc.Chart(width=1000, height=600, theme="dark", title="AAPL")
    .add_candlestick(ohlcv_df)
    .add_volume(ohlcv_df)
    .add_line(sma_df, color="#2196F3", title="SMA 20")
    .add_horizontal_line(150.0, color="red", label="Support")
    .add_marker("2024-06-15", shape="arrowUp", color="green", text="Buy")
)
chart.show()
```

---

### Quick-Plot Functions

One-line chart creation. All return a `Chart` instance.

```python
wrc.candlestick(
    data: pl.DataFrame,
    width: int = 800,
    height: int = 600,
    theme: str | Theme | None = None,
    title: str | None = None,
) -> Chart

wrc.line(data, width=800, height=600, theme=None, title=None) -> Chart
wrc.area(data, width=800, height=600, theme=None, title=None) -> Chart

wrc.forecast(
    paths: np.ndarray,                # (n_paths, n_steps)
    historical: np.ndarray | pl.Series | list,
    probabilities: np.ndarray | None = None,
    weighted_forecast: np.ndarray | None = None,
    width: int = 1000,
    height: int = 600,
    theme: str | Theme | None = "dark",
    title: str | None = None,
) -> Chart

wrc.dashboard(
    dataframes: list[pl.DataFrame],
    rows: int | None = None,          # Auto-calculated
    cols: int | None = None,          # Auto-calculated, max 3
    width: int = 1200,
    height: int = 800,
    theme: str | Theme | None = None,
    title: str | None = None,
) -> Chart
```

```python
wrc.candlestick(df).show()
wrc.line(close_df, title="Price History").show()

# Multi-panel dashboard
wrc.dashboard([price_df, volume_df, rsi_df], cols=1).show()

# Forecast visualization with Monte Carlo paths
wrc.forecast(result.paths, prices, result.probabilities).show()
```

---

### `DataSchema`

Column auto-detection for DataFrames.

```python
class DataSchema:
    @staticmethod
    def detect(df: pl.DataFrame) -> dict
    @staticmethod
    def infer_chart_type(df: pl.DataFrame) -> str    # "candlestick" or "line"
    @staticmethod
    def get_ohlc_cols(df, time=None, open_=None, high=None, low=None, close=None) -> dict
    @staticmethod
    def get_time_col(df, override=None) -> str
    @staticmethod
    def get_value_col(df, override=None) -> str
```

Auto-detects columns named `date`/`time`/`timestamp`, `open`/`Open`/`o`, `high`/`High`/`h`, etc.

---

## Themes

Three built-in themes, accessible as classes or strings:

| Theme | String | Background | Primary Colors |
|-------|--------|------------|----------------|
| `WayyTheme` | `"wayy"` / `WAYY` | White | Black, Red (#E53935) |
| `DarkTheme` | `"dark"` / `DARK` | Dark (#1a1a2e) | White, Red |
| `LightTheme` | `"light"` / `LIGHT` | Gray (#f0f0f0) | Teal, Red |

```python
# All equivalent
chart = wrc.Chart(df, theme="dark")
chart = wrc.Chart(df, theme=wrc.DARK)
chart = wrc.Chart(df, theme=wrc.DarkTheme())

# Custom theme
from wrchart import Theme
my_theme = Theme(
    background="#0a0a0a",
    text_color="#ffffff",
    up_color="#00e676",
    down_color="#ff1744",
    grid_color="#333333",
)
```

Helper functions:

```python
wrc.get_theme("dark") -> Theme
wrc.resolve_theme("dark") -> Theme     # Also accepts Theme instances and None
```

---

## Transforms

Convert OHLCV DataFrames to alternative chart types. All take a Polars DataFrame and return a Polars DataFrame.

```python
from wrchart import (
    to_heikin_ashi,
    to_renko,
    to_kagi,
    to_point_and_figure,
    to_line_break,
    to_range_bars,
    lttb_downsample,
    adaptive_downsample,
)
```

| Function | Parameters | Description |
|----------|-----------|-------------|
| `to_heikin_ashi(df)` | DataFrame with OHLC | Smoothed candlesticks |
| `to_renko(df, brick_size)` | DataFrame + brick size | Price-only bricks |
| `to_kagi(df, reversal_amount)` | DataFrame + reversal threshold | Kagi direction chart |
| `to_point_and_figure(df, box_size, reversal_boxes)` | DataFrame + box config | P&F X/O chart |
| `to_line_break(df, num_lines)` | DataFrame + line count | Line break chart |
| `to_range_bars(df, range_size)` | DataFrame + range | Equal-range bars |
| `lttb_downsample(df, target_points)` | DataFrame + target | LTTB decimation |
| `adaptive_downsample(df, target_points)` | DataFrame + target | Adaptive decimation |

```python
# Renko chart
renko_df = wrc.to_renko(ohlcv_df, brick_size=5.0)
wrc.candlestick(renko_df, title="AAPL Renko").show()

# Heikin-Ashi smoothing
ha_df = wrc.to_heikin_ashi(ohlcv_df)
wrc.candlestick(ha_df, title="Heikin-Ashi").show()

# Downsample 1M points for display
downsampled = wrc.lttb_downsample(big_df, target_points=5000)
wrc.line(downsampled).show()
```

---

## Indicators

Technical indicators that operate on Polars DataFrames.

```python
from wrchart.indicators import sma, ema, wma, bollinger_bands, rsi, macd, stochastic
```

| Function | Returns | Description |
|----------|---------|-------------|
| `sma(df, period, col="close")` | `pl.Series` | Simple Moving Average |
| `ema(df, period, col="close")` | `pl.Series` | Exponential Moving Average |
| `wma(df, period, col="close")` | `pl.Series` | Weighted Moving Average |
| `bollinger_bands(df, period, std_dev)` | `tuple[pl.Series, pl.Series, pl.Series]` | Upper, middle, lower bands |
| `rsi(df, period=14, col="close")` | `pl.Series` | Relative Strength Index |
| `macd(df, fast=12, slow=26, signal=9)` | `tuple[pl.Series, pl.Series, pl.Series]` | MACD, signal, histogram |
| `stochastic(df, k_period=14, d_period=3)` | `tuple[pl.Series, pl.Series]` | %K, %D |

```python
from wrchart.indicators import sma, rsi, bollinger_bands

sma_20 = sma(df, 20)
rsi_14 = rsi(df, 14)
upper, middle, lower = bollinger_bands(df, 20, 2.0)
```

---

## Multi-Panel Charts

Grid layouts with heterogeneous panel types.

```python
from wrchart import MultiPanelChart, LinePanel, BarPanel, HeatmapPanel, GaugePanel, AreaPanel

class MultiPanelChart:
    def __init__(
        self,
        rows: int,
        cols: int,
        width: int = 1200,
        height: int = 800,
        row_heights: list[float] | None = None,
        col_widths: list[float] | None = None,
    )
```

Panel types:

| Panel | Description |
|-------|-------------|
| `LinePanel` | Line chart panel |
| `BarPanel` | Bar/histogram panel |
| `HeatmapPanel` | Heatmap panel |
| `GaugePanel` | Gauge/meter panel |
| `AreaPanel` | Area chart panel |

```python
chart = wrc.MultiPanelChart(rows=3, cols=1, row_heights=[0.5, 0.25, 0.25])
# Add panels with data...
chart.show()
```

---

## Forecast Visualization

Specialized chart for Monte Carlo forecast paths with probability-weighted density coloring.

```python
from wrchart import ForecastChart, VIRIDIS, PLASMA, INFERNO, HOT

class ForecastChart:
    def __init__(
        self,
        width: int = 1000,
        height: int = 600,
        theme: str | Theme | None = "dark",
        title: str | None = None,
    )

    def set_data(prices, result) -> self
    def set_colorscale(scale) -> self        # VIRIDIS, PLASMA, INFERNO, HOT
    def set_max_paths(n: int) -> self
```

Helper functions for density computation:

```python
from wrchart import density_to_color, compute_path_density, compute_path_colors_by_density
```

```python
# Quick way (use the quick-plot function)
wrc.forecast(result.paths, prices, result.probabilities).show()

# Detailed way
fc = wrc.ForecastChart(title="S&P 500 Forecast")
fc.set_data(prices, result)
fc.set_colorscale(wrc.PLASMA)
fc.set_max_paths(200)
fc.show()
```

---

## Drawing Tools

Annotation objects for technical analysis drawings.

```python
from wrchart import (
    HorizontalLine,
    VerticalLine,
    TrendLine,
    Ray,
    Rectangle,
    Arrow,
    Text,
    PriceRange,
    FibonacciRetracement,
    FibonacciExtension,
    export_drawings,
    import_drawings,
)
```

| Drawing | Key Parameters |
|---------|----------------|
| `HorizontalLine` | `price, color, line_width, line_style` |
| `VerticalLine` | `time, color, line_width` |
| `TrendLine` | `start_time, start_price, end_time, end_price, color` |
| `Ray` | `start_time, start_price, end_time, end_price` |
| `Rectangle` | `start_time, start_price, end_time, end_price, color, fill_color` |
| `Arrow` | `time, price, direction, color` |
| `Text` | `time, price, text, color, font_size` |
| `PriceRange` | `start_price, end_price, color` |
| `FibonacciRetracement` | `start_time, start_price, end_time, end_price, levels` |
| `FibonacciExtension` | `start_time, start_price, end_time, end_price, levels` |

```python
chart = wrc.Chart(df)
chart.add_drawing(wrc.TrendLine("2024-01-15", 150, "2024-06-15", 180, color="blue"))
chart.add_drawing(wrc.FibonacciRetracement("2024-01-01", 140, "2024-03-01", 190))
chart.show()

# Export/import drawings
drawings_json = wrc.export_drawings([line, fib])
restored = wrc.import_drawings(drawings_json)
```

---

## Financial Helpers

Pre-built chart compositions for common financial visualizations.

```python
from wrchart import (
    returns_distribution,
    price_with_indicator,
    indicator_panels,
    equity_curve,
    drawdown_chart,
    rolling_sharpe,
)
```

| Function | Description |
|----------|-------------|
| `returns_distribution(returns)` | Histogram of return distribution |
| `price_with_indicator(df, indicator_df)` | Price chart overlaid with indicator |
| `indicator_panels(df, indicators)` | Multi-panel with price + indicators |
| `equity_curve(returns)` | Cumulative returns area chart |
| `drawdown_chart(returns)` | Drawdown visualization |
| `rolling_sharpe(returns, window)` | Rolling Sharpe ratio chart |

```python
wrc.equity_curve(strategy_returns).show()
wrc.drawdown_chart(strategy_returns).show()
wrc.returns_distribution(strategy_returns).show()
```

---

## Series Types (Advanced)

For direct series construction when you need fine-grained control:

```python
from wrchart import CandlestickSeries, LineSeries, AreaSeries, HistogramSeries, ScatterSeries
```

Most users should use `Chart.add_candlestick()`, etc. instead.

---

## Live Streaming (Optional)

Requires websockets. Not imported by default.

```python
from wrchart import LiveChart, LiveTable, LiveDashboard, LiveServer
```

| Class | Description |
|-------|-------------|
| `LiveChart` | Chart that updates with streaming data |
| `LiveTable` | Real-time data table |
| `LiveDashboard` | Multi-widget live dashboard |
| `LiveServer` | WebSocket server for pushing updates |

Available only if websockets is installed. Check with `wrc._HAS_LIVE`.

---

## Common Patterns

### 1. OHLCV candlestick with volume

```python
import wrchart as wrc

chart = (
    wrc.Chart(width=1000, height=600, theme="dark", title="AAPL")
    .add_candlestick(df)
    .add_volume(df)
)
chart.show()
```

### 2. Price with moving averages

```python
from wrchart.indicators import sma, ema

df_with_sma = df.with_columns([
    sma(df, 20).alias("sma_20"),
    ema(df, 50).alias("ema_50"),
])

sma_df = df.select(["timestamp", "sma_20"]).rename({"sma_20": "value"})
ema_df = df.select(["timestamp", "ema_50"]).rename({"ema_50": "value"})

chart = (
    wrc.Chart(title="AAPL + Moving Averages")
    .add_candlestick(df)
    .add_line(sma_df, color="#2196F3", title="SMA 20")
    .add_line(ema_df, color="#FF9800", title="EMA 50")
)
chart.show()
```

### 3. Alternative chart types

```python
# Renko
renko = wrc.to_renko(df, brick_size=2.0)
wrc.candlestick(renko, title="Renko").show()

# Heikin-Ashi
ha = wrc.to_heikin_ashi(df)
wrc.candlestick(ha, title="Heikin-Ashi").show()

# Point & Figure
pnf = wrc.to_point_and_figure(df, box_size=1.0, reversal_boxes=3)
```

### 4. Forecast visualization from fractime

```python
import fractime as ft
import wrchart as wrc

result = ft.forecast(prices, horizon=30)
wrc.forecast(
    paths=result.paths,
    historical=prices,
    probabilities=result.probabilities,
    title="30-Day Forecast",
).show()
```

### 5. Backtest equity curve from wrtrade

```python
import wrtrade as wrt
import wrchart as wrc

result = portfolio.backtest(prices)
wrc.equity_curve(result.returns).show()
wrc.drawdown_chart(result.returns).show()
```

---

## Gotchas

| Pitfall | Details |
|---------|---------|
| **Input must be Polars DataFrame** | All chart methods expect `pl.DataFrame`. Convert pandas with `pl.from_pandas(pdf)`. |
| **WebGLChart is deprecated** | Use `Chart()` which auto-selects backend. For explicit WebGL: `Chart(backend="webgl")`. |
| **Column names are auto-detected** | Works with `date`/`time`/`timestamp`, `open`/`Open`/`o`, etc. Override with explicit column params if detection fails. |
| **Method chaining supported** | All `.add_*` methods return `self`. Build charts fluently. |
| **Jupyter auto-renders** | `Chart` implements `_repr_html_()`. In Jupyter, just put the chart object as the last expression in a cell. |
| **Large data auto-switches backend** | Datasets over 100k rows automatically use WebGL. You can force `backend="lightweight"` but performance may suffer. |
| **Transforms return new DataFrames** | `to_renko()`, `to_heikin_ashi()`, etc. do not modify the original DataFrame. |
| **Live features require websockets** | `LiveChart`, `LiveTable`, etc. are `None` if websockets is not installed. |

---

## Integration

### wrchart <- wrdata (data in)

```python
from wrdata import DataStream
import wrchart as wrc

stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")

# Column names match -- auto-detected
wrc.candlestick(df, title="AAPL").show()
```

### wrchart <- fractime (forecast visualization)

```python
import fractime as ft
import wrchart as wrc

result = ft.forecast(prices, horizon=30)

# Quick-plot function
wrc.forecast(result.paths, prices, result.probabilities).show()

# Or use fractime's built-in (wraps wrchart)
ft.plot_forecast(prices, result)
```

### wrchart <- wrtrade (backtest visualization)

```python
import wrtrade as wrt
import wrchart as wrc

result = portfolio.backtest(prices)

# wrtrade's built-in (uses wrchart)
result.plot().show()

# Or direct
wrc.equity_curve(result.returns).show()
wrc.drawdown_chart(result.returns).show()
wrc.rolling_sharpe(result.returns, window=63).show()
```

### wrchart in Streamlit

```python
import streamlit as st
import wrchart as wrc

chart = wrc.candlestick(df, theme="dark")
chart.streamlit(height=500)
```

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY.
*People for research, research for people.*
