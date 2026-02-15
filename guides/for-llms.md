# Using wayyFinance Docs with LLMs

> This documentation repository is designed for LLM consumption. Paste files into your LLM context to get accurate code generation for the wayyFinance ecosystem.

## Three Ways to Use It

### 1. llms.txt -- Navigable Index

The [`llms.txt`](../llms.txt) file is a structured index of all documentation in this repository. Paste it into your LLM's context window for guided exploration. The LLM can see what documentation exists and ask you for specific files as needed.

Best for: exploratory conversations, when you are not sure which package you need.

**Approximate token budget**: ~500 tokens.

### 2. llms-full.txt -- Complete Reference

The [`llms-full.txt`](../llms-full.txt) file concatenates all package references into a single file. Paste it all at once for maximum capability. The LLM will have complete API knowledge across all six packages.

Best for: writing complex code that spans multiple packages, building full workflows.

**Approximate token budget**: ~15,000 tokens.

### 3. Individual Reference Files -- Focused Work

Paste a specific package's `reference.md` file when you only need one library:

| File | Tokens (approx) | Use When |
|------|-----------------|----------|
| [`packages/wrdata/reference.md`](../packages/wrdata/reference.md) | ~3,000 | Fetching market data |
| [`packages/fractime/reference.md`](../packages/fractime/reference.md) | ~2,500 | Forecasting and Hurst analysis |
| [`packages/wrtrade/reference.md`](../packages/wrtrade/reference.md) | ~3,000 | Backtesting and trading |
| [`packages/wrchart/reference.md`](../packages/wrchart/reference.md) | ~2,000 | Python charting |
| [`packages/wrchart-js/reference.md`](../packages/wrchart-js/reference.md) | ~2,000 | React charting |
| [`packages/wayydb/reference.md`](../packages/wayydb/reference.md) | ~2,000 | Time-series database |

Best for: focused tasks involving a single package.

## Recommended Workflow

1. Paste `llms-full.txt` into your LLM context
2. Ask it to write code using wayyFinance
3. Copy-paste the output and run it

The documentation includes function signatures, parameter types, return types, and working examples. The LLM should produce code that runs on the first try.

## Example Prompts

Once you have pasted the documentation into context, try these:

### Data + Forecasting

```
Fetch AAPL daily data from 2024 and generate a 30-day fractal forecast.
Plot the results with confidence intervals.
```

### Backtesting

```
Backtest a moving average crossover strategy on BTC-USD.
Use a 20-day and 50-day SMA. Show the equity curve and
run a permutation test to check if results are statistically significant.
```

### Screening

```
Build a multi-asset Hurst exponent screener. Check AAPL, MSFT, GOOGL,
BTC-USD, and ETH-USD. Flag any with H > 0.6 as trending.
```

### Streaming

```
Set up a real-time WebSocket stream for BTC-USD from Binance.
Print each tick with timestamp and price.
```

### Full Pipeline

```
Build a complete research pipeline:
1. Fetch SPY data for the last 2 years
2. Detect regime changes with fractime
3. Backtest a regime-aware strategy (long in trending, flat in mean-reverting)
4. Plot the equity curve with regime annotations
5. Run permutation testing with 1000 iterations
```

### Options Analysis

```
Fetch the options chain for AAPL using wrdata.
Calculate implied volatility across strikes and expirations.
```

## Tips for Better Results

- **Be specific about packages**: Say "use wrdata to fetch" rather than just "fetch data"
- **Mention the asset type**: The LLM will select the right provider (Yahoo for stocks, Coinbase for crypto, FRED for economic data)
- **Ask for complete scripts**: The docs include enough detail for end-to-end code generation
- **Request error handling**: The docs list common exceptions for each function

## What the LLM Will Know

With `llms-full.txt` in context, the LLM has access to:

- Every public function and class across all six packages
- Parameter names, types, and defaults
- Return types and their attributes
- Working code examples for each function
- Provider-specific details (rate limits, auth requirements, supported assets)
- Cross-package integration patterns (wrdata to fractime to wrchart)

## What the LLM Will Not Know

- Private/internal APIs (functions prefixed with `_`)
- Unreleased features not yet in the documentation
- Your specific environment setup (API keys, Python version, OS)
- Real-time market conditions or current prices

Provide this context yourself when relevant.

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
