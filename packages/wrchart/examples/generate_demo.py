#!/usr/bin/env python3
"""
Generate comprehensive wrchart demo HTML.

Demonstrates all chart types, transforms, and indicators.
"""

import sys
sys.path.insert(0, '..')

import numpy as np
import polars as pl
import wrchart as wrc
from wrchart.indicators import sma, ema, wma, bollinger_bands, rsi, macd, stochastic


def create_ohlcv_data(n: int = 252, seed: int = 42) -> pl.DataFrame:
    """Generate realistic OHLCV data."""
    np.random.seed(seed)

    # Random walk with drift
    returns = np.random.randn(n) * 0.02 + 0.0003
    prices = 100 * np.exp(np.cumsum(returns))

    opens = np.roll(prices, 1)
    opens[0] = prices[0]
    highs = np.maximum(prices, opens) * (1 + np.abs(np.random.randn(n)) * 0.01)
    lows = np.minimum(prices, opens) * (1 - np.abs(np.random.randn(n)) * 0.01)
    volumes = np.random.randint(100000, 1000000, n) * (1 + np.abs(returns) * 50)

    return pl.DataFrame({
        'time': list(range(n)),
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes.astype(int),
    })


def create_tick_data(n: int = 50_000, seed: int = 42) -> pl.DataFrame:
    """Generate high-frequency tick data."""
    np.random.seed(seed)
    return pl.DataFrame({
        'time': list(range(n)),
        'value': 100 + np.cumsum(np.random.randn(n) * 0.01),
    })


def create_million_point_data(n: int = 1_000_000, seed: int = 12345) -> pl.DataFrame:
    """Generate 1 million tick data points for WebGL demo."""
    np.random.seed(seed)
    # Random walk with mean reversion
    values = np.zeros(n)
    values[0] = 100
    for i in range(1, n):
        values[i] = values[i-1] + np.random.randn() * 0.002
        # Keep in reasonable bounds
        values[i] = np.clip(values[i], 90, 110)
    return pl.DataFrame({
        'time': list(range(n)),
        'value': values,
    })


def generate_html_page(charts_html: str, title: str = "wrchart Demo") -> str:
    """Wrap charts in a full HTML page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        /* Hide TradingView attribution logo */
        .tv-attribution-logo,
        [class*="attribution"],
        a[href*="tradingview"] {{
            display: none !important;
            visibility: hidden !important;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #000000;
            color: #FFFFFF;
            padding: 24px;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 24px;
            border-bottom: 1px solid #333;
        }}
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 8px;
        }}
        .header .accent {{
            color: #E53935;
        }}
        .header p {{
            color: #888;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 48px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #333;
            letter-spacing: -0.02em;
        }}
        .section-title .accent {{
            color: #E53935;
        }}
        .description {{
            color: #888;
            font-size: 13px;
            margin-bottom: 16px;
            line-height: 1.5;
        }}
        .chart-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 24px;
            margin-bottom: 24px;
        }}
        .chart-container {{
            background: #111;
            padding: 16px;
            flex: 1;
            min-width: 400px;
        }}
        .chart-title {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #FFF;
        }}
        .chart-subtitle {{
            font-size: 11px;
            color: #666;
            margin-top: 8px;
            font-family: 'JetBrains Mono', monospace;
        }}
        .stats {{
            display: flex;
            gap: 16px;
            margin-top: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
        }}
        .stat {{
            color: #888;
        }}
        .stat-value {{
            color: #E53935;
        }}
        .footer {{
            text-align: center;
            padding-top: 24px;
            border-top: 1px solid #333;
            color: #666;
            font-size: 12px;
        }}
        .footer a {{
            color: #E53935;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>wrchart <span class="accent">Demo</span></h1>
        <p>Interactive financial charting with Polars and TradingView-style aesthetics</p>
    </div>

    {charts_html}

    <div class="footer">
        <p>Built with <a href="https://github.com/wayy-research/wrchart">wrchart</a> by <a href="https://wayyresearch.com">Wayy Research</a></p>
    </div>
</body>
</html>"""


