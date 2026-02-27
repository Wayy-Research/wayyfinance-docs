# Our Approach to Quantitative Finance

> Markets are not random. They are not predictable either. The truth is more useful than both.

This guide introduces the ideas behind the wayyFinance ecosystem. If you already know what a Hurst exponent is and just want to install things, go to the [Getting Started](../overview/getting-started.md) guide. This is for people who want to understand *why* we built these tools and what makes this approach different.

## The Core Idea: Markets Have Memory

Most introductory finance courses teach the Efficient Market Hypothesis (EMH) and random walk theory. The implication: price movements are independent, past prices tell you nothing about future prices, and technical analysis is astrology.

This is a useful simplification. It is also wrong in practice.

Financial time series exhibit **long-range dependence**. A trending day is more likely to be followed by another trending day. A volatile week tends to cluster with other volatile weeks. This memory structure is measurable, and it varies over time.

The tool for measuring it is the **Hurst exponent**, introduced by Harold Edwin Hurst in 1951 while studying Nile river flood patterns. It quantifies the degree of persistence (or anti-persistence) in a time series:

| Hurst Value | Behavior | What It Means |
|-------------|----------|---------------|
| H < 0.5 | Anti-persistent (mean-reverting) | Price tends to reverse direction. A move up makes a move down more likely. |
| H = 0.5 | Random walk | No exploitable memory. Past prices tell you nothing. |
| H > 0.5 | Persistent (trending) | Price tends to continue its direction. Momentum exists. |

We estimate it using Detrended Fluctuation Analysis (DFA), which handles non-stationary financial data better than the classical R/S method. In code:

```python
import fractime as ft
from wrdata import DataStream

stream = DataStream()
df = stream.get("AAPL", start="2023-01-01")  # Returns a Polars DataFrame
prices = df["close"].to_numpy()               # Zero-copy to NumPy

analyzer = ft.Analyzer(prices, method="dfa")
print(f"Hurst: {analyzer.hurst.value:.3f}")
print(f"Regime: {analyzer.regime}")  # 'trending', 'mean_reverting', or 'random'
```

