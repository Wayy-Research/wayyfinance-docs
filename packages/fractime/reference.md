# fractime -- API Reference

> Version: 0.7.0 | Python: 3.10+ | Install: `pip install fractime`

Fractal-based time series forecasting, Hurst exponent analysis, regime detection, and advanced analytics. Uses fractal geometry and chaos theory to model financial time series.

---

## Quick Start

```python
import fractime as ft
import numpy as np

prices = np.random.lognormal(0.0005, 0.02, 500).cumprod() * 100

analyzer = ft.Analyzer(prices)
print(f"Hurst: {analyzer.hurst}")           # 0.5432
print(f"Regime: {analyzer.regime}")          # 'random'

result = ft.forecast(prices, horizon=30)
print(result.forecast)                       # 30-step price forecast
ft.plot_forecast(prices, result)             # Interactive Plotly chart
```

---

## Core API

### `Analyzer`

Fractal analysis with lazy computation. Metrics are computed on first access and cached.

```python
class Analyzer:
    def __init__(
        self,
        data: np.ndarray | pl.Series | dict,    # Price series or multi-dim dict
        dates: np.ndarray | pl.Series | None = None,
        method: str = "rs",                       # "rs" (Rescaled Range) or "dfa"
        window: int = 63,                         # Rolling window (~3 months)
        n_samples: int = 1000,                    # Bootstrap samples
        min_scale: int | None = None,
        max_scale: int | None = None,
    )
```

**Properties** (all lazy, computed on first access):

| Property | Type | Description |
|----------|------|-------------|
| `hurst` | `Metric` | Hurst exponent. H>0.5 = trending, H=0.5 = random, H<0.5 = mean-reverting |
| `fractal_dim` | `Metric` | Box-counting fractal dimension |
| `volatility` | `Metric` | Rolling volatility estimate |
| `regime` | `str` | Current regime: `"trending"`, `"random"`, or `"mean_reverting"` |
| `result` | `AnalysisResult` | Complete analysis result object |

**Methods**:

| Method | Returns | Description |
|--------|---------|-------------|
| `.analyze()` | `AnalysisResult` | Run full analysis, return result object |

```python
# Basic
analyzer = ft.Analyzer(prices)
print(analyzer.hurst)              # Metric: 0.6721

# Access different views of the same metric
analyzer.hurst.value               # 0.6721 (point estimate)
analyzer.hurst.rolling             # pl.DataFrame with rolling Hurst
analyzer.hurst.ci(0.95)            # (0.61, 0.73) bootstrap CI
analyzer.hurst.std                 # 0.04 standard error
analyzer.hurst.median              # 0.67 bootstrap median

# DFA method with custom window
analyzer = ft.Analyzer(prices, method="dfa", window=126)

# Multi-dimensional analysis
analyzer = ft.Analyzer({"price": prices, "volume": volumes})
analyzer["price"].hurst
analyzer["volume"].hurst
```

---

### `Forecaster`

Monte Carlo forecasting using fractal pattern matching.

```python
class Forecaster:
    def __init__(
        self,
        data: np.ndarray | pl.Series,
        dates: np.ndarray | pl.Series | None = None,
        exogenous: dict | None = None,           # {"VIX": vix_series}
        analyzer: Analyzer | None = None,         # Reuse pre-computed analyzer
        lookback: int = 252,                       # Pattern matching window
        method: str = "rs",                        # Hurst method
        time_warp: bool = False,                   # Mandelbrot trading time
        path_weights: dict | None = None,          # Custom path weighting
        scoring: str = "v1",                       # Scoring version
    )
```

**Methods**:

| Method | Returns | Description |
|--------|---------|-------------|
| `.predict(steps=30, n_paths=1000)` | `ForecastResult` | Generate probabilistic forecast |

**Properties**:

| Property | Type | Description |
|----------|------|-------------|
| `.hurst` | `Metric` | Shortcut to internal analyzer's Hurst |
| `.analyzer` | `Analyzer` | The analyzer used internally |

```python
model = ft.Forecaster(prices)
result = model.predict(steps=30)

# With exogenous variables
model = ft.Forecaster(prices, exogenous={"VIX": vix_data})
result = model.predict(steps=30)

# Reuse an existing analyzer
analyzer = ft.Analyzer(prices, method="dfa")
model = ft.Forecaster(prices, analyzer=analyzer)
```

---

### `Simulator`

