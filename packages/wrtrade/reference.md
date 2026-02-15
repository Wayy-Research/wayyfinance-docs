# wrtrade -- API Reference

> Version: 2.1.1 | Python: 3.10+ | Install: `pip install wrtrade`

Ultra-fast backtesting and trading framework built on Polars. Define signal functions, backtest in one line, validate with permutation testing, optimize with Kelly criterion, and deploy to live brokers.

---

## Quick Start

```python
import wrtrade as wrt
import polars as pl

def sma_crossover(prices: pl.Series) -> pl.Series:
    fast = prices.rolling_mean(window_size=10)
    slow = prices.rolling_mean(window_size=50)
    return (fast > slow).cast(pl.Int8).fill_null(0)    # 1=buy, 0=flat

result = wrt.backtest(sma_crossover, prices)
print(f"Sortino: {result.sortino:.2f}")
result.tear_sheet()
```

---

## Core API

These are the functions and classes most users need. Everything below fits on one screen.

### `backtest`

One-line backtest of a signal function against a price series.

```python
def backtest(
    signal_func: Callable[[pl.Series], pl.Series],
    prices: pl.Series,
) -> Result
```

```python
result = wrt.backtest(my_signal, prices)
print(result.sortino)
print(result.max_drawdown)
```

### `validate`

Permutation testing to determine if a signal has statistically significant edge.

```python
def validate(
    signal_func: Callable[[pl.Series], pl.Series],
    prices: pl.Series,
    n_permutations: int = 1000,
) -> float   # p-value
```

```python
p_value = wrt.validate(my_signal, prices, n_permutations=1000)
if p_value < 0.05:
    print("Signal has statistically significant edge")
else:
    print("Signal may be overfitting or spurious")
```

### `optimize`

Kelly criterion optimization of position sizing.

```python
def optimize(
    signal_func: Callable[[pl.Series], pl.Series],
    prices: pl.Series,
) -> dict
```

```python
optimal = wrt.optimize(my_signal, prices)
print(f"Optimal Kelly fraction: {optimal['kelly_fraction']:.2f}")
```

### `tear_sheet`

Print a formatted performance report from a returns series.

```python
def tear_sheet(returns: pl.Series) -> None
```

```python
wrt.tear_sheet(returns)
# ==================================================
#            PERFORMANCE TEAR SHEET
# ==================================================
# Volatility (Annualized):     0.1823
# Sortino Ratio:               1.4521
# Gain to Pain Ratio:          1.2341
# Max Drawdown:               -0.0892
# ==================================================
```

---

### `Portfolio`

Core portfolio data type. Holds one or more signals with weights and can backtest, validate, and optimize itself.

```python
class Portfolio:
    def __init__(
        self,
        signals: SignalFunc | list[SignalSpec] | dict[str, SignalSpec],
        name: str | None = None,
        max_position: float = 1.0,       # 1.0 = 100%
        take_profit: float | None = None, # e.g., 0.05 for 5%
        stop_loss: float | None = None,   # e.g., 0.02 for 2%
    )
```

**Signal format options:**

```python
# Single function
portfolio = wrt.Portfolio(my_signal)

# List of (function, weight) tuples
portfolio = wrt.Portfolio([
    (trend_signal, 0.6),
    (momentum_signal, 0.4),
])

# List of (name, function, weight) tuples
portfolio = wrt.Portfolio([
    ("trend", trend_signal, 0.6),
    ("momentum", momentum_signal, 0.4),
])

# Dictionary
portfolio = wrt.Portfolio({
    "trend": (trend_signal, 0.6),
    "momentum": (momentum_signal, 0.4),
})

# With risk controls
portfolio = wrt.Portfolio(
    my_signal,
    max_position=0.5,
    take_profit=0.10,
    stop_loss=0.03,
)
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `.backtest(prices, benchmark=True, risk_free_rate=0.0)` | `Result` | Run backtest |
| `.validate(prices, n_permutations=1000)` | `float` | Permutation test p-value |
| `.optimize(prices)` | `dict` | Kelly optimization |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `.weights` | `dict[str, float]` | Current signal weights (read/write) |

```python
portfolio = wrt.Portfolio([
    (trend_signal, 0.6),
    (momentum_signal, 0.4),
])

