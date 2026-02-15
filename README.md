# wayyfinance-docs

Central documentation hub for the wayyFinance ecosystem — 6 open-source libraries for quantitative finance.

## The Ecosystem

| Package | Version | What It Does |
|---------|---------|-------------|
| [wrdata](packages/wrdata/) | 0.1.6 | Unified data from 32+ providers (stocks, crypto, forex, options, economic) |
| [fractime](packages/fractime/) | 0.7.0 | Fractal forecasting, Hurst analysis, regime detection |
| [wrtrade](packages/wrtrade/) | 2.1.1 | Backtesting, Kelly optimization, permutation testing, broker deployment |
| [wrchart](packages/wrchart/) | 0.2.0 | Interactive financial charts (Python, Lightweight Charts) |
| [wrchart-js](packages/wrchart-js/) | 0.2.0 | React charting components (TypeScript, TradingView) |
| [wayy-db](packages/wayydb/) | 0.1.0 | Columnar time-series database with kdb+-style joins |

## Quick Start

```bash
pip install wrdata fractime wrtrade wrchart
```

```python
from wrdata import DataStream
import fractime as ft

stream = DataStream()
df = stream.get("AAPL", start="2024-01-01")

prices = df["close"].to_numpy()
result = ft.forecast(prices, horizon=30)
ft.plot_forecast(prices[-100:], result).show()
```

## For LLMs

Point your LLM at [`llms.txt`](llms.txt) for a navigable index, or [`llms-full.txt`](llms-full.txt) for the complete reference in a single file.

See [guides/for-llms.md](guides/for-llms.md) for details.

## Documentation

- **[Overview](overview/)** — Ecosystem map, architecture, getting started
- **[Package References](packages/)** — Complete API docs for each library
- **[Cookbooks](cookbooks/)** — Runnable cross-package examples
- **[Guides](guides/)** — API keys, data providers, quant pitfalls

## Auto-Sync

Package READMEs and examples are synced weekly from source repos via [GitHub Actions](.github/workflows/sync-docs.yml). Reference docs are hand-maintained.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024