The wayyFinance ecosystem uses [Polars](https://pola.rs/) for DataFrames -- not Pandas. `wrdata` returns Polars DataFrames. `wrtrade` signal functions take and return `pl.Series`. Convert between Polars and NumPy with `df["close"].to_numpy()`. If you need Pandas, call `df.to_pandas()`.

If the Hurst exponent comes back at 0.62, that is a quantitative statement: this series has persistent memory. Momentum-style strategies have a structural reason to work on it. If it comes back at 0.43, mean-reversion strategies have the structural advantage.

This is the foundation of everything else we build.

## Why Not Just Predict Prices?

A common first instinct is to train a model that outputs "the price will be $187.50 on March 15th." This is seductive and almost always wrong.

Price prediction fails for several reasons:

1. **Non-stationarity.** The statistical properties of financial series change over time. A model trained on 2023 data may describe a market that no longer exists in 2025.
2. **Regime dependence.** A trending market and a mean-reverting market require opposite strategies. A single model that ignores regimes will be right half the time and catastrophically wrong the other half.
3. **Noise dominance.** On daily data, signal-to-noise ratios are typically 0.05-0.15. The noise is 7-20x louder than the signal. Point predictions absorb all of it.

Our approach sidesteps this. Instead of predicting prices, we **characterize the market's current behavior** and build strategies that exploit that characterization.

The output of `ft.forecast()` is not a price target. It is a probability distribution:

```python
model = ft.Forecaster(prices, method="dfa")
result = model.predict(steps=30, n_paths=2000)

# Not "the price will be X" -- instead:
lo, hi = result.ci(0.90)
print(f"90% CI in 30 days: [{lo[-1]:.2f}, {hi[-1]:.2f}]")
print(f"Median path: {result.forecast[-1]:.2f}")
```

This gives you 2,000 Monte Carlo paths weighted by the fractal properties of the series. You get a range of outcomes with probabilities attached. That is something you can actually trade on.

## Regimes: The Market Changes Character

A Hurst exponent computed over a full year tells you the average memory structure. But markets switch between regimes -- trending for three months, then choppy for two, then trending again.

We use Hidden Markov Models (HMMs) to detect these regime shifts in real time:

```python
import numpy as np

detector = ft.RegimeDetector(n_regimes=2)
returns = np.diff(prices) / prices[:-1]
detector.fit(returns)

regime, probability = detector.get_current_regime(returns)
print(f"Current regime: {regime} ({probability:.0%} confidence)")
# HMM regime: 'bull', 'bear', or 'sideways'
```

Note the two regime systems in the ecosystem. The Hurst-based regime from `ft.Analyzer` (`'trending'`, `'mean_reverting'`, `'random'`) describes memory structure. The HMM-based regime from `ft.RegimeDetector` (`'bull'`, `'bear'`, `'sideways'`) describes market direction. They measure different things and are complementary.

The regime detector identifies the current state of the market and the probability of being in that state. This unlocks **regime-adaptive strategies**: allocate more to momentum signals in bull regimes, more to mean-reversion signals in bear or sideways regimes.

```python
import wrtrade as wrt
import polars as pl

def trend_signal(prices: pl.Series) -> pl.Series:
    fast = prices.rolling_mean(window_size=10)
    slow = prices.rolling_mean(window_size=50)
    return (fast > slow).cast(pl.Int8).fill_null(0)

def reversion_signal(prices: pl.Series) -> pl.Series:
    z = (prices - prices.rolling_mean(20)) / prices.rolling_std(20)
    return pl.when(z < -2).then(1).when(z > 2).then(-1).otherwise(0).fill_null(0).cast(pl.Int8)

# Set static portfolio weights based on detected regime
# Re-create the portfolio when the regime changes
trend_weight = 0.8 if regime == "bull" else 0.3
reversion_weight = 1.0 - trend_weight

portfolio = wrt.Portfolio([
    ("trend", trend_signal, trend_weight),
    ("reversion", reversion_signal, reversion_weight),
])
```

Portfolio weights are fixed at construction time. In practice, you re-run regime detection periodically (e.g. weekly) and rebuild the portfolio when the regime changes. The principle applies broadly: measure the market's character *before* choosing how to trade it.

## Don't Fool Yourself

The easiest person to fool in quantitative finance is yourself. A backtest with 15 tuned parameters will always look great on historical data. It will almost certainly fail in production.

We enforce three layers of protection against self-deception:

### 1. Walk-Forward Validation

Never test on the same data you used to build the strategy. Train on 2020-2023, test on 2024. Never go back and adjust.

This is the same principle as train/test splits in machine learning, but the temporal ordering matters more. You cannot shuffle financial data -- the future must always come after the past.

### 2. Permutation Testing

After backtesting, ask: "Could random data have produced this result?"

Permutation testing shuffles the price series (destroying any real structure) and re-runs the backtest thousands of times. If your strategy performs equally well on shuffled data, the original result was noise.

```python
result = wrt.backtest(my_signal, prices)
p_value = wrt.validate(my_signal, prices, n_permutations=1000)

if p_value < 0.05:
    print(f"Edge is statistically significant (p={p_value:.3f})")
else:
    print(f"Likely overfit (p={p_value:.3f}) -- do not deploy")
```

A p-value below 0.05 means that fewer than 5% of random permutations matched your strategy's performance. It does not guarantee the strategy will work in the future, but it does tell you the result is unlikely to be pure luck.

### 3. Economic Rationale

Every strategy should have a reason to work that you can explain in plain language. "Trending markets tend to continue trending because of herding behavior and delayed information absorption" is a reason. "I found these 12 parameters that happened to work on 2022 data" is not.

## Position Sizing: Where the Money Is

Most beginners focus on entry signals. Professionals focus on position sizing.

Two strategies with identical signals but different position sizing will produce wildly different outcomes. The Kelly criterion gives mathematically optimal sizing based on your edge and win rate:

```python
optimizer = wrt.KellyOptimizer()
full_kelly = optimizer.calculate_discrete_kelly(result.returns)
print(f"Full Kelly fraction: {full_kelly:.1%}")
```

**Never use full Kelly.** Full Kelly maximizes long-run geometric growth, but tolerates drawdowns exceeding 50%. In practice, use a quarter:

```python
quarter_kelly = full_kelly * 0.25
print(f"Quarter Kelly: {quarter_kelly:.1%}")
```

Quarter Kelly significantly reduces variance and drawdown risk at the cost of slower compounding. This is the right trade-off for almost everyone.

## The Workflow

Putting it together, the workflow we advocate looks like this:

```
1. Measure  --> Compute Hurst exponent and detect regime
2. Decide   --> Is the market forecastable? (H significantly != 0.5)
3. Build    --> Choose signal type that matches the regime
4. Test     --> Walk-forward backtest with transaction costs
5. Validate --> Permutation test (p < 0.05?)
6. Size     --> Quarter-Kelly position sizing
7. Paper    --> Paper-trade for at least 30 days
8. Deploy   --> Live with risk limits (stop loss, max position, max daily loss)
```

Each step has a gate. If the Hurst exponent is near 0.5, stop at step 2 -- the market is not forecastable right now. If the permutation test fails at step 5, stop -- your edge is not real. If paper trading diverges from the backtest at step 7, stop -- something is wrong with execution.

Most of the value is in knowing when *not* to trade.

In code, steps 1-6 look like this:

```python
from wrdata import DataStream
import fractime as ft
import wrtrade as wrt
import polars as pl

# 1. Measure
stream = DataStream()
df = stream.get("AAPL", start="2023-01-01")
prices = df["close"].to_numpy()
analyzer = ft.Analyzer(prices, method="dfa")

# 2. Decide
lower, upper = analyzer.hurst.ci(0.95)
if lower <= 0.45 and upper >= 0.55:
    print("Hurst CI spans 0.5 -- market structure unclear, skip")
    exit()

# 3. Build (trending market -> momentum signal)
def momentum(prices: pl.Series) -> pl.Series:
    return (prices.pct_change(20) > 0).cast(pl.Int8).fill_null(0)

# 4. Test
result = wrt.backtest(momentum, df["close"])

# 5. Validate
p_value = wrt.validate(momentum, df["close"], n_permutations=1000)
if p_value >= 0.05:
    print(f"Permutation test failed (p={p_value:.3f}) -- no real edge")
    exit()

# 6. Size
optimizer = wrt.KellyOptimizer()
full_kelly = optimizer.calculate_discrete_kelly(result.returns)
position_size = full_kelly * 0.25  # Quarter-Kelly
print(f"Position size: {position_size:.1%} of capital")
print(f"Sortino: {result.sortino:.2f} | p-value: {p_value:.3f}")
```

## What This Approach Is Not

**Not a black box.** Every number has a meaning. The Hurst exponent measures memory. Regime detection classifies market behavior. Permutation testing quantifies statistical significance. You should understand what each component does.

**Not a guarantee.** Markets change. A Hurst exponent of 0.65 today does not mean the market will be persistent next month. The approach tells you what is happening *now* and gives you a framework for adapting when it changes.

**Not high-frequency.** The tools work on daily to weekly timeframes. Intraday data is supported (wrdata streams tick data, wayy-db handles microsecond-resolution as-of joins), but the fractal analysis is most reliable on daily bars with 200+ observations.

**Not just for quants.** If you can write a Python function, you can use these tools. The math is handled by the libraries. The important part is the discipline: measure before you trade, validate before you deploy, size before you risk.

## Next Steps

- **[Getting Started](../overview/getting-started.md)** -- install the tools and run your first forecast in 2 minutes
- **[Quant Pitfalls](quant-pitfalls.md)** -- the bugs that silently corrupt results (lookahead bias, float precision, timezone errors)
- **[Cookbook 01: Data to Forecast](../cookbooks/01-data-to-forecast.py)** -- full end-to-end example
- **[Cookbook 03: Regime-Aware Trading](../cookbooks/03-regime-aware-trading.py)** -- adaptive strategies using regime detection
- **[Ecosystem Overview](../overview/ecosystem.md)** -- which package does what

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*9 years of institutional experience, pip-installable.*
*People for research, research for people.*
