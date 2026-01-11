# Hooks Unit Tests

This directory contains comprehensive unit tests for the custom React hooks used in the CBSC Dashboard frontend application.

## Test Files

### Core Hooks

#### 1. useToast Hook (`useToast.test.tsx`)
Tests the toast notification system including:
- Toast creation and removal
- Auto-removal with custom durations
- Global state synchronization across hook instances
- Toast type handling (success, error, warning, info)
- Unique ID generation
- Clean up on component unmount

#### 2. useResponsive Hook (`useResponsive.test.ts`)
Tests responsive design utilities including:
- Breakpoint detection (xs, sm, md, lg, xl, 2xl)
- Device type detection (mobile, tablet, desktop)
- Orientation detection (portrait, landscape)
- Window resize handling
- Media query matching
- Touch device detection
- Server-side rendering fallbacks

#### 3. useWebSocketEnhanced Hook (`useWebSocketEnhanced.test.ts`)
Tests enhanced WebSocket functionality including:
- Connection state management
- Auto-connection and disconnection
- Message sending and receiving
- Channel subscriptions with filters
- Connection quality tracking
- Error handling and reconnection
- Event listener management
- Subscription cleanup on unmount

### Chart Hooks

#### 4. useChartResize Hook (`../chart/useChartResize.test.ts`)
Tests chart responsive behavior including:
- ResizeObserver integration
- Container size tracking
- Breakpoint-based responsive behavior
- Custom constraints (min/max width/height)
- Aspect ratio maintenance
- Padding application
- Manual resize triggering
- Debounced resize handling

#### 5. useChartExport Hook (`../chart/useChartExport.test.ts`)
Tests chart export functionality including:
- PNG/JPG export from various chart libraries
- SVG export support
- Data export to CSV and JSON formats
- Custom export functions
- Export history tracking
- Blob generation and download
- Scaling and quality options
- Background color customization

#### 6. useRealtimeChart Hook (`../chart/useRealtimeChart.test.ts`)
Tests real-time data visualization including:
- WebSocket integration for live data
- Data buffering and processing
- Deduplication and filtering
- Data rate calculation
- Pause/resume functionality
- Data windowing for time-based filtering
- Export capabilities
- Error handling and recovery

## Test Setup

### Common Mocks (`setup.jest.ts`)
The test setup includes comprehensive mocks for:
- Web APIs (ResizeObserver, IntersectionObserver, matchMedia)
- Canvas and SVG rendering
- WebSocket connections
- File download functionality
- Performance and animation APIs
- Image and media elements

### Utilities
Common test utilities provided:
- `createMockRef<T>()` - Creates a React ref mock
- `createMockElement()` - Creates DOM element mocks
- `createMockCanvas()` - Creates canvas element mocks
- `createMockSVG()` - Creates SVG element mocks
- `waitFor()` - Promise-based delay utility
- `flushPromises()` - Flushes pending promises

### Mock Data
Pre-defined mock data for testing:
- `mockChartData` - Sample chart data points
- `mockWebSocketMessage` - WebSocket message structure
- `mockToastData` - Toast notification data

## Running Tests

### Individual Test Files
```bash
# Run specific hook tests
npx jest src/hooks/__tests__/useToast.test.tsx
npx jest src/hooks/__tests__/useResponsive.test.ts
npx jest src/hooks/__tests__/useWebSocketEnhanced.test.ts
npx jest src/hooks/chart/useChartResize.test.ts
npx jest src/hooks/chart/useChartExport.test.ts
npx jest src/hooks/chart/useRealtimeChart.test.ts
```

### All Hook Tests
```bash
# Run all hook tests
npx jest src/hooks/
```

### With Coverage
```bash
# Run tests with coverage report
npm run test:coverage -- --testPathPattern=src/hooks/
```

## Test Best Practices

1. **Isolation**: Each test is completely isolated with proper cleanup
2. **Mocking**: External dependencies are mocked to ensure consistent testing
3. **Edge Cases**: Tests cover normal flow, edge cases, and error conditions
4. **User Interactions**: All user-facing interactions are tested
5. **State Changes**: State transitions are verified at each step
6. **Async Handling**: Proper handling of promises and async operations
7. **Cleanup**: Resources are properly cleaned up after each test

## TypeScript

All tests are written in TypeScript with proper type safety:
- Type-safe mocking with jest.Mocked types
- Proper typing for test utilities
- Interface compliance verification

## Coverage Goals

Target coverage for hooks:
- Statements: 90%+
- Branches: 85%+
- Functions: 95%+
- Lines: 90%+

## Future Enhancements

Potential areas for additional testing:
- Integration tests with actual components
- Performance testing with large datasets
- Accessibility testing
- Visual regression testing for chart rendering
- End-to-end testing scenarios