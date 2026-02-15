# @wayy/wrchart -- API Reference

> Version: 0.2.0 | Node >=18, React >=18 | Install: `npm install @wayy/wrchart`

React charting components built on TradingView Lightweight Charts with Wayy brand styling. Provides candlestick, line, area, and histogram charts, a WebGL trade heatmap, drawing tools, and hooks for real-time data streaming.

Peer dependencies: `react >=18.0.0`, `react-dom >=18.0.0`. Ships `lightweight-charts ^4.1.0` as a direct dependency.

```bash
npm install @wayy/wrchart
# or
yarn add @wayy/wrchart
```

---

## Quick Start

```tsx
import { WayyChart, wayyDarkTheme } from '@wayy/wrchart';

function PriceChart() {
  const data = [
    { time: '2024-01-01', open: 100, high: 105, low: 98, close: 103, volume: 42000 },
    { time: '2024-01-02', open: 103, high: 107, low: 101, close: 106, volume: 38000 },
    { time: '2024-01-03', open: 106, high: 110, low: 104, close: 109, volume: 51000 },
  ];

  return <WayyChart data={data} theme="dark" width={900} height={500} />;
}
```

---

## Core API

### Components

#### `WayyChart`

Main chart component. Renders candlestick, line, area, or histogram series with optional volume overlay, price lines, and markers.

```tsx
import { WayyChart } from '@wayy/wrchart';
import type { WayyChartProps, WayyChartRef } from '@wayy/wrchart';
```

**Props (`WayyChartProps`)**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `WayyChartData[]` | required | Array of OHLCV bars or value points |
| `type` | `SeriesType` | `'candlestick'` | `'candlestick'`, `'line'`, `'area'`, `'histogram'` |
| `theme` | `ChartTheme` | `'dark'` | `'dark'` or `'light'` |
| `width` | `number \| string` | `'100%'` | Chart width in pixels or CSS value |
| `height` | `number \| string` | `400` | Chart height in pixels or CSS value |
| `autosize` | `boolean` | `true` | Resize chart with container via ResizeObserver |
| `showVolume` | `boolean` | `true` | Show volume histogram (candlestick mode only) |
| `showGrid` | `boolean` | `true` | Show background grid lines |
| `showCrosshair` | `boolean` | `true` | Show crosshair on hover |
| `markers` | `SeriesMarker<Time>[]` | `[]` | Buy/sell markers on the series |
| `priceLines` | `PriceLine[]` | `[]` | Horizontal price lines. Each: `{ price, color, title?, lineWidth? }` |
| `chartOptions` | `DeepPartial<ChartOptions>` | `{}` | Override LW Charts options (merged with theme) |
| `seriesOptions` | `DeepPartial<...>` | `{}` | Override series-specific options |
| `onCrosshairMove` | `(param: { time?, price? }) => void` | -- | Callback on crosshair movement |
| `onClick` | `(param: { time?, price? }) => void` | -- | Callback on chart click |
| `className` | `string` | `''` | CSS class on the container div |
| `style` | `React.CSSProperties` | `{}` | Inline styles on the container div |

**Ref (`WayyChartRef`)**

Access the imperative API via `useRef<WayyChartRef>()`.

| Method/Property | Type | Description |
|----------------|------|-------------|
| `chart` | `IChartApi \| null` | Raw Lightweight Charts API |
| `series` | `ISeriesApi<any> \| null` | Main series API |
| `volumeSeries` | `ISeriesApi<any> \| null` | Volume series API (if `showVolume`) |
| `fitContent()` | `() => void` | Fit all data into view |
| `scrollToRealtime()` | `() => void` | Scroll to latest bar |
| `setData(data)` | `(data: WayyChartData[]) => void` | Replace all series data |
| `updateData(data)` | `(data: WayyChartData) => void` | Update or append a single bar |
| `addMarker(marker)` | `(marker: SeriesMarker<Time>) => void` | Add one marker |
| `removeMarkers()` | `() => void` | Clear all markers |

**Data type (`WayyChartData`)**

```ts
interface WayyChartData {
  time: Time;           // '2024-01-01' or Unix seconds
  open?: number;        // Used by candlestick
  high?: number;
  low?: number;
  close?: number;       // Used by candlestick, line, area
  value?: number;       // Used by line, area, histogram
  volume?: number;      // Used by volume overlay
  color?: string;       // Per-bar color override (histogram)
}
```

---

#### `TradeHeatmap`

WebGL-rendered heatmap showing buy/sell volume at each price level with time-decay coloring. Renders at 60fps using a dual-canvas architecture: WebGL for the heatmap bars, 2D canvas overlay for labels and grid.

