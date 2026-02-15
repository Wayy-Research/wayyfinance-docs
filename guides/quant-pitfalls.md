# Quant Pitfalls & Best Practices

> Common mistakes that silently corrupt your results. Every one of these has cost someone real money.

## 1. Lookahead Bias

**The problem**: Using future data to make past decisions. Your backtest looks amazing, but only because it cheated.

**How it happens**: Computing a signal using the current bar's close, then trading on that same bar.

Wrong:

```python
# BUG: signal uses today's close, but you're trading at today's close
# In live trading, you wouldn't know today's close until the bar finishes
df = df.with_columns(
    signal=pl.when(pl.col("close") > pl.col("close").rolling_mean(20))
    .then(1)
    .otherwise(0)
)
```

Right:

```python
# Signal uses yesterday's data, trade executes on today's open
df = df.with_columns(
    signal=pl.when(
        pl.col("close").shift(1) > pl.col("close").shift(1).rolling_mean(20)
    )
    .then(1)
    .otherwise(0)
)
```

**Rules**:
- Always `shift(1)` before computing signals from the data you trade on
- Use walk-forward validation, never train and test on the same data
- wrtrade's `Backtest` engine handles execution timing correctly when you define signals in `on_bar` -- the signal fires after the bar closes and the order fills on the next bar

## 2. Float Precision

**The problem**: Floating-point arithmetic accumulates tiny errors. Over thousands of trades, these errors become material.

```python
# This is not 0.3
>>> 0.1 + 0.1 + 0.1
0.30000000000000004

# After 10,000 trades with $0.01 rounding errors, you're off by ~$100
```

**Rules**:
- Use `Decimal` for prices and position sizes when real money is involved
- Floats are fine for returns, ratios, Sharpe, Hurst exponents, and other analytical values
- Never compare floats with `==`

```python
from decimal import Decimal

# Broker orders: always Decimal
order_price = Decimal("152.35")
shares = Decimal("100")
cost = order_price * shares  # Exact: Decimal("15235.00")

# Analytics: float is fine
daily_return = 0.0127
sharpe_ratio = 1.85
hurst = 0.63
```

## 3. Timezone Bugs

**The problem**: Mixing timezone-naive and timezone-aware datetimes. Or comparing timestamps across timezones without conversion. NYSE closes at 16:00 ET, which is 20:00 or 21:00 UTC depending on daylight savings.

**Rules**:
- Store everything as UTC internally
- Convert to local time only at display boundaries
- Never create naive datetimes for market data

Wrong:

```python
from datetime import datetime

# BUG: naive datetime, no timezone info
market_close = datetime(2024, 6, 15, 16, 0, 0)
```

Right:

```python
from datetime import datetime, timezone, timedelta

# Always attach a timezone
market_close_et = datetime(2024, 6, 15, 16, 0, 0,
                           tzinfo=timezone(timedelta(hours=-4)))  # EDT

# Convert to UTC for storage
market_close_utc = market_close_et.astimezone(timezone.utc)
# 2024-06-15 20:00:00+00:00

# Convert back for display
print(market_close_utc.astimezone(timezone(timedelta(hours=-4))))
```

All wayyFinance packages use UTC internally. wrdata returns UTC timestamps. Do not convert them to local time until you are rendering for a user.

## 4. OHLCV Invariants

**The problem**: Data providers sometimes deliver bars where the high is below the close, the low is above the open, or volume is negative. If you do not validate, your indicators and backtests silently produce garbage.

**Required invariants**:

```
high >= max(open, close)
low  <= min(open, close)
high >= low
volume >= 0
```

**Validation**:

```python
def validate_ohlcv(df: pl.DataFrame) -> pl.DataFrame:
    """Check OHLCV invariants. Raises on violation."""
    violations = df.filter(
        (pl.col("high") < pl.col("open")) |
        (pl.col("high") < pl.col("close")) |
        (pl.col("low") > pl.col("open")) |
        (pl.col("low") > pl.col("close")) |
        (pl.col("high") < pl.col("low")) |
        (pl.col("volume") < 0)
    )
    if len(violations) > 0:
        raise ValueError(
            f"OHLCV invariant violations in {len(violations)} bars:\n"
            f"{violations.head(5)}"
        )
    return df
```

**Common causes of bad data**:
- Pre/post-market sessions included in regular hours bars
- Stock splits applied to open/close but not high/low
- Currency conversion applied inconsistently
- Data provider bugs (more common than you think)

## 5. Survivorship Bias

**The problem**: Testing your strategy only on stocks that exist today. Companies that went bankrupt, were delisted, or were acquired are missing from current symbol lists. Your strategy looks better than it is because it never had to deal with the losers.

**Example**: Testing a "buy the dip" strategy on the current S&P 500. Companies that dipped and never recovered were removed from the index. You only see the survivors.

**Mitigation**:
- Use point-in-time index constituents when available
- Include delisted symbols in your universe (some data providers offer this)
- Be skeptical of strategies that only work on large-cap indices
- At minimum, acknowledge this limitation in your research

