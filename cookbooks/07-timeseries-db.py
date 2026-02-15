"""
Cookbook 07: TimeSeries DB
==========================
Ingest market data from wrdata into wayyDB, then perform
kdb+-style as-of joins between trades and quotes.

Requirements: pip install wrdata wayy-db
"""

import wayy_db
from wayy_db import ops
import numpy as np
from datetime import datetime, timezone

# --- Step 1: Create sample trade data ---
# In production, you'd stream this from wrdata
np.random.seed(42)
n_trades = 1000
trade_times = np.sort(np.random.randint(0, 86400, n_trades).astype(np.int64))
trade_prices = 100.0 + np.cumsum(np.random.randn(n_trades) * 0.01)
trade_sizes = np.random.randint(1, 100, n_trades).astype(np.int64)

trades = wayy_db.from_dict(
    {
        "time": trade_times,
        "price": trade_prices,
        "size": trade_sizes,
    },
    name="trades",
    sorted_by="time",
)
print(f"Created trades table: {trades.num_rows} rows, {trades.num_columns} cols")

# --- Step 2: Create sample quote data ---
n_quotes = 500
quote_times = np.sort(np.random.randint(0, 86400, n_quotes).astype(np.int64))
mid_prices = 100.0 + np.cumsum(np.random.randn(n_quotes) * 0.005)
spreads = np.random.uniform(0.01, 0.05, n_quotes)

quotes = wayy_db.from_dict(
    {
        "time": quote_times,
        "bid": mid_prices - spreads / 2,
        "ask": mid_prices + spreads / 2,
    },
    name="quotes",
    sorted_by="time",
)
print(f"Created quotes table: {quotes.num_rows} rows, {quotes.num_columns} cols")

# --- Step 3: As-of join — latest quote at each trade time ---
joined = ops.aj(trades, quotes, on="time", as_of="time")
print(f"\nAs-of join result: {joined.num_rows} rows")

# Show first few results
result = joined.to_dict()
print(f"\nFirst 5 trades with latest quotes:")
print(f"{'Time':>8} {'Price':>10} {'Size':>6} {'Bid':>10} {'Ask':>10} {'Spread':>8}")
for i in range(5):
    spread = result["ask"][i] - result["bid"][i]
    print(
        f"{result['time'][i]:>8} "
        f"{result['price'][i]:>10.2f} "
        f"{result['size'][i]:>6} "
        f"{result['bid'][i]:>10.4f} "
        f"{result['ask'][i]:>10.4f} "
        f"{spread:>8.4f}"
    )

# --- Step 4: Compute analytics ---
# VWAP
vwap_price = ops.sum(trades["price"] * trades["size"]) / ops.sum(trades["size"])
print(f"\nVWAP: ${vwap_price:.4f}")

# Moving average of trade prices
ma = ops.mavg(trades["price"], window=50)
print(f"50-trade MA (latest): ${ma[-1]:.4f}")

# Percent changes
pct = ops.pct_change(trades["price"])
print(f"Average tick return: {np.nanmean(pct):.6f}")

# --- Step 5: Window join — all quotes within +-10s of each trade ---
windowed = ops.wj(trades, quotes, on="time", as_of="time", before=10, after=10)
print(f"\nWindow join (+-10s): {windowed.num_rows} rows")

# --- Step 6: Persist to disk ---
db = wayy_db.Database("/tmp/cookbook_07_db")
db.add_table(trades)
db.add_table(quotes)
print(f"\nSaved to /tmp/cookbook_07_db")

# Memory-map for fast reload
trades_mmap = trades.mmap("/tmp/cookbook_07_trades.bin")
print(f"Memory-mapped trades: {trades_mmap.num_rows} rows (zero-copy)")
