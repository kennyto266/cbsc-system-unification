# Chart Hooks Documentation

A comprehensive collection of React hooks for managing real-time charts, responsive behavior, and export functionality.

## Overview

The chart hooks provide a unified interface for working with various chart libraries (Chart.js, Plotly.js, Recharts, Ant Design Charts) while handling common requirements like real-time data updates, responsive sizing, and export capabilities.

## Installation

```bash
# No additional installation required - hooks are part of the frontend project
```

## Available Hooks

### 1. useRealtimeChart

Main hook for managing real-time chart data with WebSocket connections. Handles data buffering, debouncing, automatic reconnection, data deduplication, and performance optimization.

#### Features

- **WebSocket Integration**: Automatic connection management with reconnection logic
- **Data Buffering**: Debounced updates to prevent excessive re-renders
- **Deduplication**: Optional duplicate filtering based on timestamps
- **Data Windowing**: Automatic data retention based on time windows
- **Performance Optimization**: Configurable data point limits and throttling
- **Export Capabilities**: Built-in CSV and JSON data export

#### Basic Usage

```tsx
import { useRealtimeChart, ChannelType } from '@/hooks/chart';

const MyRealtimeChart = () => {
  const {
    data,
    isConnected,
    error,
    totalPointsReceived,
    dataRate,
    clearData,
    togglePause
  } = useRealtimeChart({
    channelId: ChannelType.STRATEGY_UPDATES,
    maxDataPoints: 1000,
    updateThrottleMs: 100,
    enableDeduplication: true,
    dataWindowMs: 3600000, // 1 hour
    onDataAdd: (point) => console.log('New data:', point),
    enableDebug: true,
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2>Real-time Strategy Performance</h2>
        <div className="flex gap-2">
          <span className={`px-2 py-1 rounded text-sm ${
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          <span className="text-sm text-gray-600">
            {dataRate.toFixed(1)} pts/s
          </span>
          <button onClick={togglePause} className="px-3 py-1 bg-blue-500 text-white rounded">
            Pause
          </button>
          <button onClick={clearData} className="px-3 py-1 bg-red-500 text-white rounded">
            Clear
          </button>
        </div>
      </div>

      <Line data={{
        labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
        datasets: [{
          label: 'Value',
          data: data.map(d => d.value),
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
        }]
      }} />

      <div className="mt-4 text-sm text-gray-600">
        Total points: {totalPointsReceived} | Current: {data.length}
      </div>
    </div>
  );
};
```

#### Advanced Configuration

```tsx
const chartConfig = {
  channelId: ChannelType.PRICE_FEEDS,
  initialData: [], // Pre-populate with existing data
  maxDataPoints: 500,
  updateThrottleMs: 50,
  enableDeduplication: true,
  dataWindowMs: 1800000, // 30 minutes
  filters: { symbols: ['BTC', 'ETH'] }, // WebSocket filters
  dataTransformer: (message) => { // Custom data transformation
    return {
      timestamp: message.data.timestamp,
      value: message.data.price,
      label: message.data.symbol,
      metadata: {
        volume: message.data.volume,
        exchange: message.data.exchange
      }
    };
  },
  onDataAdd: (point) => {
    // Trigger alerts or calculations
    if (point.value > threshold) {
      notifyHighValue(point);
    }
  },
  onDataRemove: (count) => {
    console.log(`Removed ${count} old data points`);
  },
  autoReconnect: true,
  reconnectAttempts: 10,
  reconnectDelayMs: 2000,
  enableDebug: process.env.NODE_ENV === 'development'
};

const { data, exportData, reconnect } = useRealtimeChart(chartConfig);

// Export data for analysis
const downloadData = () => {
  const csvData = exportData('csv');
  downloadFile(csvData, 'chart-data.csv');
};
```

### 2. useChartResize

Manages chart responsive behavior using ResizeObserver. Provides debounced resize handling, container size tracking, and breakpoint support.

#### Features

- **ResizeObserver Integration**: Efficient size change detection
- **Debounced Handling**: Prevents excessive resize operations
- **Breakpoint Support**: Automatic device detection
- **Size Constraints**: Min/max dimensions and aspect ratio
- **Padding Support**: Subtract padding from calculated dimensions
- **Manual Triggers**: Programmatic resize control

#### Basic Usage

```tsx
import { useChartResize } from '@/hooks/chart';