Direct Monte Carlo path generation (lower-level than Forecaster).

```python
class Simulator:
    def __init__(self, data: np.ndarray | pl.Series)
```

Generates fBm (fractional Brownian motion), pattern-based, and bootstrap paths.

---

### `Ensemble`

Combine multiple forecast models.

```python
class Ensemble:
    def __init__(self, models: list)
```

Supports combination modes: `average`, `weighted`, `stacking`, `boosting`.

---

### `RegimeDetector`

HMM-based market regime detection using Gaussian Hidden Markov Models.

```python
class RegimeDetector:
    def __init__(
        self,
        n_regimes: int = 2,           # 2 = Bull/Bear, 3 = Bull/Bear/Sideways
        random_state: int = 42,
        n_iter: int = 100,
        tol: float = 1e-4,
        covariance_type: str = "full",
    )
```

**Methods**:

| Method | Returns | Description |
|--------|---------|-------------|
| `.fit(returns)` | `self` | Train HMM on return data |
| `.predict(returns)` | `np.ndarray` | Predict regime for each timestep |
| `.predict_proba(returns)` | `np.ndarray` | Regime probabilities at each timestep |
| `.get_current_regime(returns)` | `tuple[str, float]` | Current regime label and probability |

```python
import numpy as np

detector = ft.RegimeDetector(n_regimes=2)
detector.fit(returns)

# Classify every day
regimes = detector.predict(returns)

# Current state
regime, probability = detector.get_current_regime(returns)
print(f"Current: {regime} ({probability:.1%})")
# Current: bull (87.3%)

# Full probability matrix
probs = detector.predict_proba(returns)  # shape: (n_days, n_regimes)
```

---

### `RegimeStrategy`

Position sizing based on detected regimes. Uses fractal features for risk management, not prediction.

```python
class RegimeStrategy:
    def __init__(
        self,
        regime_detector: RegimeDetector | None = None,
        bull_allocation: float = 1.0,
        bear_allocation: float = 0.3,
        sideways_allocation: float = 0.5,   # Only used with 3 regimes
    )
```

**Methods**:

| Method | Returns | Description |
|--------|---------|-------------|
| `.backtest(prices, returns)` | `BacktestResult` | Full backtest with regime-aware sizing |

```python
strategy = ft.RegimeStrategy(
    regime_detector=ft.RegimeDetector(n_regimes=2),
    bull_allocation=1.0,
    bear_allocation=0.3,
)
results = strategy.backtest(prices, returns)
print(results.summary())
```

---

### `HurstRegimeAnalyzer`

Hurst-based regime persistence and forecast horizon estimation.

```python
class HurstRegimeAnalyzer:
    def __init__(
        self,
        prices: np.ndarray,
        method: str = "dfa",
        window: int = 252,
    )
```

**Properties**:

| Property | Type | Description |
|----------|------|-------------|
| `.current_regime` | `str` | `"trending"`, `"random"`, or `"mean_reverting"` |
| `.recommended_horizon` | `int` | Suggested forecast horizon based on regime persistence |

```python
hra = ft.HurstRegimeAnalyzer(prices, method="dfa", window=252)
print(hra.current_regime)          # "trending"
print(hra.recommended_horizon)     # 30
```

---

### `quick_backtest`

One-liner regime strategy backtest.

```python
def quick_backtest(prices: np.ndarray) -> BacktestResult
```

```python
result = ft.quick_backtest(prices)
print(f"Sharpe: {result.sharpe:.2f}")
print(f"Max DD: {result.max_drawdown:.1%}")
```

---

### Convenience Functions

```python
# Quick analysis -- same as Analyzer(prices).result
result = ft.analyze(prices)

# Quick forecast -- same as Forecaster(prices).predict(horizon)
result = ft.forecast(prices, horizon=30)

# Plot any FracTime object
ft.plot(result)

# Plot forecast with historical context
ft.plot_forecast(prices, result)
```

---

## Result Types

### `Metric`

A single metric with point, rolling, and distribution views. All views are lazy.

```python
class Metric:
    # Properties
    value: float                      # Point estimate
    rolling: pl.DataFrame             # Rolling values (columns: index/date, value)
    rolling_values: np.ndarray        # Just the rolling values as array
    distribution: np.ndarray          # Bootstrap samples
    std: float                        # Standard error from bootstrap
    median: float                     # Bootstrap median

    # Methods
    def ci(level: float = 0.95) -> tuple[float, float]
    def quantile(q: float) -> float

    # Can be used as float
    float(metric)                     # Returns .value
```

