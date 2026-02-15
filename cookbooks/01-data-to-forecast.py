"""
Cookbook 01: Data to Forecast
=============================
Fetch AAPL data with wrdata, analyze fractal properties with fractime,
generate a 30-day forecast, and visualize with wrchart.

Requirements: pip install wrdata fractime wrchart
"""

from wrdata import DataStream
import fractime as ft
import numpy as np

# --- Step 1: Fetch data ---
stream = DataStream()
df = stream.get("AAPL", start="2024-01-01", interval="1d")
print(f"Fetched {len(df)} rows of AAPL data")
print(df.head())

# --- Step 2: Extract prices ---
prices = df["close"].to_numpy()

# --- Step 3: Analyze fractal properties ---
analyzer = ft.Analyzer()
result = analyzer.analyze(prices)
print(f"\nFractal Analysis:")
print(f"  Hurst Exponent: {result.hurst:.3f}")
print(f"  Fractal Dimension: {result.fractal_dim:.3f}")

if result.hurst > 0.55:
    print("  Interpretation: Trending (persistent) market")
elif result.hurst < 0.45:
    print("  Interpretation: Mean-reverting (antipersistent) market")
else:
    print("  Interpretation: Near random walk")

# --- Step 4: Generate 30-day forecast ---
forecaster = ft.Forecaster(n_paths=1000)
forecaster.fit(prices)
forecast = forecaster.predict(horizon=30)

print(f"\n30-Day Forecast:")
print(f"  Current Price: ${prices[-1]:.2f}")
print(f"  Forecast Mean: ${forecast.mean[-1]:.2f}")
print(f"  Lower (5th %%): ${forecast.lower[-1]:.2f}")
print(f"  Upper (95th %%): ${forecast.upper[-1]:.2f}")

# --- Step 5: Visualize ---
fig = ft.plot_forecast(
    prices[-100:],
    forecast,
    title="AAPL - 30 Day Fractal Forecast",
    colorscale="Viridis",
    max_paths=500,
)
fig.show()

print("\nForecast chart opened in browser.")