```tsx
import { TradeHeatmap } from '@wayy/wrchart';
import type { TradeHeatmapProps, Trade, PriceLevel } from '@wayy/wrchart';
```

**Props (`TradeHeatmapProps`)**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `trades` | `Trade[]` | required | Array of trade events to visualize |
| `currentPrice` | `number` | `0` | Current mid price (centers the view) |
| `tickSize` | `number` | `1` | Price increment per level |
| `visibleLevels` | `number` | `40` | Number of price levels visible |
| `decayTimeMs` | `number` | `30000` | Time in ms before trades fade out |
| `width` | `number \| string` | `'100%'` | Component width |
| `height` | `number \| string` | `500` | Component height |
| `showPriceAxis` | `boolean` | `true` | Show price labels on right side |
| `showTimeAxis` | `boolean` | `false` | Reserved for future use |
| `onPriceClick` | `(price: number) => void` | -- | Callback when a price level is clicked |
| `onPriceHover` | `(price: number \| null) => void` | -- | Callback on price level hover |
| `className` | `string` | `''` | CSS class |
| `style` | `React.CSSProperties` | `{}` | Inline styles |

**Types**

```ts
interface Trade {
  time: number;              // Unix timestamp (ms)
  price: number;
  quantity: number;
  side: 'buy' | 'sell';
}

interface PriceLevel {
  price: number;
  buyVolume: number;
  sellVolume: number;
  lastTradeTime: number;
  trades: Trade[];
}
```

---

#### `DrawingOverlay`

Canvas overlay for chart drawing tools. Renders trendlines, horizontal lines, rectangles, and Fibonacci retracements. Positioned absolutely over a chart, receiving coordinate conversion functions from the parent.

```tsx
import { DrawingOverlay } from '@wayy/wrchart';
import type { DrawingOverlayProps } from '@wayy/wrchart';
```

**Props (`DrawingOverlayProps`)**

| Prop | Type | Description |
|------|------|-------------|
| `drawings` | `Drawing[]` | Completed drawings to render |
| `activeTool` | `DrawingTool \| null` | Currently active tool (`null` = pointer mode) |
| `pendingPoints` | `DrawingPoint[]` | Points collected for in-progress drawing |
| `width` | `number` | Canvas width in CSS pixels |
| `height` | `number` | Canvas height in CSS pixels |
| `timeToX` | `(time: number) => number \| null` | Convert UTC timestamp to X pixel |
| `priceToY` | `(price: number) => number \| null` | Convert price to Y pixel |
| `xToTime` | `(x: number) => number \| null` | Convert X pixel to UTC timestamp |
| `yToPrice` | `(y: number) => number \| null` | Convert Y pixel to price |
| `onDrawingClick` | `(point: DrawingPoint) => void` | Called when user clicks while a tool is active |

The overlay sets `pointerEvents: 'none'` when no tool is active, so it does not interfere with the chart underneath.

---

### Hooks

#### `useChartData`

Fetches OHLCV data from a REST endpoint with optional WebSocket real-time updates and auto-refresh.

```tsx
import { useChartData } from '@wayy/wrchart';
import type { UseChartDataOptions, ChartDataState } from '@wayy/wrchart';
```

**Options (`UseChartDataOptions`)**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `symbol` | `string` | required | Ticker symbol |
| `interval` | `string` | `'1h'` | `'1m'`, `'5m'`, `'15m'`, `'1h'`, `'4h'`, `'1d'`, `'1w'` |
| `limit` | `number` | `500` | Max bars to fetch |
| `apiUrl` | `string` | `'/api/v2/ohlcv'` | REST endpoint base URL |
| `wsUrl` | `string` | -- | WebSocket URL for live updates (optional) |
| `autoRefresh` | `boolean` | `false` | Poll the REST endpoint on interval |
| `refreshIntervalMs` | `number` | `60000` | Polling interval in ms (when `autoRefresh` is true) |

**Returns (`ChartDataState`)**

| Field | Type | Description |
|-------|------|-------------|
| `data` | `WayyChartData[]` | Fetched/streamed chart data |
| `loading` | `boolean` | `true` during initial fetch |
| `error` | `Error \| null` | Fetch or parse error |
| `lastUpdate` | `number \| null` | Timestamp (ms) of last data update |
| `refresh` | `() => Promise<void>` | Manually re-fetch data |

The hook fetches `GET {apiUrl}/{symbol}?interval={interval}&limit={limit}`. It expects a JSON array of objects with `time`, `open`, `high`, `low`, `close`, `volume` fields.