result = portfolio.backtest(prices)
print(f"Sortino: {result.sortino:.2f}")
result.tear_sheet()

# Adjust weights
portfolio.weights = {"trend_signal": 0.7, "momentum_signal": 0.3}
```

---

### `Result`

Backtest result with metrics as attributes.

```python
@dataclass
class Result:
    returns: pl.Series
    total_return: float
    sortino: float
    sharpe: float
    max_drawdown: float
    volatility: float
    gain_to_pain: float

    # Optional (present when benchmark=True)
    positions: pl.Series | None
    benchmark_returns: pl.Series | None
    benchmark_total_return: float | None
    excess_return: float | None

    # Multi-signal attribution
    attribution: dict[str, float] | None

    def tear_sheet() -> None          # Print formatted report
    def plot(interactive=True)        # Plot equity curve (wrchart or matplotlib)
```

```python
result = portfolio.backtest(prices)

# Access metrics
print(result.sortino)           # 1.45
print(result.max_drawdown)      # -0.089
print(result.total_return)      # 0.342
print(result.excess_return)     # 0.127

# Formatted report
result.tear_sheet()

# Visual
chart = result.plot()
chart.show()

# Component attribution (multi-signal portfolios)
if result.attribution:
    for name, contrib in result.attribution.items():
        print(f"  {name}: {contrib:.4f}")
```

---

### Signal Functions

A signal function has the signature:

```python
def signal(prices: pl.Series) -> pl.Series
```

Return values: `1` = buy/long, `0` = flat/hold, `-1` = sell/short.

```python
def sma_crossover(prices: pl.Series) -> pl.Series:
    fast = prices.rolling_mean(window_size=10)
    slow = prices.rolling_mean(window_size=50)
    return (fast > slow).cast(pl.Int8).fill_null(0)

def mean_reversion(prices: pl.Series) -> pl.Series:
    z_score = (prices - prices.rolling_mean(20)) / prices.rolling_std(20)
    signal = pl.when(z_score < -2).then(1).when(z_score > 2).then(-1).otherwise(0)
    return signal.fill_null(0).cast(pl.Int8)

def momentum(prices: pl.Series) -> pl.Series:
    returns_20d = prices.pct_change(20)
    return (returns_20d > 0).cast(pl.Int8).fill_null(0)
```

---

## Full API

### Metrics

```python
from wrtrade import calculate_all_metrics, calculate_all_rolling_metrics

# All metrics at once
metrics = wrt.calculate_all_metrics(returns)
# {'volatility': 0.18, 'sortino_ratio': 1.45, 'gain_to_pain_ratio': 1.23, 'max_drawdown': -0.089}

# Rolling metrics for plotting
rolling = wrt.calculate_all_rolling_metrics(returns, window=252)
# {'rolling_volatility': pl.Series, 'rolling_sortino': pl.Series, ...}
```

Individual metric functions (all in `wrtrade.metrics`):

| Function | Signature | Description |
|----------|-----------|-------------|
| `volatility(returns)` | `pl.Series -> float` | Annualized volatility |
| `sortino_ratio(returns, rfr=0.0)` | `pl.Series -> float` | Sortino ratio |
| `gain_to_pain_ratio(returns)` | `pl.Series -> float` | Sum of gains / sum of losses |
| `max_drawdown(returns)` | `pl.Series -> float` | Maximum drawdown |
| `rolling_volatility(returns, window=252)` | `pl.Series -> pl.Series` | Rolling annualized vol |
| `rolling_max_drawdown(returns, window=252)` | `pl.Series -> pl.Series` | Rolling max drawdown |
| `rolling_metric(returns, func, window=252)` | `pl.Series -> pl.Series` | Any metric, rolling |

---

### `PermutationTester`

Statistical validation of trading signals through permutation testing.

```python
class PermutationTester:
    def __init__(config: PermutationConfig | None = None)

    def run_insample_test(prices, signal_func) -> dict
    def run_walkforward_test(prices, signal_func) -> dict
```

```python
@dataclass
class PermutationConfig:
    n_permutations: int = 1000
    start_index: int = 0
    preserve_gaps: bool = True
    parallel: bool = True
    n_workers: int | None = None
    random_seed: int | None = None
