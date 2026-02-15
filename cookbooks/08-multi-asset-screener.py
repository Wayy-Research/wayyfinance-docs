"""
Cookbook 08: Multi-Asset Screener
==================================
Screen stocks, crypto, and forex for Hurst exponent and
regime characteristics using wrdata + fractime.

Requirements: pip install wrdata fractime
"""

from wrdata import DataStream
import fractime as ft
import numpy as np

# --- Step 1: Define universe ---
universe = {
    "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM"],
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"],
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
}

total = sum(len(v) for v in universe.values())
print(f"Screening {total} symbols across {len(universe)} asset classes\n")

# --- Step 2: Fetch and analyze ---
stream = DataStream()
analyzer = ft.Analyzer()
regime_analyzer = ft.HurstRegimeAnalyzer()

results = []

for asset_class, symbols in universe.items():
    print(f"--- {asset_class.upper()} ---")
    for symbol in symbols:
        try:
            df = stream.get(symbol, start="2024-01-01", interval="1d")
            prices = df["close"].to_numpy()

            if len(prices) < 50:
                print(f"  {symbol}: insufficient data ({len(prices)} bars)")
                continue

            # Fractal analysis
            analysis = analyzer.analyze(prices)
            hurst = analysis.hurst
            fdim = analysis.fractal_dim

            # Regime detection
            regime_result = regime_analyzer.analyze(prices)
            regime = regime_result.regime

            results.append(
                {
                    "symbol": symbol,
                    "asset_class": asset_class,
                    "hurst": hurst,
                    "fractal_dim": fdim,
                    "regime": regime,
                    "bars": len(prices),
                }
            )

            regime_label = (
                "TRENDING" if hurst > 0.55
                else "REVERTING" if hurst < 0.45
                else "RANDOM"
            )
            print(f"  {symbol:>10}: H={hurst:.3f} D={fdim:.3f} [{regime_label}]")

        except Exception as e:
            print(f"  {symbol:>10}: ERROR - {e}")

# --- Step 3: Rank by Hurst ---
print(f"\n{'='*60}")
print(f"SCREENING RESULTS - Sorted by Hurst Exponent")
print(f"{'='*60}")

results.sort(key=lambda x: x["hurst"], reverse=True)

print(f"\n{'Symbol':>10} {'Class':>8} {'Hurst':>7} {'FracDim':>8} {'Regime':>10}")
print("-" * 50)
for r in results:
    regime_label = (
        "TRENDING" if r["hurst"] > 0.55
        else "REVERTING" if r["hurst"] < 0.45
        else "RANDOM"
    )
    print(
        f"{r['symbol']:>10} {r['asset_class']:>8} "
        f"{r['hurst']:>7.3f} {r['fractal_dim']:>8.3f} {regime_label:>10}"
    )

# --- Step 4: Strategy recommendations ---
trending = [r for r in results if r["hurst"] > 0.55]
reverting = [r for r in results if r["hurst"] < 0.45]

print(f"\nMomentum candidates (H > 0.55): {[r['symbol'] for r in trending]}")
print(f"Mean reversion candidates (H < 0.45): {[r['symbol'] for r in reverting]}")

if trending:
    best = trending[0]
    print(f"\nStrongest trend: {best['symbol']} (H={best['hurst']:.3f})")
if reverting:
    best = reverting[0]
    print(f"Strongest reversion: {best['symbol']} (H={best['hurst']:.3f})")
