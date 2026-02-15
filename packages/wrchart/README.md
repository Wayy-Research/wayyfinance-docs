# wrchart

Interactive financial charting for Python with Polars support and TradingView-style aesthetics.

## Features

- **Simple API** - Just pass your data, columns are auto-detected
- **Polars-native** - Works directly with Polars DataFrames
- **Auto backend selection** - Automatically picks optimal renderer based on data size
- **Interactive** - TradingView-style pan, zoom, and crosshair
- **Jupyter-ready** - Renders inline in notebooks
- **Non-standard charts** - Renko, Kagi, Point & Figure, Heikin-Ashi, Line Break, Range Bars
- **GPU-accelerated** - WebGL rendering for millions of points at 60fps
- **Drawing tools** - TrendLines, Fibonacci, Rectangles, and more

## Install

```bash
pip install wrchart
```

## Quick Start

```python
import wrchart as wrc
import polars as pl

# Just pass your data - columns are auto-detected
df = pl.read_csv("prices.csv")
wrc.Chart(df).show()

# Or use quick-plot functions
wrc.candlestick(df).show()
wrc.line(df).show()
```

## The Unified Chart

One `Chart` class that figures out the best rendering approach:

```python
# Small OHLC data → Interactive Lightweight Charts
chart = wrc.Chart(daily_prices)

# Large datasets (100k+) → GPU-accelerated WebGL (automatic)
chart = wrc.Chart(tick_data_1M_rows)

# Multiple DataFrames → Multi-panel dashboard
chart = wrc.Chart([df1, df2, df3])
```

## Quick-Plot Functions

One-liners for common chart types:

```python
wrc.candlestick(df).show()           # OHLC candlestick
wrc.line(df).show()                  # Line chart
wrc.area(df).show()                  # Area chart
wrc.dashboard([df1, df2]).show()     # Multi-panel layout
```

## Column Auto-Detection

No need to specify column names - common patterns are auto-detected:

```python
# These all work automatically:
# time, timestamp, date, datetime, t
# open, o, Open, OPEN
# high, h, High, HIGH
# low, l, Low, LOW
# close, c, Close, price, value
# volume, vol, v

chart = wrc.Chart(df)  # Just works
```

Or specify explicitly when needed:

```python
chart.add_candlestick(df, time_col="ts", close_col="px")
```

## Themes

```python
# String shortcuts
chart = wrc.Chart(df, theme="dark")
chart = wrc.Chart(df, theme="light")
chart = wrc.Chart(df, theme="wayy")  # default

# Or use theme constants
chart = wrc.Chart(df, theme=wrc.DARK)
```

## Drawing Tools

```python
from wrchart import TrendLine, HorizontalLine, FibonacciRetracement

chart = wrc.Chart(df)
chart.add_drawing(HorizontalLine(price=100, label="Support"))
chart.add_drawing(TrendLine(
    start_time=t1, start_price=90,
    end_time=t2, end_price=110,
))
chart.add_drawing(FibonacciRetracement(
    start_time=t1, start_price=100,
    end_time=t2, end_price=150,
))
chart.show()
```

Available drawing tools:
- `HorizontalLine`, `VerticalLine`
- `TrendLine`, `Ray`
- `Rectangle`
- `Arrow`, `Text`
- `PriceRange`
- `FibonacciRetracement`, `FibonacciExtension`

## Non-Standard Charts

```python
# Heikin-Ashi (smoothed candles)
ha_data = wrc.to_heikin_ashi(df)
wrc.candlestick(ha_data).show()

# Renko (price-based bricks)
renko_data = wrc.to_renko(df, brick_size=5.0)

# Kagi (reversal lines)
kagi_data = wrc.to_kagi(df, reversal_amount=2.0)

# Point & Figure
pnf_data = wrc.to_point_and_figure(df, box_size=1.0)

# Three Line Break
lb_data = wrc.to_line_break(df, num_lines=3)

# Range Bars
rb_data = wrc.to_range_bars(df, range_size=2.0)
```

## High-Frequency Data

For datasets over 100k points, the WebGL backend is automatically selected:

```python
# 1 million points - automatically uses WebGL
tick_data = pl.DataFrame({
    "time": range(1_000_000),
    "price": prices,
})
wrc.Chart(tick_data).show()  # 60fps rendering
```

Or use LTTB downsampling for Lightweight Charts:

```python
display_data = wrc.lttb_downsample(tick_data, target_points=2000)
wrc.line(display_data).show()
```

## Building Charts Incrementally

```python
chart = wrc.Chart(title="Price Analysis", theme="dark")
chart.add_candlestick(df)
chart.add_volume(df)
chart.add_horizontal_line(100, label="Support", color="#ff0000")
chart.add_marker(time=t, position="aboveBar", shape="arrowDown", text="Signal")
chart.show()
```

## Output Options

```python
chart.show()              # Display in Jupyter or open browser
chart.streamlit()         # Render in Streamlit app
html = chart.to_html()    # Get HTML string
json = chart.to_json()    # Get JSON config
```

## API Reference

### Chart

```python
wrc.Chart(
    data=None,              # DataFrame, list of DataFrames, or None
    width=800,
    height=600,
    theme="wayy",           # "wayy", "dark", "light" or Theme instance
    title=None,
    backend="auto",         # "auto", "lightweight", "webgl", "canvas", "multipanel"
)

# Series methods (columns auto-detected)
chart.add_candlestick(df)
chart.add_line(df)
chart.add_area(df)
chart.add_histogram(df)
chart.add_volume(df)

# Annotations
chart.add_marker(time, position, shape, color, text)
chart.add_horizontal_line(price, color, label)
chart.add_drawing(drawing)

# Output
chart.show()
chart.streamlit()
chart.to_html()
chart.to_json()
```

### Quick-Plot Functions

```python
wrc.candlestick(df, width=800, height=600, theme=None, title=None)
wrc.line(df, ...)
wrc.area(df, ...)
wrc.dashboard(dataframes, rows=None, cols=None, ...)
wrc.forecast(paths, historical, ...)
```

### Transforms

```python
wrc.to_heikin_ashi(df)
wrc.to_renko(df, brick_size)
wrc.to_kagi(df, reversal_amount)
wrc.to_point_and_figure(df, box_size)
wrc.to_line_break(df, num_lines)
wrc.to_range_bars(df, range_size)
wrc.lttb_downsample(df, target_points)
```

## License

MIT License - see LICENSE file for details.