```

```python
tester = wrt.PermutationTester(
    wrt.PermutationConfig(n_permutations=2000, random_seed=42)
)
result = tester.run_insample_test(prices, my_signal)
print(f"p-value: {result['p_value']:.4f}")
```

---

### `KellyOptimizer`

Kelly criterion optimization for position sizing.

```python
class KellyOptimizer:
    def __init__(config: KellyConfig | None = None)

    def calculate_discrete_kelly(returns, risk_free_rate=None) -> float
    def calculate_portfolio_kelly(component_returns_dict) -> dict
    def calculate_fractional_kelly(returns, fraction=0.25) -> float
```

```python
@dataclass
class KellyConfig:
    lookback_window: int = 252
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_leverage: float = 1.0
    regularization_lambda: float = 0.01
    rebalance_frequency: int = 21        # Monthly
    risk_free_rate: float = 0.02
    min_observations: int = 60
    max_iterations: int = 1000
    convergence_tolerance: float = 1e-6
    use_constraints: bool = True
    allow_short: bool = False
```

```python
optimizer = wrt.KellyOptimizer()
kelly_f = optimizer.calculate_discrete_kelly(returns)
print(f"Full Kelly: {kelly_f:.2%}")

# Fractional Kelly (recommended for real trading)
frac_kelly = optimizer.calculate_fractional_kelly(returns, fraction=0.25)
print(f"Quarter Kelly: {frac_kelly:.2%}")
```

### `HierarchicalKellyOptimizer`

Nested portfolio optimization for multi-level signal hierarchies.

---

### Components (Hierarchical Portfolios)

For complex multi-strategy portfolios.

```python
from wrtrade import SignalComponent, CompositePortfolio

@dataclass
class SignalComponent:
    name: str
    signal_func: Callable
    weight: float
    max_position: float = 1.0
    take_profit: float | None = None
    stop_loss: float | None = None

class CompositePortfolio:
    def __init__(
        name: str,
        components: list[PortfolioComponent],
        weight: float = 1.0,
        rebalance_frequency: int | None = None,
        kelly_optimization: bool = False,
    )
```

---

### Builder (Legacy API)

Prefer `Portfolio` for new code. The builder pattern is still available:

```python
from wrtrade import NDimensionalPortfolioBuilder, AdvancedPortfolioManager

builder = NDimensionalPortfolioBuilder()
builder.register_signal("ma_fast", fast_ma_signal)
builder.register_signal("ma_slow", slow_ma_signal)

comp = builder.create_signal_component("ma_fast", fast_ma_signal, weight=0.6)
portfolio = builder.create_portfolio("MyStrategy", [comp])

manager = AdvancedPortfolioManager(portfolio)
results = manager.backtest(prices)
# results: dict with portfolio_returns, benchmark_returns, portfolio_metrics, total_return, excess_return
```

---

### Deployment

Deploy strategies to live/paper brokers.

```python
from wrtrade import deploy, DeployConfig

@dataclass
class DeployConfig:
    broker: str = "alpaca"
    paper: bool = True
    max_position_pct: float = 0.10
    max_daily_loss_pct: float = 0.05
    validate: bool = True
    min_sortino: float = 1.0
    api_key: str | None = None         # Auto-reads from env
    secret_key: str | None = None      # Auto-reads from env
```

```python
deployment_id = await wrt.deploy(
    portfolio,
    symbols={"trend": "AAPL", "momentum": "AAPL"},
    config=wrt.DeployConfig(broker="alpaca", paper=True),
)
```

Supported brokers: `alpaca`, `robinhood`. Installable extras: `pip install wrtrade[alpaca]` or `pip install wrtrade[all]`.

CLI:

```bash
wrtrade strategy deploy my_strategy.yaml
wrtrade strategy start deployment-id
wrtrade strategy stop deployment-id
wrtrade strategy status deployment-id
```

---

### Charts (wrchart integration)

```python
from wrtrade import BacktestChart, plot_backtest

# Quick plot
chart = wrt.plot_backtest(result)
chart.show()

# Full chart builder
chart = wrt.BacktestChart(result)
chart.show()

# Individual chart types
from wrtrade import price_chart, line_chart, area_chart, histogram, bar_chart, indicator_panel
```

---

## Common Patterns

### 1. Backtest a signal and validate it

```python
import wrtrade as wrt