def extract_chart_js(chart: wrc.Chart) -> tuple:
    """Extract chart configuration for embedding."""
    import json
    config = json.loads(chart.to_json())
    return config, chart._id


def main():
    print("Generating comprehensive wrchart demo...")

    # Generate sample data
    df = create_ohlcv_data(252)
    tick_df = create_tick_data(50_000)

    sections_html = []

    # ===== SECTION 1: Standard Chart Types =====
    section1_charts = []

    # 1a. Standard Candlestick with Volume
    chart1 = wrc.Chart(width=850, height=450, title='Standard Candlestick with Volume')
    chart1.add_candlestick(df)
    chart1.add_volume(df)

    # 1b. Heikin-Ashi
    ha_df = wrc.to_heikin_ashi(df)
    chart2 = wrc.Chart(width=850, height=350, title='Heikin-Ashi (Smoothed Candles)')
    chart2.add_candlestick(ha_df)

    section1_charts.append(('candlestick', chart1, f'{len(df)} bars'))
    section1_charts.append(('heikin-ashi', chart2, f'{len(ha_df)} bars'))

    # ===== SECTION 2: Alternative Chart Types =====
    section2_charts = []

    # Calculate dynamic brick/range sizes based on price volatility
    price_high = df['high'].max()
    price_low = df['low'].min()
    price_range = price_high - price_low
    avg_price = df['close'].mean()

    # Use ~1.5% of price range for brick size (produces 50-150 bricks typically)
    brick_size = max(0.5, price_range * 0.015)
    # Use ~2% of price range for range bars
    range_size = max(0.5, price_range * 0.02)
    # Use ~1% of avg price for kagi reversal
    kagi_reversal = max(0.5, avg_price * 0.01)

    print(f"Price range: {price_range:.2f}, brick_size: {brick_size:.2f}, range_size: {range_size:.2f}")

    # 2a. Renko
    renko_df = wrc.to_renko(df, brick_size=brick_size)
    chart_renko = wrc.Chart(width=420, height=300, title=f'Renko (brick=${brick_size:.2f})')
    chart_renko.add_candlestick(renko_df)

    # 2b. Kagi
    kagi_df = wrc.to_kagi(df, reversal_amount=kagi_reversal)
    chart_kagi = wrc.Chart(width=420, height=300, title=f'Kagi (reversal=${kagi_reversal:.2f})')
    chart_kagi.add_candlestick(kagi_df)

    # 2c. Three Line Break
    lb_df = wrc.to_line_break(df, num_lines=3)
    chart_lb = wrc.Chart(width=420, height=300, title='Three Line Break')
    chart_lb.add_candlestick(lb_df)

    # 2d. Range Bars
    rb_df = wrc.to_range_bars(df, range_size=range_size)
    chart_rb = wrc.Chart(width=420, height=300, title=f'Range Bars (${range_size:.2f} range)')
    chart_rb.add_candlestick(rb_df)

    # 2e. Point & Figure
    pnf_df = wrc.to_point_and_figure(df, box_size=1.0, reversal_boxes=3)
    chart_pnf = wrc.Chart(width=420, height=300, title='Point & Figure ($1 box, 3-box reversal)')
    # P&F needs special handling - convert to candlestick-like format
    pnf_candle = pnf_df.select([
        pl.col('time'),
        pl.col('low').alias('open'),
        pl.col('high'),
        pl.col('low'),
        pl.col('high').alias('close'),
    ])
    chart_pnf.add_candlestick(pnf_candle)

    section2_charts.append(('renko', chart_renko, f'{len(renko_df)} bricks'))
    section2_charts.append(('kagi', chart_kagi, f'{len(kagi_df)} lines'))
    section2_charts.append(('line-break', chart_lb, f'{len(lb_df)} lines'))
    section2_charts.append(('range-bars', chart_rb, f'{len(rb_df)} bars'))
    section2_charts.append(('pnf', chart_pnf, f'{len(pnf_df)} columns'))

    # ===== SECTION 3: High-Frequency Data with LTTB =====
    display_df = wrc.lttb_downsample(tick_df, target_points=2000)
    chart_hf = wrc.Chart(width=850, height=350, title=f'High-Frequency Tick Data ({len(tick_df):,} points → 2k with LTTB)')
    chart_hf.add_line(display_df)

    # ===== SECTION 3b: GPU-Accelerated Million Point Rendering =====
    print("Generating 1 million data points for WebGL...")
    million_df = create_million_point_data(1_000_000)
    webgl_chart = wrc.WebGLChart(
        width=850,
        height=400,
        title='GPU-Accelerated Tick Data'
    )
    webgl_chart.add_line(million_df, time_col='time', value_col='value')
    print(f"WebGL chart ready with {len(million_df):,} points")

    # ===== SECTION 4: Overlay Indicators =====
    section4_charts = []

    # 4a. Moving Averages
    sma_20 = sma(df, period=20, value_col='close', output_col='value')
    ema_20 = ema(df, period=20, value_col='close', output_col='value')
    wma_20 = wma(df, period=20, value_col='close', output_col='value')

    chart_ma = wrc.Chart(width=850, height=400, title='Moving Averages (SMA, EMA, WMA - 20 period)')
    chart_ma.add_candlestick(df)
    chart_ma.add_line(sma_20, color='#E53935', title='SMA 20')
    chart_ma.add_line(ema_20, color='#2196F3', title='EMA 20')
    chart_ma.add_line(wma_20, color='#4CAF50', title='WMA 20')

    # 4b. Bollinger Bands
    bb = bollinger_bands(df, period=20, std_dev=2.0, value_col='close')
    bb_upper = bb.select([pl.col('time'), pl.col('upper').alias('value')])
    bb_middle = bb.select([pl.col('time'), pl.col('middle').alias('value')])
    bb_lower = bb.select([pl.col('time'), pl.col('lower').alias('value')])

    chart_bb = wrc.Chart(width=850, height=400, title='Bollinger Bands (20, 2σ)')
    chart_bb.add_candlestick(df)
    chart_bb.add_line(bb_upper, color='#888888', title='Upper Band')
    chart_bb.add_line(bb_middle, color='#E53935', title='Middle (SMA)')
    chart_bb.add_line(bb_lower, color='#888888', title='Lower Band')

    section4_charts.append(('ma', chart_ma, ''))
    section4_charts.append(('bb', chart_bb, ''))

    # ===== SECTION 5: Oscillator Indicators =====
    section5_charts = []

    # 5a. RSI
    rsi_df = rsi(df, period=14, value_col='close', output_col='value')
    chart_rsi = wrc.Chart(width=420, height=200, title='RSI (14)')
    chart_rsi.add_line(rsi_df, color='#E53935')

    # 5b. Stochastic
    stoch_df = stochastic(df, k_period=14, d_period=3)
    stoch_k = stoch_df.select([pl.col('time'), pl.col('k').alias('value')])
    stoch_d = stoch_df.select([pl.col('time'), pl.col('d').alias('value')])
    chart_stoch = wrc.Chart(width=420, height=200, title='Stochastic (14, 3)')
    chart_stoch.add_line(stoch_k, color='#E53935', title='%K')
    chart_stoch.add_line(stoch_d, color='#888888', title='%D')

    # 5c. MACD
    macd_df = macd(df, fast_period=12, slow_period=26, signal_period=9, value_col='close')
    macd_line = macd_df.select([pl.col('time'), pl.col('macd').alias('value')])
    signal_line = macd_df.select([pl.col('time'), pl.col('signal').alias('value')])
    hist_data = macd_df.select([pl.col('time'), pl.col('histogram').alias('value')])

    chart_macd = wrc.Chart(width=850, height=250, title='MACD (12, 26, 9)')
    chart_macd.add_line(macd_line, color='#E53935', title='MACD')
    chart_macd.add_line(signal_line, color='#888888', title='Signal')
    chart_macd.add_histogram(hist_data, color='#4CAF50')

    section5_charts.append(('rsi', chart_rsi, ''))
    section5_charts.append(('stoch', chart_stoch, ''))
    section5_charts.append(('macd', chart_macd, ''))

    # ===== Generate HTML =====
    import json

    all_configs = []

    def add_chart_config(chart, label, stats_text):
        config = json.loads(chart.to_json())
        all_configs.append({
            'label': label,
            'config': config,
            'stats': stats_text,
            'id': chart._id
        })

    # Add all charts
    for label, chart, stats in section1_charts:
        add_chart_config(chart, label, stats)
    for label, chart, stats in section2_charts:
        add_chart_config(chart, label, stats)
    add_chart_config(chart_hf, 'hf', f'{len(tick_df):,} → {len(display_df):,} points')
    for label, chart, stats in section4_charts:
        add_chart_config(chart, label, stats)
    for label, chart, stats in section5_charts:
        add_chart_config(chart, label, stats)

    # Build sections HTML
    html_parts = []

    # Section 1: Standard Charts
    html_parts.append("""
    <div class="section">
        <h2 class="section-title">Standard <span class="accent">Chart Types</span></h2>
        <p class="description">Traditional OHLCV candlestick charts with volume, and Heikin-Ashi smoothed candles for trend identification.</p>
        <div class="chart-row">
    """)

    for label, chart, stats in section1_charts:
        cid = chart._id
        html_parts.append(f"""
            <div class="chart-container">
                <div class="chart-title">{chart.title}</div>
                <div id="wrchart-{cid}"></div>
                <div class="chart-subtitle">{stats}</div>
            </div>
        """)

    html_parts.append("</div></div>")

    # Section 2: Alternative Charts
    html_parts.append("""
    <div class="section">
        <h2 class="section-title">Alternative <span class="accent">Chart Types</span></h2>
        <p class="description">Non-time-based charts that filter noise and focus on significant price movements. Renko, Kagi, Point & Figure, Line Break, and Range Bars.</p>
        <div class="chart-row">
    """)

    for label, chart, stats in section2_charts:
        cid = chart._id
        html_parts.append(f"""
            <div class="chart-container">
                <div class="chart-title">{chart.title}</div>
                <div id="wrchart-{cid}"></div>
                <div class="chart-subtitle">{stats}</div>
            </div>
        """)

    html_parts.append("</div></div>")

    # Section 3: High-Frequency Data
    html_parts.append(f"""
    <div class="section">
        <h2 class="section-title">High-Frequency <span class="accent">Data Visualization</span></h2>
        <p class="description">LTTB (Largest Triangle Three Buckets) downsampling preserves visual fidelity while dramatically reducing data points for smooth rendering.</p>
        <div class="chart-row">
            <div class="chart-container" style="flex: 1;">
                <div class="chart-title">{chart_hf.title}</div>
                <div id="wrchart-{chart_hf._id}"></div>
                <div class="stats">
                    <span class="stat">Original: <span class="stat-value">{len(tick_df):,}</span> points</span>
                    <span class="stat">Displayed: <span class="stat-value">{len(display_df):,}</span> points</span>
                    <span class="stat">Compression: <span class="stat-value">{len(tick_df) / len(display_df):.1f}x</span></span>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">GPU-Accelerated <span class="accent">Million Point Rendering</span></h2>
        <p class="description">WebGL-powered rendering with dynamic Level of Detail (LOD). Handles 1M+ data points at 60fps with smooth pan/zoom. Uses GPU acceleration for real-time tick data visualization.</p>
        <div class="chart-row">
            <div class="chart-container" style="flex: 1;">
                {webgl_chart._generate_html()}
                <div class="chart-subtitle" style="margin-top: 12px;">
                    Controls: Mouse drag to pan, scroll to zoom. Dynamic LOD automatically adjusts detail based on zoom level.
                </div>
            </div>
        </div>
    </div>
    """)

    # Section 4: Overlay Indicators
    html_parts.append("""
    <div class="section">
        <h2 class="section-title">Overlay <span class="accent">Indicators</span></h2>
        <p class="description">Technical indicators plotted directly on the price chart: Moving Averages (SMA, EMA, WMA) and Bollinger Bands.</p>
        <div class="chart-row">
    """)

    for label, chart, stats in section4_charts:
        cid = chart._id
        html_parts.append(f"""
            <div class="chart-container" style="flex: 1;">
                <div class="chart-title">{chart.title}</div>
                <div id="wrchart-{cid}"></div>
            </div>
        """)

    html_parts.append("</div></div>")

    # Section 5: Oscillators
    html_parts.append("""
    <div class="section">
        <h2 class="section-title">Oscillator <span class="accent">Indicators</span></h2>
        <p class="description">Momentum indicators for overbought/oversold conditions and trend strength: RSI, Stochastic, and MACD.</p>
        <div class="chart-row">
    """)

    for label, chart, stats in section5_charts[:2]:  # RSI and Stochastic
        cid = chart._id
        html_parts.append(f"""
            <div class="chart-container">
                <div class="chart-title">{chart.title}</div>
                <div id="wrchart-{cid}"></div>
            </div>
        """)

    html_parts.append("</div><div class='chart-row'>")

    # MACD full width
    chart_macd_item = section5_charts[2]
    cid = chart_macd_item[1]._id
    html_parts.append(f"""
            <div class="chart-container" style="flex: 1;">
                <div class="chart-title">{chart_macd_item[1].title}</div>
                <div id="wrchart-{cid}"></div>
            </div>
    """)

    html_parts.append("</div></div>")

    # Add JavaScript to render all charts
    html_parts.append("<script>")
    html_parts.append("(function() {")

    for item in all_configs:
        config = item['config']
        cid = item['id']
        config_json = json.dumps(config)

        html_parts.append(f"""
            (function() {{
                const config = {config_json};
                const container = document.getElementById('wrchart-{cid}');
                if (!container) return;

                const chart = LightweightCharts.createChart(container, {{
                    width: config.width,
                    height: config.height,
                    layout: {{
                        ...config.options.layout,
                        attributionLogo: false
                    }},
                    ...config.options
                }});

                const seriesMap = {{}};
                config.series.forEach(seriesConfig => {{
                    let series;
                    switch(seriesConfig.type) {{
                        case 'Candlestick':
                            series = chart.addCandlestickSeries(seriesConfig.options);
                            break;
                        case 'Line':
                            series = chart.addLineSeries(seriesConfig.options);
                            break;
                        case 'Area':
                            series = chart.addAreaSeries(seriesConfig.options);
                            break;
                        case 'Histogram':
                            series = chart.addHistogramSeries(seriesConfig.options);
                            break;
                        default:
                            return;
                    }}
                    series.setData(seriesConfig.data);
                    seriesMap[seriesConfig.id] = series;
                }});

                const volumeSeries = config.series.find(s => s.options && s.options.priceScaleId === 'volume');
                if (volumeSeries) {{
                    chart.priceScale('volume').applyOptions({{
                        scaleMargins: {{ top: 0.8, bottom: 0 }}
                    }});
                }}

                chart.timeScale().fitContent();
            }})();
        """)

    html_parts.append("})();")
    html_parts.append("</script>")

    # Combine into full page
    charts_html = "\n".join(html_parts)
    full_html = generate_html_page(charts_html)

    # Write output
    output_path = 'demo.html'
    with open(output_path, 'w') as f:
        f.write(full_html)

    print(f"Demo generated: {output_path}")
    print(f"Chart types: Candlestick, Heikin-Ashi, Renko, Kagi, P&F, Line Break, Range Bars")
    print(f"Indicators: SMA, EMA, WMA, Bollinger Bands, RSI, MACD, Stochastic")
    print(f"High-frequency: {len(tick_df):,} points downsampled to {len(display_df):,}")


if __name__ == '__main__':
    main()
