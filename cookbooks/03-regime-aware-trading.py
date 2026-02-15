"""
Cookbook 03: Regime-Aware Trading
=================================
Use fractime's HurstRegimeAnalyzer to detect market regimes,
then adapt trading strategy allocation using wrtrade.

Requirements: pip install wrdata fractime wrtrade
"""

from wrdata import DataStream
import fractime as ft
import wrtrade as wrt
import polars as pl
import numpy as np

# --- Step 1: Fetch data ---
stream = DataStream()
df = stream.get("SPY", start="2023-01-01", interval="1d")
prices_np = df["close"].to_numpy()
prices_pl = df["close"]
print(f"Fetched {len(prices_np)} days of SPY data")

# --- Step 2: Analyze regime ---
regime_analyzer = ft.HurstRegimeAnalyzer()
regime_result = regime_analyzer.analyze(prices_np)

print(f"\nRegime Analysis:")
print(f"  Current Hurst: {regime_result.hurst:.3f}")
print(f"  Regime: {regime_result.regime}")
print(f"  Confidence: {regime_result.confidence:.2%}")

# --- Step 3: Define regime-adaptive signals ---
def momentum_signal(prices: pl.Series) -> pl.Series:
    """Momentum: buy when 20-day return > 0."""
    ret = prices.pct_change(20)
    return (ret > 0.02).cast(int) - (ret < -0.02).cast(int)


def reversion_signal(prices: pl.Series) -> pl.Series:
    """Mean reversion: buy when below 20-day SMA, sell when above."""
    sma = prices.rolling_mean(20)
    std = prices.rolling_std(20)
    z = (prices - sma) / std
    return (z < -1.5).cast(int) - (z > 1.5).cast(int)


# --- Step 4: Build regime-adaptive portfolio ---
builder = wrt.NDimensionalPortfolioBuilder()

# Weight based on regime
if regime_result.hurst > 0.55:
    print("\nTrending regime detected - favoring momentum")
    mom_weight, rev_weight = 0.8, 0.2
elif regime_result.hurst < 0.45:
    print("\nMean-reverting regime detected - favoring reversion")
    mom_weight, rev_weight = 0.2, 0.8
else:
    print("\nRandom walk regime - equal weights")
    mom_weight, rev_weight = 0.5, 0.5

portfolio = builder.create_portfolio(
    "Regime_Adaptive",
    [
        builder.create_signal_component("Momentum", momentum_signal, weight=mom_weight),
        builder.create_signal_component("Reversion", reversion_signal, weight=rev_weight),
    ],
)

# --- Step 5: Backtest ---
manager = wrt.AdvancedPortfolioManager(portfolio)
results = manager.backtest(prices_pl)

print(f"\nBacktest Results (regime-adaptive):")
print(f"  Total Return: {results['total_return']:.2%}")
print(f"  Sortino Ratio: {results['portfolio_metrics']['sortino_ratio']:.2f}")
print(f"  Max Drawdown: {results['portfolio_metrics']['max_drawdown']:.2%}")

# --- Step 6: Validate ---
test = manager.run_permutation_test(
    prices_pl, n_permutations=500, metric="sortino_ratio"
)
print(f"\nPermutation Test P-Value: {test['p_value']:.4f}")

# --- Step 7: Forecast with regime context ---
forecaster = ft.Forecaster(n_paths=1000)
forecaster.fit(prices_np)
forecast = forecaster.predict(horizon=30)

print(f"\n30-Day Forecast (regime-informed):")
print(f"  Current: ${prices_np[-1]:.2f}")
print(f"  Forecast: ${forecast.mean[-1]:.2f}")
print(f"  Range: ${forecast.lower[-1]:.2f} - ${forecast.upper[-1]:.2f}")
