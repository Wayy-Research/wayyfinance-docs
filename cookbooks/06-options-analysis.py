"""
Cookbook 06: Options Analysis
==============================
Fetch SPY options chain with wrdata, analyze implied volatility
patterns with fractime.

Requirements: pip install wrdata fractime
"""

from wrdata import DataStream
import fractime as ft
import numpy as np

# --- Step 1: Fetch SPY price and options ---
stream = DataStream()

# Get underlying price
df = stream.get("SPY", start="2024-01-01", interval="1d")
spot_price = df["close"][-1]
print(f"SPY spot price: ${spot_price:.2f}")

# Get available expirations
expirations = stream.get_expirations("SPY")
print(f"Available expirations: {len(expirations)}")
print(f"  Nearest: {expirations[0]}")
print(f"  Farthest: {expirations[-1]}")

# --- Step 2: Fetch near-the-money options ---
chain = stream.options(
    "SPY",
    strike_min=spot_price - 20,
    strike_max=spot_price + 20,
)
print(f"\nFetched {len(chain)} option contracts")

# --- Step 3: Analyze IV across strikes ---
calls = chain.filter(chain["option_type"] == "call")
puts = chain.filter(chain["option_type"] == "put")

print(f"\nCalls: {len(calls)}, Puts: {len(puts)}")

# IV smile analysis
if len(calls) > 0:
    call_strikes = calls["strike_price"].to_numpy().astype(float)
    call_ivs = calls["implied_volatility"].to_numpy().astype(float)

    # Filter valid IVs
    valid = ~np.isnan(call_ivs) & (call_ivs > 0)
    call_strikes = call_strikes[valid]
    call_ivs = call_ivs[valid]

    if len(call_ivs) > 0:
        atm_idx = np.argmin(np.abs(call_strikes - spot_price))
        print(f"\nIV Analysis (Calls):")
        print(f"  ATM Strike: ${call_strikes[atm_idx]:.0f}")
        print(f"  ATM IV: {call_ivs[atm_idx]:.1%}")
        print(f"  Min IV: {call_ivs.min():.1%} (strike ${call_strikes[call_ivs.argmin()]:.0f})")
        print(f"  Max IV: {call_ivs.max():.1%} (strike ${call_strikes[call_ivs.argmax()]:.0f})")
        print(f"  IV Skew (25d): {call_ivs[0] - call_ivs[-1]:.1%}")

# --- Step 4: Fractal analysis of historical volatility ---
prices = df["close"].to_numpy()
analyzer = ft.Analyzer()
analysis = analyzer.analyze(prices)

print(f"\nHistorical Volatility (Fractal Analysis):")
print(f"  Hurst Exponent: {analysis.hurst:.3f}")
print(f"  Fractal Dimension: {analysis.fractal_dim:.3f}")

# Compare realized vol to implied vol
log_returns = np.diff(np.log(prices))
realized_vol = np.std(log_returns) * np.sqrt(252)
print(f"  Realized Vol (annualized): {realized_vol:.1%}")

if len(call_ivs) > 0:
    atm_iv = call_ivs[atm_idx]
    vol_premium = atm_iv - realized_vol
    print(f"  ATM IV: {atm_iv:.1%}")
    print(f"  Vol Premium (IV - RV): {vol_premium:.1%}")
    if vol_premium > 0.05:
        print("  -> Options appear expensive relative to realized vol")
    elif vol_premium < -0.02:
        print("  -> Options appear cheap relative to realized vol")
    else:
        print("  -> Options fairly priced")