const ResponsiveChart = () => {
  const {
    size,
    containerRef,
    isMobile,
    isTablet,
    breakpoint,
    isResizing
  } = useChartResize({
    debounceMs: 150,
    minWidth: 300,
    minHeight: 200,
    padding: { top: 10, right: 10, bottom: 30, left: 50 },
    breakpoints: {
      mobile: 768,
      tablet: 1024,
      desktop: 1440
    },
    onResize: (newSize, prevSize) => {
      console.log(`Chart resized: ${prevSize.width}x${prevSize.height} -> ${newSize.width}x${newSize.height}`);
    }
  });

  const chartOptions = {
    responsive: false,
    maintainAspectRatio: false,
    width: size.width,
    height: size.height,
    plugins: {
      legend: {
        display: !isMobile // Hide legend on mobile
      }
    }
  };

  return (
    <div className="w-full h-full">
      <div ref={containerRef} className="relative w-full h-full">
        {size.width > 0 && size.height > 0 ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <span className="text-gray-500">Loading chart...</span>
          </div>
        )}
        {isResizing && (
          <div className="absolute top-0 right-0 p-2">
            <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded">
              Resizing...
            </span>
          </div>
        )}
      </div>
      <div className="mt-2 text-sm text-gray-600">
        Size: {size.width}x{size.height} | Breakpoint: {breakpoint}
      </div>
    </div>
  );
};
```

#### Aspect Ratio Example

```tsx
const AspectRatioChart = () => {
  const { size, containerRef } = useChartResize({
    enableAspectRatio: true,
    aspectRatio: 16 / 9, // Widescreen
    maxWidth: 1920,
    maxHeight: 1080
  });

  return (
    <div className="chart-container">
      <div ref={containerRef} style={{ width: '100%' }}>
        <Scatter
          data={data}
          options={{
            responsive: false,
            width: size.width,
            height: size.height
          }}
        />
      </div>
    </div>
  );
};
```

### 3. useChartExport

Comprehensive hook for exporting charts to various formats. Supports PNG, JPG, SVG, CSV, and JSON exports with custom dimensions and quality settings.

#### Features

- **Multiple Formats**: PNG, JPG, SVG, CSV, JSON export
- **Chart Library Support**: Chart.js, Plotly, Recharts, Ant Design
- **Custom Dimensions**: High-resolution export with scaling
- **Quality Control**: Adjustable quality for lossy formats
- **Data Export**: Export chart data separately
- **Custom Exporters**: Extensible for custom chart types
- **Export History**: Track export operations

#### Basic Usage

```tsx
import { useChartExport } from '@/hooks/chart';