When `wsUrl` is provided, the hook connects to `{wsUrl}?symbol={symbol}&interval={interval}` and merges incoming bars: matching timestamps update in place, new timestamps append. Auto-reconnects after 3 seconds on close.

---

#### `useLivePrice`

Real-time bid/ask/last price streaming via WebSocket with auto-reconnect.

```tsx
import { useLivePrice } from '@wayy/wrchart';
import type { UseLivePriceOptions, LivePriceState } from '@wayy/wrchart';
```

**Options (`UseLivePriceOptions`)**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `symbol` | `string` | required | Ticker symbol |
| `wsUrl` | `string` | `'/ws/market'` | WebSocket base URL |
| `reconnectIntervalMs` | `number` | `3000` | Reconnect delay in ms |

Connects to `{wsUrl}/{symbol}`.

**Returns (`LivePriceState`)**

| Field | Type | Description |
|-------|------|-------------|
| `bid` | `number \| null` | Best bid price |
| `ask` | `number \| null` | Best ask price |
| `last` | `number \| null` | Last trade price |
| `bidSize` | `number \| null` | Bid size |
| `askSize` | `number \| null` | Ask size |
| `volume` | `number \| null` | Session volume |
| `change` | `number \| null` | Price change |
| `changePercent` | `number \| null` | Percent change |
| `connected` | `boolean` | WebSocket connection status |
| `lastUpdate` | `number \| null` | Timestamp (ms) of last message |

---

#### `useDrawings`

Manages chart drawing state with per-symbol localStorage persistence. Handles tool selection, point collection, auto-completion, and CRUD operations.

```tsx
import { useDrawings } from '@wayy/wrchart';
import type {
  UseDrawingsOptions,
  UseDrawingsResult,
  Drawing,
  DrawingPoint,
  DrawingTool,
} from '@wayy/wrchart';
```

**Options (`UseDrawingsOptions`)**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `symbol` | `string` | required | Current chart symbol (filters visible drawings) |
| `storageKey` | `string` | `'wayy_drawings'` | localStorage key prefix |
| `defaultColor` | `string` | `'#E53935'` | Default drawing color (Wayy red) |
| `defaultLineWidth` | `number` | `1` | Default line width |

**Returns (`UseDrawingsResult`)**

| Field | Type | Description |
|-------|------|-------------|
| `drawings` | `Drawing[]` | Drawings for the current symbol |
| `allDrawings` | `Drawing[]` | All drawings across all symbols |
| `activeTool` | `DrawingTool \| null` | Currently selected tool |
| `pendingPoints` | `DrawingPoint[]` | Points collected for in-progress drawing |
| `setActiveTool(tool)` | `(tool: DrawingTool \| null) => void` | Select a tool (null to deactivate) |
| `addPoint(point)` | `(point: DrawingPoint) => void` | Add a point. Auto-completes when enough points collected. |
| `cancelDrawing()` | `() => void` | Cancel in-progress drawing |
| `deleteDrawing(id)` | `(id: string) => void` | Delete a drawing by ID |
| `clearDrawings()` | `() => void` | Delete all drawings for current symbol |

**Types**

```ts
type DrawingTool = 'trendline' | 'hline' | 'rectangle' | 'fib';

interface DrawingPoint {
  time: number;   // UTC seconds
  price: number;
}

interface Drawing {
  id: string;
  tool: DrawingTool;
  symbol: string;
  points: DrawingPoint[];
  color: string;
  lineWidth: number;
  created: number;  // Date.now() timestamp
}
```

Points required per tool: `hline` = 1, `trendline` = 2, `rectangle` = 2, `fib` = 2. After completion the tool stays active for rapid sequential drawing.

---

### Themes

Brand-aligned styling for TradingView Lightweight Charts.

```tsx
import {
  WAYY_COLORS,
  WAYY_FONTS,
  wayyDarkTheme,
  wayyLightTheme,
  wayyCandles,
  wayyArea,
  wayyLine,
  wayyVolume,
  wayyMarkers,
  getVolumeColor,
  hexToRgba,
} from '@wayy/wrchart';
```

#### `WAYY_COLORS`

```ts
const WAYY_COLORS = {
  black: '#000000',
  white: '#FFFFFF',
  red: '#E53935',           // Brand accent, sells, down
  redLight: '#fff5f5',
  green: '#22c55e',          // Buys, up
  greenDark: '#16a34a',
  redDark: '#c62828',
  gray50: '#fafafa',
  gray100: '#f5f5f5',
  gray200: '#e0e0e0',
  gray400: '#888888',
  gray600: '#555555',
  gray800: '#333333',
  gray900: '#1a1a1a',
  grid: '#1a1a1a',
  crosshair: '#888888',
  volume: 'rgba(136, 136, 136, 0.3)',
} as const;
```

