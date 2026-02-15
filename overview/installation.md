# Installation Guide

> Per-package install instructions, optional extras, and environment setup.

## Requirements

**Python packages**: Python 3.10+ recommended. wrtrade supports 3.8+, wrchart and wayy-db support 3.9+.

**JavaScript package**: Node.js 18+ for @wayy/wrchart.

**C++ compiler**: Required only for wayy-db (CMake + pybind11, built automatically via scikit-build-core).

## Install everything at once

If you want the full Python stack:

```bash
pip install wrdata fractime wrtrade wrchart
```

This installs data collection, forecasting, backtesting, and charting. wayy-db is installed separately because it requires a C++ build toolchain.

## Per-package installation

### wrdata

Unified market data from 32+ providers.

```bash
pip install wrdata
```

Core dependencies: polars, pandas, aiohttp, httpx, ccxt, yfinance, pydantic, sqlalchemy.

No optional extras are published yet. All providers are included in the base install.

Some data providers require API keys. See the [API Keys Guide](../guides/api-keys.md) for setup.

---

### fractime

Fractal forecasting, Hurst exponent analysis, and regime detection.

```bash
pip install fractime
```

Core dependencies: numpy, numba, scikit-learn, scipy, statsmodels, matplotlib, polars, pandas, pyarrow, wrchart.

The base install includes everything: ARIMA/GARCH/Prophet baselines (pmdarima, arch, prophet), Bayesian inference (pymc, arviz, pytensor), ML models (xgboost, hmmlearn), and wavelet analysis (PyWavelets).

---

### wrtrade

Backtesting engine with Kelly optimization and broker deployment.

```bash
pip install wrtrade
```

Core dependencies: polars, numpy, scipy, pandas, wrchart, click, pyyaml, aiohttp.

**Optional extras for broker SDKs**:

```bash
# Alpaca broker integration
pip install wrtrade[alpaca]

# Robinhood broker integration
pip install wrtrade[robinhood]

# All broker integrations
pip install wrtrade[all]
```

---

### wrchart

Interactive financial charts for Python and Jupyter.

```bash
pip install wrchart
```

Core dependencies: polars, numpy.

**Optional extras**:

```bash
# Jupyter notebook support (ipywidgets, jupyterlab)
pip install wrchart[jupyter]

# Everything
pip install wrchart[all]
```

---

### @wayy/wrchart (wrchart-js)

React charting components built on TradingView Lightweight Charts.

```bash
npm install @wayy/wrchart
```

Peer dependencies: react >= 18.0.0, react-dom >= 18.0.0.

Runtime dependency: lightweight-charts ^4.1.0 (installed automatically).

```tsx
import { Chart, CandlestickSeries } from "@wayy/wrchart";

function PriceChart({ data }) {
  return (
    <Chart width={800} height={400}>
      <CandlestickSeries data={data} />
    </Chart>
  );
}
```

---

### wayy-db

Columnar time-series database with kdb+-style as-of joins. C++ core with Python bindings.

```bash
pip install wayy-db
```

Core dependencies: numpy. The C++ extension is built automatically via scikit-build-core and pybind11 during installation.

**Build requirements**: A C++17-compatible compiler (GCC 9+, Clang 10+, MSVC 2019+) and CMake 3.15+. On most Linux systems these are already available. On macOS, install Xcode Command Line Tools. On Windows, install Visual Studio Build Tools.

**Optional extras**:

```bash
# REST/WebSocket API server (FastAPI, uvicorn, Redis)
pip install wayy-db[api]

# Benchmarking suite (pandas, polars, duckdb comparison)
pip install wayy-db[bench]
```

## Environment variables

Several packages use API keys for data providers. Create a `.env` file in your project root:

```bash
# .env
ALPHA_VANTAGE_KEY=your_key_here
POLYGON_API_KEY=your_key_here
FRED_API_KEY=your_key_here
TIINGO_API_KEY=your_key_here
TWELVE_DATA_KEY=your_key_here
```

wrdata reads these automatically via python-dotenv. See the [API Keys Guide](../guides/api-keys.md) for the full list of supported providers and how to obtain keys.

## Verifying your installation

After installing, confirm everything works:

```python
# Check versions
import wrdata; print(f"wrdata: {wrdata.__version__}")
import fractime; print(f"fractime: {fractime.__version__}")
import wrtrade; print(f"wrtrade: {wrtrade.__version__}")
import wrchart; print(f"wrchart: {wrchart.__version__}")

# Quick smoke test
from wrdata import DataStream
stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")
print(f"Fetched {len(df)} rows of AAPL data")
```

## Using uv (recommended)

We recommend [uv](https://docs.astral.sh/uv/) for fast, reproducible environments:

```bash
uv venv
source .venv/bin/activate
uv pip install wrdata fractime wrtrade wrchart
```

## Troubleshooting

**wayy-db fails to build**: Make sure you have a C++ compiler and CMake installed.
```bash
# Ubuntu/Debian
sudo apt install build-essential cmake

# macOS
xcode-select --install

# Fedora
sudo dnf install gcc-c++ cmake
```

**fractime import is slow on first run**: Numba compiles JIT functions on first use. Subsequent imports are fast thanks to caching.

**ccxt or yfinance import warnings**: These are upstream warnings from data providers and can be safely ignored. They do not affect functionality.

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
