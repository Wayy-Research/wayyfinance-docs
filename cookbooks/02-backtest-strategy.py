"""
Cookbook 02: Backtest Strategy
==============================
Build a moving average crossover strategy, backtest on BTC with wrtrade,
and validate with permutation testing.

Requirements: pip install wrdata wrtrade
"""

from wrdata import DataStream
import wrtrade as wrt
import polars as pl

# --- Step 1: Fetch BTC data ---
stream = DataStream()
df = stream.get("BTC-USD", start="2023-01-01", interval="1d")
prices = df["close"]
print(f"Fetched {len(prices)} days of BTC-USD data")

# --- Step 2: Define signal function ---
def ma_crossover(prices: pl.Series) -> pl.Series:
    """Buy when 10-day MA > 30-day MA, sell when below."""
    fast = prices.rolling_mean(10)
    slow = prices.rolling_mean(30)
    return (fast > slow).cast(int) - (fast < slow).cast(int)


# --- Step 3: Build portfolio ---
builder = wrt.NDimensionalPortfolioBuilder()
component = builder.create_signal_component(
    "MA_Crossover", ma_crossover, weight=1.0
)
portfolio = builder.create_portfolio("BTC_Strategy", [component])

# --- Step 4: Backtest ---
manager = wrt.AdvancedPortfolioManager(portfolio)
results = manager.backtest(prices)

print(f"\nBacktest Results:")
print(f"  Total Return: {results['total_return']:.2%}")
print(f"  Sortino Ratio: {results['portfolio_metrics']['sortino_ratio']:.2f}")
print(f"  Max Drawdown: {results['portfolio_metrics']['max_drawdown']:.2%}")
print(f"  Volatility: {results['portfolio_metrics']['volatility']:.2%}")

# --- Step 5: Validate with permutation test ---
print(f"\nRunning permutation test (1000 permutations)...")
test = manager.run_permutation_test(
    prices, n_permutations=1000, metric="sortino_ratio"
)

print(f"  Real Sortino: {test['real_performance']:.3f}")
print(f"  Random Mean: {test['permutation_mean']:.3f}")
print(f"  P-Value: {test['p_value']:.4f}")

if test["p_value"] < 0.05:
    print("  Result: Strategy is statistically significant!")
else:
    print("  Result: Strategy may be overfitting")

# --- Step 6: Print tear sheet ---
print(f"\n--- Tear Sheet ---")
wrt.tear_sheet(results["portfolio_returns"])