#### `WAYY_FONTS`

```ts
const WAYY_FONTS = {
  serif: "'Instrument Serif', Georgia, serif",
  sans: "'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;
```

#### Chart themes

| Export | Description |
|--------|-------------|
| `wayyDarkTheme` | Black background (`#000`), gray text, dark grid. Primary theme. |
| `wayyLightTheme` | White background, dark text, light grid. |

Both are `DeepPartial<ChartOptions>` objects passed directly to `WayyChart`'s `theme` prop or merged into `chartOptions`.

#### Series presets

| Export | Series Type | Key Colors |
|--------|-------------|------------|
| `wayyCandles` | Candlestick | Green up (`#22c55e`), red down (`#E53935`) |
| `wayyArea` | Area | White line, white-to-transparent fill |
| `wayyLine` | Line | White, 2px width |
| `wayyVolume` | Histogram | Volume price scale config |
| `wayyMarkers` | Markers | `.buy` (green arrow up), `.sell` (red arrow down) |

#### Utility functions

**`getVolumeColor(isUp: boolean, opacity?: number): string`**

Returns `rgba(...)` string for volume bars. Green if `isUp`, red otherwise.

**`hexToRgba(hex: string, alpha?: number): string`**

Converts hex color to `rgba(r, g, b, alpha)` string.

---

### Re-exports from lightweight-charts

These types are re-exported so you do not need to install `lightweight-charts` directly:

```ts
export type {
  IChartApi,
  ISeriesApi,
  Time,
  SeriesMarker,
  DeepPartial,
  ChartOptions,
  CandlestickData,
  LineData,
  HistogramData,
} from 'lightweight-charts';
```

---

## Common Patterns

### Candlestick chart with dark theme

```tsx
import { WayyChart } from '@wayy/wrchart';

function App() {
  const data = [
    { time: '2024-01-01', open: 100, high: 105, low: 98, close: 103, volume: 42000 },
    { time: '2024-01-02', open: 103, high: 107, low: 101, close: 106, volume: 38000 },
    { time: '2024-01-03', open: 106, high: 110, low: 104, close: 109, volume: 51000 },
  ];

  return <WayyChart data={data} theme="dark" showVolume width={900} height={500} />;
}
```

### Live streaming chart

```tsx
import { useRef, useEffect } from 'react';
import { WayyChart, useChartData, useLivePrice } from '@wayy/wrchart';
import type { WayyChartRef } from '@wayy/wrchart';

function LiveChart({ symbol }: { symbol: string }) {
  const chartRef = useRef<WayyChartRef>(null);
  const { data, loading, error } = useChartData({
    symbol,
    interval: '1m',
    apiUrl: '/api/v2/ohlcv',
    wsUrl: 'wss://your-server.com/ws/ohlcv',
  });

  const { last, bid, ask, connected } = useLivePrice({
    symbol,
    wsUrl: 'wss://your-server.com/ws/market',
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <div>Last: {last} | Bid: {bid} | Ask: {ask} | {connected ? 'LIVE' : 'OFFLINE'}</div>
      <WayyChart ref={chartRef} data={data} theme="dark" height={600} />
    </div>
  );
}
```

### Chart with drawing tools

```tsx
import { useRef, useCallback } from 'react';
import { WayyChart, DrawingOverlay, useDrawings } from '@wayy/wrchart';
import type { WayyChartRef, DrawingTool } from '@wayy/wrchart';

function ChartWithDrawings({ symbol, data }: { symbol: string; data: any[] }) {
  const chartRef = useRef<WayyChartRef>(null);
  const {
    drawings,
    activeTool,
    pendingPoints,
    setActiveTool,
    addPoint,
    clearDrawings,
  } = useDrawings({ symbol });

  // Build coordinate converters from the chart API
  const timeToX = useCallback(
    (time: number) => chartRef.current?.chart?.timeScale().timeToCoordinate(time as any) ?? null,
    []
  );
  const priceToY = useCallback(
    (price: number) => chartRef.current?.series?.priceToCoordinate(price) ?? null,
    []
  );
  const xToTime = useCallback(
    (x: number) => {
      const t = chartRef.current?.chart?.timeScale().coordinateToTime(x);
      return t != null ? (t as number) : null;
    },
    []
  );
  const yToPrice = useCallback(
    (y: number) => chartRef.current?.series?.coordinateToPrice(y) ?? null,
    []
  );

  return (
    <div style={{ position: 'relative' }}>
      <div>
        <button onClick={() => setActiveTool('trendline')}>Trendline</button>
        <button onClick={() => setActiveTool('hline')}>H-Line</button>
        <button onClick={() => setActiveTool('fib')}>Fibonacci</button>
        <button onClick={() => setActiveTool(null)}>Pointer</button>
        <button onClick={clearDrawings}>Clear All</button>
      </div>
      <WayyChart ref={chartRef} data={data} theme="dark" height={600} />
      <DrawingOverlay
        drawings={drawings}
        activeTool={activeTool}
        pendingPoints={pendingPoints}
        width={900}
        height={600}
        timeToX={timeToX}
        priceToY={priceToY}
        xToTime={xToTime}
        yToPrice={yToPrice}
        onDrawingClick={addPoint}
      />
    </div>
  );
}
```