def my_signal(prices):
    fast = prices.rolling_mean(window_size=10)
    slow = prices.rolling_mean(window_size=50)
    return (fast > slow).cast(pl.Int8).fill_null(0)

result = wrt.backtest(my_signal, prices)
print(f"Sortino: {result.sortino:.2f}")
print(f"Sharpe:  {result.sharpe:.2f}")
print(f"Max DD:  {result.max_drawdown:.2%}")

p_value = wrt.validate(my_signal, prices)
print(f"p-value: {p_value:.4f}")
```

### 2. Multi-signal portfolio with attribution

```python
portfolio = wrt.Portfolio([
    ("trend", trend_signal, 0.4),
    ("momentum", momentum_signal, 0.3),
    ("reversion", mean_reversion_signal, 0.3),
])

result = portfolio.backtest(prices)
result.tear_sheet()

for name, contrib in result.attribution.items():
    print(f"  {name}: {contrib:.4f}")
```

### 3. Optimize position sizing with fractional Kelly

```python
optimizer = wrt.KellyOptimizer()
full_kelly = optimizer.calculate_discrete_kelly(result.returns)
quarter_kelly = optimizer.calculate_fractional_kelly(result.returns, fraction=0.25)
print(f"Full Kelly says {full_kelly:.1%} -- using quarter Kelly: {quarter_kelly:.1%}")
```

### 4. Full pipeline: data -> signal -> validate -> deploy

```python
from wrdata import DataStream
import wrtrade as wrt

stream = DataStream()
df = stream.get("AAPL", start="2020-01-01")
prices = df["close"]

result = wrt.backtest(my_signal, prices)
p_value = wrt.validate(my_signal, prices)

if p_value < 0.05 and result.sortino > 1.0:
    await wrt.deploy(
        portfolio,
        symbols={"signal": "AAPL"},
        config=wrt.DeployConfig(paper=True),
    )
```

---

## Gotchas

| Pitfall | Details |
|---------|---------|
| **Signals must be lagged** | wrtrade applies `positions.shift(1)` internally. You generate the signal at time t, the position is applied at t+1. This prevents lookahead bias. |
| **All Polars, not pandas** | Signal functions receive and return `pl.Series`. Convert with `series.to_pandas()` if needed. |
| **Permutation test before deploying** | Always run `validate()` with p<0.05 before trusting a signal. Many strategies are overfit. |
| **Full Kelly is too aggressive** | Use fractional Kelly (0.25 is standard). Full Kelly maximizes growth but tolerates massive drawdowns. |
| **Signal values must be -1, 0, or 1** | Fractional values are clipped to `[-max_position, max_position]`. |
| **Take profit / stop loss are optional** | They add execution logic but also complexity. Start without them. |
| **Benchmark is buy-and-hold** | `result.excess_return` is versus buy-and-hold, not a market index. |
| **Rolling metrics need 252+ observations** | Metrics return NaN for the initial window. |

---

## Integration

### wrtrade <- wrdata (data in)

```python
from wrdata import DataStream
import wrtrade as wrt

stream = DataStream()
df = stream.get("AAPL", start="2020-01-01")
prices = df["close"]    # Already a pl.Series -- no conversion needed

result = wrt.backtest(my_signal, prices)
```

### wrtrade <- fractime (regimes drive signals)

```python
import fractime as ft
import wrtrade as wrt

detector = ft.RegimeDetector(n_regimes=2)
detector.fit(returns_np)

def regime_signal(prices: pl.Series) -> pl.Series:
    returns = prices.pct_change().fill_null(0).to_numpy()
    regimes = detector.predict(returns)
    return pl.Series([1 if r == 0 else 0 for r in regimes])

result = wrt.backtest(regime_signal, prices)
```

### wrtrade -> wrchart (visualization out)

```python
import wrtrade as wrt

result = portfolio.backtest(prices)
chart = result.plot()     # Returns a wrchart.Chart
chart.show()

# Or use wrchart directly
import wrchart as wrc
equity = result.returns.cum_sum()
df = pl.DataFrame({"time": range(len(equity)), "equity": equity})
wrc.area(df).show()
```

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY.
*People for research, research for people.*