const ExportableChart = () => {
  const chartRef = useRef<HTMLCanvasElement>(null);

  const {
    exportToPNG,
    exportToJPG,
    exportToSVG,
    exportToCSV,
    exportToJSON,
    isExporting,
    exportHistory,
    clearHistory
  } = useChartExport({
    chartRef,
    chartType: 'chartjs',
    filename: 'my-chart',
    data: chartData,
    defaultOptions: {
      width: 1920,
      height: 1080,
      quality: 0.9,
      backgroundColor: '#ffffff',
      scale: 2
    }
  });

  return (
    <div className="space-y-4">
      <div className="relative">
        <canvas ref={chartRef} />
        {isExporting && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <span className="text-white">Exporting to {isExporting}...</span>
          </div>
        )}
      </div>

      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => exportToPNG()}
          disabled={isExporting !== null}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          Export as PNG
        </button>

        <button
          onClick={() => exportToJPG({ quality: 0.8, backgroundColor: '#f0f0f0' })}
          disabled={isExporting !== null}
          className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
        >
          Export as JPG
        </button>

        <button
          onClick={() => exportToSVG()}
          disabled={isExporting !== null}
          className="px-4 py-2 bg-purple-500 text-white rounded disabled:opacity-50"
        >
          Export as SVG
        </button>

        <button
          onClick={() => exportToCSV()}
          disabled={isExporting !== null}
          className="px-4 py-2 bg-orange-500 text-white rounded disabled:opacity-50"
        >
          Export Data (CSV)
        </button>

        <button
          onClick={() => exportToJSON()}
          disabled={isExporting !== null}
          className="px-4 py-2 bg-gray-500 text-white rounded disabled:opacity-50"
        >
          Export Data (JSON)
        </button>
      </div>

      {exportHistory.length > 0 && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">Export History</h3>
            <button
              onClick={clearHistory}
              className="text-sm text-red-500 hover:text-red-700"
            >
              Clear History
            </button>
          </div>
          <ul className="space-y-1 text-sm text-gray-600">
            {exportHistory.map((export_, index) => (
              <li key={index}>
                {export_.format.toUpperCase()} - {export_.filename} -
                {new Date(export_.timestamp).toLocaleString()}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

#### Custom Export Function

```tsx
const CustomChartExport = () => {
  const customExportFunction = async (format: ExportFormat, options: ExportOptions) => {
    // Custom export logic for a non-standard chart library
    if (format === 'png') {
      const canvas = await convertCustomChartToCanvas(chartElement);
      return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/png', options.quality);
      });
    }
    return null;
  };

  const { export: customExport } = useChartExport({
    chartRef,
    chartType: 'custom',
    customExportFunction
  });

  // Export with custom dimensions
  const exportHighRes = () => {
    customExport('png', {
      width: 3840,
      height: 2160,
      scale: 3,
      filename: 'chart-4k'
    });
  };
};
```

## Combined Usage Example

```tsx
import {
  useRealtimeChart,
  useChartResize,
  useChartExport,
  ChannelType
} from '@/hooks/chart';

const ComprehensiveChart = () => {
  const chartRef = useRef<HTMLDivElement>(null);

  // Real-time data management
  const {
    data,
    isConnected,
    error,
    dataRate,
    togglePause,
    clearData
  } = useRealtimeChart({
    channelId: ChannelType.STRATEGY_UPDATES,
    maxDataPoints: 1000,
    enableDeduplication: true
  });

  // Responsive sizing
  const {
    size,
    containerRef,
    isMobile,
    breakpoint
  } = useChartResize({
    ref: chartRef,
    debounceMs: 150,
    padding: { top: 20, right: 20, bottom: 40, left: 60 }
  });

  // Export functionality
  const {
    exportToPNG,
    exportToSVG,
    exportToCSV,
    isExporting
  } = useChartExport({
    chartRef,
    chartType: 'chartjs',
    filename: `strategy-chart-${breakpoint}`,
    data: data
  });

  // Chart configuration
  const chartData = {
    labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [{
      label: 'Strategy Value',
      data: data.map(d => d.value),
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      tension: 0.1
    }]
  };

  const chartOptions = {
    responsive: false,
    maintainAspectRatio: false,
    width: size.width,
    height: size.height,
    plugins: {
      legend: {
        display: !isMobile
      },
      zoom: {
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true
          },
          mode: 'x',
        }
      }
    },
    scales: {
      x: {
        display: !isMobile
      }
    }
  };

  return (
    <div className="w-full h-full p-4">
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-xl font-bold">Strategy Performance</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm">
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          <span className="text-sm text-gray-600">
            {dataRate.toFixed(1)} pts/s
          </span>
        </div>
      </div>

      <div
        ref={chartRef}
        className="relative bg-white rounded-lg shadow-lg"
        style={{ minHeight: '400px' }}
      >
        {size.width > 0 && (
          <Line data={chartData} options={chartOptions} />
        )}

        {isExporting && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
            <div className="text-white">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2" />
              Exporting...
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 flex justify-between items-center">
        <div className="flex gap-2">
          <button
            onClick={() => togglePause()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Pause Updates
          </button>
          <button
            onClick={clearData}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Clear Data
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => exportToPNG()}
            disabled={isExporting !== null}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            Save as PNG
          </button>
          <button
            onClick={() => exportToSVG()}
            disabled={isExporting !== null}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
          >
            Save as SVG
          </button>
          <button
            onClick={() => exportToCSV()}
            disabled={isExporting !== null}
            className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
          >
            Export Data
          </button>
        </div>
      </div>

      <div className="mt-2 text-sm text-gray-600 text-center">
        Chart size: {size.width}x{size.height} | Breakpoint: {breakpoint} | Data points: {data.length}
      </div>
    </div>
  );
};
```

## Best Practices

### Performance Optimization

1. **Use Debouncing**: Configure appropriate debounce delays for your use case
2. **Limit Data Points**: Set reasonable maxDataPoints to prevent memory issues
3. **Enable Deduplication**: Prevent duplicate data from affecting performance
4. **Use Data Windowing**: Automatically prune old data based on time

### Error Handling

```tsx
const { data, error, isConnected } = useRealtimeChart(config);

useEffect(() => {
  if (error) {
    console.error('Chart error:', error);
    // Show error notification
    showErrorNotification(`Chart connection error: ${error.message}`);
  }
}, [error]);

useEffect(() => {
  if (!isConnected) {
    // Show reconnecting state
    showReconnectingState();
  }
}, [isConnected]);
```

### Memory Management

```tsx
// Clear data on unmount
useEffect(() => {
  return () => {
    clearData();
  };
}, [clearData]);

// Implement periodic cleanup
useEffect(() => {
  const interval = setInterval(() => {
    // Remove data older than 1 hour
    setDataWindow(3600000);
  }, 300000); // Every 5 minutes

  return () => clearInterval(interval);
}, []);
```

## API Reference

### useRealtimeChart

#### Config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| channelId | `ChannelType` | Required | WebSocket channel to subscribe to |
| initialData | `ChartDataPoint[]` | `[]` | Initial data array |
| maxDataPoints | `number` | `1000` | Maximum data points to keep |
| updateThrottleMs | `number` | `100` | Throttle for updates |
| enableDeduplication | `boolean` | `true` | Filter duplicate points |
| dataWindowMs | `number` | `3600000` | Data retention window |
| filters | `Record<string, any>` | `undefined` | WebSocket filters |
| dataTransformer | `(message) => ChartDataPoint` | `undefined` | Custom transformer |
| autoReconnect | `boolean` | `true` | Enable reconnection |
| reconnectAttempts | `number` | `5` | Max reconnection attempts |
| reconnectDelayMs | `number` | `1000` | Reconnection delay |

### useChartResize

#### Config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ref | `React.RefObject` | `undefined` | Container element ref |
| debounceMs | `number` | `150` | Resize debounce delay |
| breakpoints | `ChartBreakpoints` | `{ mobile: 768, tablet: 1024, desktop: 1440 }` | Breakpoint widths |
| enableAspectRatio | `boolean` | `false` | Maintain aspect ratio |
| aspectRatio | `number` | `16/9` | Width/height ratio |
| minWidth | `number` | `100` | Minimum width |
| minHeight | `number` | `100` | Minimum height |
| maxWidth | `number` | `undefined` | Maximum width |
| maxHeight | `number` | `undefined` | Maximum height |
| padding | `{ top?, right?, bottom?, left? }` | `{}` | Padding to subtract |

### useChartExport

#### Config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| chartRef | `React.RefObject` | Required | Chart container ref |
| chartType | `ChartType` | `'chartjs'` | Chart library type |
| data | `any[]` | `undefined` | Data for CSV/JSON export |
| filename | `string` | `'chart'` | Default filename |
| customExportFunction | `(format, options) => Promise<Blob>` | `undefined` | Custom exporter |

## Troubleshooting

### Common Issues

1. **WebSocket Not Connecting**
   - Check server is running
   - Verify channel ID is correct
   - Check authentication

2. **Chart Not Resizing**
   - Ensure container has dimensions
   - Check ResizeObserver support
   - Verify padding values

3. **Export Not Working**
   - Ensure chart ref is valid
   - Check chart library compatibility
   - Verify canvas/SVG exists

4. **Performance Issues**
   - Increase throttle/debounce values
   - Reduce maxDataPoints
   - Enable data deduplication
   - Use data windowing

### Debug Mode

Enable debug logging for troubleshooting:

```tsx
const config = {
  enableDebug: true, // For all hooks
  // ... other options
};
```

## Migration Guide

### From Manual Chart Management

```tsx
// Before
const [data, setData] = useState([]);
const [isConnected, setIsConnected] = useState(false);

useEffect(() => {
  const ws = new WebSocket('ws://localhost:3004');
  ws.onmessage = (event) => {
    const point = JSON.parse(event.data);
    setData(prev => [...prev.slice(-999), point]);
  };
  return () => ws.close();
}, []);

// After
const { data, isConnected } = useRealtimeChart({
  channelId: ChannelType.PRICE_FEEDS,
  maxDataPoints: 1000
});
```

## Contributing

When adding new features or fixing bugs:

1. Update TypeScript types
2. Add comprehensive tests
3. Update documentation
4. Consider backward compatibility
5. Test with all supported chart libraries