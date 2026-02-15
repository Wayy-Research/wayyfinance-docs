"""
Basic wrchart examples.

Run in a Jupyter notebook or as a script.
"""

import numpy as np
import polars as pl

# Import wrchart
import sys
sys.path.insert(0, "..")
import wrchart as wrc


def create_sample_ohlcv(n: int = 252) -> pl.DataFrame:
    """Generate sample OHLCV data."""
    np.random.seed(42)

    # Random walk for price
    returns = np.random.randn(n) * 0.02
    prices = 100 * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices
    opens = np.roll(prices, 1)
    opens[0] = prices[0]
    highs = np.maximum(prices, opens) * (1 + np.abs(np.random.randn(n)) * 0.01)
    lows = np.minimum(prices, opens) * (1 - np.abs(np.random.randn(n)) * 0.01)

    # Volume
    volumes = np.random.randint(1000, 10000, n) * (1 + np.abs(returns) * 10)

    return pl.DataFrame({
        "time": list(range(n)),
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
    })


def example_candlestick():
    """Basic candlestick chart with volume."""
    print("Creating candlestick chart...")

    df = create_sample_ohlcv()

    chart = wrc.Chart(width=900, height=500, title="OHLCV Candlestick Chart")
    chart.add_candlestick(df)
    chart.add_volume(df)
    chart.show()


def example_heikin_ashi():
    """Heikin-Ashi smoothed candles."""
    print("Creating Heikin-Ashi chart...")

    df = create_sample_ohlcv()
    ha_df = wrc.to_heikin_ashi(df)

    chart = wrc.Chart(width=900, height=500, title="Heikin-Ashi Chart")
    chart.add_candlestick(ha_df)
    chart.show()


def example_renko():
    """Renko price-based chart."""
    print("Creating Renko chart...")

    df = create_sample_ohlcv(500)  # More data for Renko
    renko_df = wrc.to_renko(df, brick_size=1.0)

    chart = wrc.Chart(width=900, height=500, title="Renko Chart (brick=$1)")
    chart.add_candlestick(renko_df)
    chart.show()


def example_line_with_indicators():
    """Line chart with moving averages."""
    print("Creating line chart with indicators...")

    df = create_sample_ohlcv()

    # Calculate moving averages
    from wrchart.indicators import sma, ema

    sma_20 = sma(df, period=20, value_col="close", output_col="value")
    sma_50 = sma(df, period=50, value_col="close", output_col="value")

    chart = wrc.Chart(width=900, height=500, title="Price with Moving Averages")
    chart.add_candlestick(df)
    chart.add_line(sma_20, color="#E53935", title="SMA 20")
    chart.add_line(sma_50, color="#888888", title="SMA 50")
    chart.show()


def example_tick_data():
    """High-frequency tick data with LTTB downsampling."""
    print("Creating tick data chart...")

    # Generate 100k ticks
    np.random.seed(42)
    n = 100_000
    tick_df = pl.DataFrame({
        "time": list(range(n)),
        "value": 100 + np.cumsum(np.random.randn(n) * 0.01),
    })

    # Downsample to 2000 points
    display_df = wrc.lttb_downsample(tick_df, target_points=2000)

    print(f"Original: {n} points -> Display: {len(display_df)} points")

    chart = wrc.Chart(
        width=900,
        height=400,
        title=f"Tick Data ({n:,} points downsampled to {len(display_df):,})"
    )
    chart.add_line(display_df)
    chart.show()


def example_themes():
    """Different theme options."""
    print("Creating charts with different themes...")

    df = create_sample_ohlcv(100)

    # Wayy theme (default)
    chart1 = wrc.Chart(width=600, height=300, theme=wrc.WayyTheme, title="Wayy Theme")
    chart1.add_candlestick(df)
    chart1.show()

    # Dark theme
    chart2 = wrc.Chart(width=600, height=300, theme=wrc.DarkTheme, title="Dark Theme")
    chart2.add_candlestick(df)
    chart2.show()

    # Light theme
    chart3 = wrc.Chart(width=600, height=300, theme=wrc.LightTheme, title="Light Theme")
    chart3.add_candlestick(df)
    chart3.show()


if __name__ == "__main__":
    # Run examples
    example_candlestick()
    print()
    example_heikin_ashi()
    print()
    example_renko()
    print()
    example_line_with_indicators()
    print()
    example_tick_data()
    print()
    example_themes()