## 6. Overfitting

**The problem**: Your strategy has 15 parameters, each tuned to perfection on historical data. It captures the noise, not the signal. Out-of-sample, it falls apart.

**Warning signs**:
- Sharpe ratio > 3 on daily data (verify your math twice)
- Strategy performance degrades sharply with small parameter changes
- Many parameters relative to the number of trades
- No economic rationale for why the strategy should work

**Mitigation with wrtrade**:

```python
from wrtrade import Backtest, permutation_test

# Run the backtest
bt = Backtest(data=df, strategy=MyStrategy)
result = bt.run()

# Permutation test: is this result statistically significant?
p_value = permutation_test(bt, n_permutations=1000, metric="sharpe")
print(f"p-value: {p_value:.4f}")

# p < 0.05 means the result is unlikely due to chance
# p > 0.05 means you probably overfit
```

**Rules of thumb**:
- Fewer parameters is better. Can you explain each one?
- Walk-forward validation: train on 2020-2022, test on 2023, never look back
- Permutation testing: if randomized data produces similar results, your edge is not real
- The strategy should have an economic reason to work, not just a statistical one

## 7. Data Quality

**The problem**: Missing bars, duplicate timestamps, gaps over weekends treated as trading days, and adjusted vs. unadjusted prices mixed together.

**Common issues**:

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing bars | Gaps in time series | Use wrdata's `min_coverage` parameter |
| Duplicate timestamps | Inflated returns | Deduplicate by timestamp |
| Weekend/holiday gaps | False signals on gap days | Filter to trading days |
| Split-adjusted vs raw | 2:1 split looks like a 50% crash | Use adjusted data consistently |
| Dividend adjustments | Missing yield from total return | Use total return series or account separately |

**wrdata handles most of this**:

```python
stream = DataStream()

# min_coverage rejects symbols with too many missing bars
df = stream.get("AAPL", start="2020-01-01", min_coverage=0.95)

# Check for gaps
timestamps = df["timestamp"].to_list()
gaps = [
    (timestamps[i], timestamps[i+1])
    for i in range(len(timestamps) - 1)
    if (timestamps[i+1] - timestamps[i]).days > 3  # more than a weekend
]
if gaps:
    print(f"Warning: {len(gaps)} gaps found in data")
```

**Corporate actions checklist**:
- Are prices adjusted for splits? (They should be, unless you are modeling order books)
- Are dividends accounted for? (Total return vs. price return)
- Did a ticker change? (META was FB, GOOGL was GOOG)
- Did a merger happen? (Your signal on the acquired company is meaningless after the merge date)

## 8. Transaction Costs

**The problem**: Your strategy trades 500 times per year and earns 0.05% per trade before costs. After a realistic 0.1% round-trip cost (slippage + commissions), it loses money.

**The math**:

```
Gross return per trade:    +0.05%
Round-trip cost:           -0.10%
Net return per trade:      -0.05%

500 trades/year * -0.05% = -25% annual return
```

A strategy that looked like it earned 25% annually actually loses 25%.

**Realistic cost assumptions**:

| Market | Round-trip Cost | Notes |
|--------|----------------|-------|
| US large-cap stocks | 0.02-0.05% | Tight spreads, low commissions |
| US small-cap stocks | 0.10-0.30% | Wider spreads, impact cost |
| Crypto (major pairs) | 0.10-0.20% | Exchange fees + spread |
| Crypto (altcoins) | 0.30-1.00% | Thin books, high slippage |
| Forex (major pairs) | 0.01-0.03% | Tightest spreads in any market |
| Options | 0.50-2.00% | Wide bid-ask, assignment risk |

**In wrtrade**:

```python
bt = Backtest(
    data=df,
    strategy=MyStrategy,
    commission=0.001,    # 0.1% per trade
    slippage=0.0005,     # 0.05% slippage
)
result = bt.run()

# Compare: gross vs net Sharpe
print(f"Net Sharpe: {result.sharpe:.2f}")
```

**Rules**:
- Always include transaction costs in backtests. A costless backtest is fantasy.
- Higher frequency = more sensitivity to costs. Daily strategies are more forgiving than intraday.
- Reduce turnover where possible. Can you hold for 5 days instead of 1?
- Test with 2x your expected costs to build in a safety margin.

## Summary

| Pitfall | One-Line Check |
|---------|----------------|
| Lookahead bias | "Am I using data I wouldn't have at decision time?" |
| Float precision | "Am I using Decimal for money?" |
| Timezone bugs | "Is everything in UTC until display?" |
| OHLCV invariants | "Did I validate high >= low, high >= close?" |
| Survivorship bias | "Does my universe include dead companies?" |
| Overfitting | "Does the permutation test pass at p < 0.05?" |
| Data quality | "Did I check for gaps, duplicates, and splits?" |
| Transaction costs | "Does this still work at 2x my expected costs?" |

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY, Est. 2024.
*People for research, research for people.*
