"""
Cookbook 04: Realtime Streaming
===============================
Stream live BTC prices from Binance via WebSocket,
build 1-minute candles in real time.

Requirements: pip install wrdata
Note: This script runs indefinitely. Press Ctrl+C to stop.
"""

import asyncio
from datetime import datetime, timezone
from wrdata import DataStream


async def stream_with_candles():
    stream = DataStream()

    # State for building 1-minute candles
    current_candle = {
        "open": None,
        "high": float("-inf"),
        "low": float("inf"),
        "close": None,
        "volume": 0.0,
        "minute": None,
    }
    candle_count = 0

    async for tick in stream.stream("BTCUSDT", stream_type="ticker"):
        now = datetime.now(timezone.utc)
        minute = now.replace(second=0, microsecond=0)

        # New minute — emit completed candle
        if current_candle["minute"] is not None and minute != current_candle["minute"]:
            candle_count += 1
            print(
                f"[{current_candle['minute'].strftime('%H:%M')}] "
                f"O:{current_candle['open']:.2f} "
                f"H:{current_candle['high']:.2f} "
                f"L:{current_candle['low']:.2f} "
                f"C:{current_candle['close']:.2f} "
                f"V:{current_candle['volume']:.4f}"
            )

            # Reset candle
            current_candle = {
                "open": tick.price,
                "high": tick.price,
                "low": tick.price,
                "close": tick.price,
                "volume": tick.volume,
                "minute": minute,
            }
        else:
            # Update current candle
            if current_candle["open"] is None:
                current_candle["open"] = tick.price
                current_candle["minute"] = minute

            current_candle["high"] = max(current_candle["high"], tick.price)
            current_candle["low"] = min(current_candle["low"], tick.price)
            current_candle["close"] = tick.price
            current_candle["volume"] += tick.volume

        # Print live tick
        print(
            f"  BTCUSDT: ${tick.price:,.2f} | "
            f"Bid: ${tick.bid:,.2f} | "
            f"Ask: ${tick.ask:,.2f}",
            end="\r",
        )

        # Stop after 5 candles for demo
        if candle_count >= 5:
            print(f"\n\nCompleted {candle_count} candles. Stopping.")
            break

    await stream.disconnect_streams()


if __name__ == "__main__":
    asyncio.run(stream_with_candles())