### Trade heatmap for order flow

```tsx
import { TradeHeatmap } from '@wayy/wrchart';
import type { Trade } from '@wayy/wrchart';

function OrderFlow({ trades, currentPrice }: { trades: Trade[]; currentPrice: number }) {
  return (
    <TradeHeatmap
      trades={trades}
      currentPrice={currentPrice}
      tickSize={0.5}
      visibleLevels={60}
      decayTimeMs={60000}
      height={700}
      onPriceClick={(price) => console.log('Clicked price level:', price)}
    />
  );
}
```

### Buy/sell markers on chart

```tsx
import { WayyChart, wayyMarkers } from '@wayy/wrchart';
import type { SeriesMarker, Time } from '@wayy/wrchart';

function ChartWithSignals({ data, signals }) {
  const markers: SeriesMarker<Time>[] = signals.map((s) => ({
    time: s.time as Time,
    ...(s.side === 'buy' ? wayyMarkers.buy : wayyMarkers.sell),
    text: `${s.side.toUpperCase()} @ ${s.price}`,
  }));

  return <WayyChart data={data} theme="dark" markers={markers} height={500} />;
}
```

---

## Gotchas

**React 18+ required.** The package uses `forwardRef`, `useImperativeHandle`, and expects React 18 concurrent features. Will not work with React 17 or below.

**Data must be an array, not a DataFrame.** Transform your data to `WayyChartData[]` before passing to `WayyChart`. The `time` field accepts ISO date strings (`'2024-01-01'`) or Unix timestamps in seconds.

**Theme objects are deeply merged.** `chartOptions` merges on top of the selected theme. To override a specific nested property, you do not need to provide the full theme -- just the overriding keys.

**Volume only renders in candlestick mode.** The `showVolume` prop is ignored when `type` is `'line'`, `'area'`, or `'histogram'`.

**Ref is null during first render.** The `WayyChartRef` methods (`fitContent`, `setData`, etc.) are only available after the chart mounts. Guard calls with `chartRef.current?.fitContent()`.

**DrawingOverlay requires coordinate converters.** It does not access the chart API directly. You must wire up `timeToX`, `priceToY`, `xToTime`, and `yToPrice` from the parent chart's `IChartApi` and `ISeriesApi`.

**`tsup` build note.** When bundling with `tsup`, set `treeshake: false` in your `tsup.config.ts`. The `DrawingOverlay` component can be tree-shaken out incorrectly due to complex React dependencies.

**WebSocket hooks auto-reconnect.** Both `useChartData` (when `wsUrl` is set) and `useLivePrice` reconnect automatically after a close event. There is no manual reconnect function exposed.

**Use `??` not `||` for numeric state.** `LivePriceState` fields like `last`, `bid`, `ask` can be `0` (legitimate). Use `state.last ?? 'N/A'` instead of `state.last || 'N/A'` to avoid treating zero as falsy.

---

## Integration

**Python counterpart.** This is the TypeScript/React counterpart of [wrchart](../wrchart/reference.md) (Python). Same Wayy brand colors and visual language. Python `wrchart` produces standalone HTML/Jupyter output; `@wayy/wrchart` renders inside React component trees.

**Backend data source.** Typically used with backends powered by [wrdata](../wrdata/reference.md) for market data and [wayy-db](../wayydb/reference.md) for temporal queries. The `useChartData` hook expects a REST API returning JSON arrays of OHLCV bars.

**Brand consistency.** All Wayy frontend apps share `WAYY_COLORS` and `WAYY_FONTS`. Import them from `@wayy/wrchart` to stay consistent across your UI: black backgrounds, `#E53935` red accent, JetBrains Mono for data, Space Grotesk for labels.

---

Built by [Wayy Research](https://wayy.pro), Buffalo NY.
*People for research, research for people.*