### `AnalysisResult`

```python
@dataclass
class AnalysisResult:
    hurst: Metric
    fractal_dim: Metric
    volatility: Metric
    regime: str                       # "trending", "random", "mean_reverting"
    regime_probabilities: dict[str, float]

    def summary() -> str              # Text summary
    def to_frame() -> pl.DataFrame    # All rolling metrics as DataFrame
```

### `ForecastResult`

```python
@dataclass
class ForecastResult:
    # Properties
    forecast: np.ndarray              # Primary forecast (weighted median)
    mean: np.ndarray                  # Weighted mean of paths
    path_mean: np.ndarray             # Always from MC (ignores point override)
    lower: np.ndarray                 # 5th percentile
    upper: np.ndarray                 # 95th percentile
    std: np.ndarray                   # Standard deviation at each step
    paths: np.ndarray                 # All paths, shape: (n_paths, n_steps)
    probabilities: np.ndarray         # Path weights, shape: (n_paths,)
    n_paths: int
    n_steps: int
    dates: np.ndarray | None          # Forecast dates if provided
    metadata: dict

    # Methods
    def ci(level: float = 0.95) -> tuple[np.ndarray, np.ndarray]
    def quantile(q: float) -> np.ndarray
    def to_frame() -> pl.DataFrame    # Columns: step, forecast, lower, upper, mean, std
```

### `BacktestResult` (from `RegimeStrategy`)

```python
@dataclass
class BacktestResult:
    total_return: float
    annualized_return: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    volatility: float
    win_rate: float
    avg_position: float
    regime_accuracy: float
    returns: np.ndarray
    positions: np.ndarray
    regimes: np.ndarray
    equity_curve: np.ndarray

    def to_dict() -> dict[str, float]
    def summary() -> str
```

---

## Advanced Analytics (v0.6+)

These functions provide research-grade fractal analytics.

```python
from fractime import (
    compute_wavelet_hurst,
    compute_rolling_wavelet_hurst,
    compute_mf_adcca,
    compute_qpl,
    compute_fractal_coherence,
    compute_rolling_fractal_coherence,
    compute_ftd,
    compute_dtw_alignment,
    compute_dtw_beta,
)
```

| Function | Input | Returns | Description |
|----------|-------|---------|-------------|
| `compute_wavelet_hurst(series)` | 1D array | `float` | Wavelet-based Hurst exponent |
| `compute_rolling_wavelet_hurst(series, window)` | 1D array, int | `np.ndarray` | Rolling wavelet Hurst |
| `compute_mf_adcca(series1, series2)` | Two 1D arrays | `dict` | Multifractal asymmetric detrended cross-correlation |
| `compute_qpl(series)` | 1D array | `dict` | Quantum price levels |
| `compute_fractal_coherence(series_list)` | List of arrays | `dict` | Cross-dimensional coherence |
| `compute_rolling_fractal_coherence(series_list)` | List of arrays | `np.ndarray` | Rolling coherence |
| `compute_ftd(series)` | 1D array | `dict` | Asymmetric fractal trend dimension |
| `compute_dtw_alignment(series1, series2)` | Two 1D arrays | `dict` | Dynamic time warping alignment |
| `compute_dtw_beta(series1, series2)` | Two 1D arrays | `float` | DTW-corrected beta |

```python
# Wavelet Hurst (alternative to RS/DFA)
h = ft.compute_wavelet_hurst(prices)

# Cross-asset fractal relationship
beta = ft.compute_dtw_beta(stock_prices, index_prices)
print(f"DTW-corrected beta: {beta:.3f}")

# Quantum price levels (support/resistance from fractal structure)
levels = ft.compute_qpl(prices)
```

---

### `BayesianForecaster` (optional)

Requires PyMC. Available only if `pymc` is installed.

```python
from fractime import BayesianForecaster   # Raises ImportError if PyMC missing

forecaster = BayesianForecaster(prices)
result = forecaster.predict(steps=30)
```

---

## Common Patterns

### 1. Analyze a stock and decide if it is forecastable

