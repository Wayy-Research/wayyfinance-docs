"""
Cookbook 05: Whale Detection
=============================
Monitor Binance for large trades (top 1% by volume)
using wrdata's whale detection system.

Requirements: pip install wrdata
Note: This script runs indefinitely. Press Ctrl+C to stop.
"""

import asyncio
from wrdata.streaming.binance_stream import BinanceStreamProvider


async def detect_whales():
    provider = BinanceStreamProvider()
    await provider.connect()

    whale_count = 0

    def on_whale(whale_tx):
        nonlocal whale_count
        whale_count += 1
        side = whale_tx.side.upper()
        print(f"\n{'='*60}")
        print(f"WHALE ALERT #{whale_count}")
        print(f"  Symbol: {whale_tx.symbol}")
        print(f"  Side: {side}")
        print(f"  Size: {whale_tx.size} BTC")
        print(f"  Price: ${whale_tx.price:,.2f}")
        print(f"  USD Value: ${whale_tx.usd_value:,.0f}")
        print(f"  Percentile: {whale_tx.percentile:.1f}%")
        print(f"  Maker: {whale_tx.is_maker}")
        print(f"  Time: {whale_tx.timestamp}")
        print(f"{'='*60}")

    print("Monitoring BTCUSDT for whale trades (top 1%)...")
    print("Waiting for volume baseline to build...\n")

    async for msg in provider.subscribe_aggregate_trades(
        symbol="BTCUSDT",
        enable_whale_detection=True,
        percentile_threshold=99.0,
        whale_callback=on_whale,
    ):
        # Print normal trade activity
        print(
            f"  Trade: {msg.symbol} ${msg.price:,.2f} x {msg.volume:.4f}",
            end="\r",
        )

        # Stop after 10 whales for demo
        if whale_count >= 10:
            print(f"\n\nDetected {whale_count} whale trades. Stopping.")
            break

    await provider.disconnect()


if __name__ == "__main__":
    asyncio.run(detect_whales())
