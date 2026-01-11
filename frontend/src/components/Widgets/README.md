# Strategy Performance Widgets

This directory contains React components for displaying real-time trading strategy performance data in the CBSC quantitative trading platform dashboard.

## Components

### 1. StrategyStatusWidget
Displays real-time status of all trading strategies with the ability to toggle them on/off.

**Features:**
- Real-time status updates via WebSocket
- Strategy toggle functionality
- Daily P&L display
- Win rate calculation
- Mini sparkline charts
- Error handling and display

**Usage:**
```tsx
import { StrategyStatusWidget } from '@/components/Widgets';

<StrategyStatusWidget
  onToggleStrategy={(strategyId, enabled) => {
    // Handle strategy toggle
  }}
  onViewDetails={(strategyId) => {
    // Navigate to strategy details
  }}
/>
```

### 2. PerformanceMetricsWidget
Shows comprehensive performance indicators including Sharpe ratio, maximum drawdown, and other risk metrics.

**Features:**
- Multiple view modes (Returns, Risk, Efficiency)
- Historical performance charts
- Benchmark comparison
- Period selection (1D, 1W, 1M, 3M, 6M, 1Y, All)
- Interactive tooltips with metric definitions

**Usage:**
```tsx
import { PerformanceMetricsWidget } from '@/components/Widgets';

<PerformanceMetricsWidget
  onPeriodChange={(period) => {
    // Handle period change
  }}
  onBenchmarkChange={(benchmark) => {
    // Handle benchmark change
  }}
/>
```

### 3. PortfolioOverviewWidget
Provides a comprehensive view of portfolio allocation, holdings, and rebalancing suggestions.

**Features:**
- Asset allocation pie chart
- Sector breakdown
- Top holdings list
- Rebalancing suggestions
- Cash and margin information
- Interactive treemap view

**Usage:**
```tsx
import { PortfolioOverviewWidget } from '@/components/Widgets';

<PortfolioOverviewWidget
  onRebalance={(suggestions) => {
    // Execute rebalancing
  }}
  onViewAsset={(symbol) => {
    // Navigate to asset details
  }}
/>
```

## Custom Hooks

### useStrategyUpdates
Custom hook for managing real-time strategy updates via WebSocket.

**Features:**
- Automatic reconnection
- Strategy state management
- Toggle functionality
- Performance statistics

**Usage:**
```tsx
import { useStrategyUpdates } from '@/hooks/useStrategyUpdates';

const {
  strategies,
  isConnected,
  toggleStrategy,
  getActiveCount,
  getTotalPnL,
  getWinRate
} = useStrategyUpdates({
  autoReconnect: true,
  maxRetries: 10
});
```

## Dependencies

These components require the following dependencies:

```bash
npm install recharts lucide-react
```

And the following peer dependencies (already installed in the project):

- React 18+
- TypeScript
- Tailwind CSS
- WebSocket Context

## WebSocket Integration

The widgets use the existing WebSocket infrastructure for real-time updates:

### Message Format

```typescript
// Strategy status update
{
  channel: 'strategies',
  type: 'strategy_update',
  strategyId: 'string',
  data: {
    status: 'active' | 'inactive' | 'error' | 'paused',
    dailyPnL: number,
    totalReturn: number,
    // ... other strategy properties
  }
}

// Performance metrics update
{
  channel: 'performance',
  type: 'metrics_update',
  data: PerformanceMetrics
}

// Portfolio update
{
  channel: 'portfolio',
  type: 'portfolio_update',
  data: PortfolioData
}
```

## Styling

The components use Tailwind CSS classes for styling. Custom theme colors can be configured through CSS variables:

```css
:root {
  --color-primary: #3b82f6;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
}
```

## Testing

Run tests with:

```bash
npm test -- StrategyWidgets.test.tsx
```

## Accessibility

All components follow WCAG 2.1 AA guidelines:

- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- High contrast mode compatibility
- Screen reader friendly

## Performance

- Uses React.memo for component memoization
- Implements virtual scrolling for large datasets
- Debounces WebSocket messages
- Implements proper cleanup in useEffect hooks

## Example Dashboard

See `src/pages/StrategyPerformanceDashboard.tsx` for a complete example of how to use all widgets together in a unified dashboard.

## Contributing

When adding new features:

1. Follow the existing code style
2. Add TypeScript types
3. Write tests for new functionality
4. Update documentation
5. Ensure accessibility compliance

## Troubleshooting

### Common Issues

1. **WebSocket Connection Issues**
   - Check WebSocket endpoint configuration
   - Verify authentication
   - Check network connectivity

2. **Component Not Rendering**
   - Ensure all dependencies are installed
   - Check TypeScript types
   - Verify prop types

3. **Performance Issues**
   - Check for unnecessary re-renders
   - Verify memoization implementation
   - Monitor WebSocket message frequency

### Debug Mode

Enable debug mode by setting environment variable:

```bash
REACT_APP_DEBUG_WEBSOCKET=true
```

This will log all WebSocket messages to the console.