```python
import fractime as ft
from wrdata import DataStream

stream = DataStream()
df = stream.get("AAPL", start="2020-01-01")
prices = df["close"].to_numpy()

analyzer = ft.Analyzer(prices, method="dfa")
print(f"Hurst: {analyzer.hurst}")
print(f"Regime: {analyzer.regime}")

# H significantly different from 0.5 = potentially forecastable
lower, upper = analyzer.hurst.ci(0.95)
if lower > 0.55:
    print("Persistent trending -- fractal forecast may add value")
elif upper < 0.45:
    print("Mean-reverting -- consider contrarian signals")
else:
    print("Near random walk -- fractal forecast unlikely to help")
```

### 2. Forecast with confidence intervals

```python
model = ft.Forecaster(prices, method="dfa")
result = model.predict(steps=30, n_paths=2000)

lower, upper = result.ci(0.90)
print(f"30-day forecast: {result.forecast[-1]:.2f}")
print(f"90% CI: [{lower[-1]:.2f}, {upper[-1]:.2f}]")

ft.plot_forecast(prices, result)
```

### 3. Regime-aware position sizing

```python
strategy = ft.RegimeStrategy(
    regime_detector=ft.RegimeDetector(n_regimes=3),
    bull_allocation=1.0,
    bear_allocation=0.2,
    sideways_allocation=0.5,
)
results = strategy.backtest(prices, returns)
print(results.summary())
```

### 4. Rolling fractal analysis

```python
import polars as pl

prices = df["close"].to_numpy()
dates = df["timestamp"].to_numpy()

analyzer = ft.Analyzer(prices, dates=dates, window=63)
rolling_df = analyzer.hurst.rolling    # pl.DataFrame with date, value

# Plot rolling Hurst
import wrchart as wrc
wrc.line(rolling_df, title="Rolling Hurst Exponent").show()
```

### 5. Cross-asset fractal comparison

```python
beta = ft.compute_dtw_beta(aapl_prices, spy_prices)
coherence = ft.compute_fractal_coherence([aapl_prices, spy_prices, gld_prices])
print(f"AAPL-SPY DTW beta: {beta:.3f}")
print(f"3-asset coherence: {coherence}")
```

---

## Gotchas

| Pitfall | Details |
|---------|---------|
| **Minimum 20 data points** | Hurst estimation requires at least 20 observations. Returns H=0.5 for insufficient data. |
| **First call is slow (Numba JIT)** | Numba compiles on first invocation. Subsequent calls are fast. |
| **Input auto-conversion** | Accepts numpy arrays, Polars Series, pandas Series, and Python lists. All converted to numpy internally. |
| **v0.7.0 API differs from v0.2.0** | Class names changed: `FractalAnalyzer` -> `Analyzer`, `FractalForecaster` -> `Forecaster`. |
| **Hurst is not a trading signal** | H measures memory structure, not direction. Use for risk management and position sizing. |
| **Bootstrap CI requires computation** | Accessing `.ci()` or `.std` triggers bootstrap sampling (can take seconds with large data). |
| **Rolling requires dates** | Calling `.rolling` without passing `dates` to the `Analyzer` raises `ValueError`. |
| **PyMC is optional** | `BayesianForecaster` is only available if PyMC is installed. Importing it without PyMC returns `None`. |

---

## Integration

### fractime <- wrdata (data in)

```python
from wrdata import DataStream
import fractime as ft

stream = DataStream()
df = stream.get("^GSPC", start="2015-01-01")
prices = df["close"].to_numpy()    # fractime expects numpy

result = ft.forecast(prices, horizon=30)
```

### fractime -> wrchart (visualization out)

```python
# Built-in plotting (uses wrchart/plotly internally)
ft.plot_forecast(prices, result)

# Or manual with wrchart
import wrchart as wrc
wrc.forecast(
    paths=result.paths,
    historical=prices,
    probabilities=result.probabilities,
).show()
```

### fractime -> wrtrade (regimes drive signals)

```python
import fractime as ft
import wrtrade as wrt
import polars as pl

detector = ft.RegimeDetector(n_regimes=2)
detector.fit(returns_np)

def regime_signal(prices: pl.Series) -> pl.Series:
    returns = prices.pct_change().fill_null(0).to_numpy()
    regimes = detector.predict(returns)
    # 1 in bull regime, 0.3 in bear
    positions = [1.0 if r == 0 else 0.3 for r in regimes]
    return pl.Series(positions)

result = wrt.backtest(regime_signal, prices_polars)
print(f"Sortino: {result.sortino:.2f}")
```

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY.
*People for research, research for people.*
