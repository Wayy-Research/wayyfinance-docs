# @wayy/wrchart

React charting components for financial data, built on TradingView Lightweight Charts.

## Install

```bash
npm install @wayy/wrchart
```

Requires React 18+.

## Usage

```tsx
import { WayyChart, wayyDarkTheme } from '@wayy/wrchart';

function App() {
  const data = [
    { time: '2024-01-01', open: 100, high: 105, low: 98, close: 103 },
    { time: '2024-01-02', open: 103, high: 107, low: 101, close: 106 },
  ];

  return <WayyChart data={data} theme={wayyDarkTheme} width={900} height={500} />;
}
```

## Components

- **WayyChart** — Main chart component (candlestick, line, area, histogram)
- **TradeHeatmap** — WebGL trade heatmap overlay
- **DrawingOverlay** — Drawing tools (trendlines, fibonacci, etc.)

## Hooks

- **useChartData** — Fetch and manage chart data with loading/error states
- **useLivePrice** — Real-time WebSocket price streaming
- **useDrawings** — Manage drawing tools state

## Themes

- `wayyDarkTheme` — Dark background, white/red candles
- `wayyLightTheme` — Light background, black/red candles
- `WAYY_COLORS` — Brand color constants
- `WAYY_FONTS` — JetBrains Mono, Space Grotesk

## License

MIT — [Wayy Research](https://wayy.pro)
