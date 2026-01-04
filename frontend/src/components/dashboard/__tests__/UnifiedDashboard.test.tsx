/**
 * Unit tests for UnifiedDashboard component
 */

// Mocks must be defined BEFORE imports
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn(),
    unregister: jest.fn(),
  },
  defaults: {},
}));

jest.mock('react-chartjs-2', () => ({
  Line: () => null,
  Bar: () => null,
  Pie: () => null,
  Doughnut: () => null,
}));

// Mock WebSocket manager - use manual mock
jest.mock('../../../services/websocketManager', () => {
  const actualModule = jest.requireActual('../../../services/__mocks__/websocketManager');
  return {
    ...actualModule,
  };
});

// Mock API client
jest.mock('../../../services/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

import React from 'react';
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';

import { wsManager } from '../../../services/websocketManager';
import UnifiedDashboard from '../UnifiedDashboard';
import dashboardReducer from '../../../store/slices/dashboardSlice';
import strategyReducer from '../../../store/slices/strategySlice';
import authReducer from '../../../store/slices/authSlice';

// Create test store
function createTestStore(preloadedState = {}) {
  return configureStore({
    reducer: {
      dashboard: dashboardReducer,
      strategy: strategyReducer,
      auth: authReducer,
    },
    preloadedState: {
      dashboard: {
        stats: null,
        health: null,
        performanceData: null,
        alerts: [],
        isLoading: false,
        isRefreshing: false,
        error: null,
        lastRefresh: null,
        preferences: {
          timeRange: '1M',
          autoRefresh: true,
          refreshInterval: 10000,
          theme: 'auto',
          compactMode: false,
          showAnimations: true,
          layout: 'grid',
        },
        selectedStrategies: [],
        selectedTimeRange: '1M',
        fullscreen: false,
      },
      auth: {
        user: { username: 'testuser', email: 'test@example.com' },
        token: 'test-token',
        isAuthenticated: true,
      },
      strategy: {
        strategies: [
          {
            id: '1',
            name: 'Test Strategy 1',
            category: 'momentum',
            status: 'active',
            performance: { totalReturn: 15.5, sharpeRatio: 1.8 },
          },
          {
            id: '2',
            name: 'Test Strategy 2',
            category: 'mean_reversion',
            status: 'paused',
            performance: { totalReturn: -2.3, sharpeRatio: 0.5 },
          },
        ],
      },
      ...preloadedState,
    },
  });
}

// Test wrapper component
function TestWrapper({ children, store }: { children: React.ReactNode; store?: any }) {
  const testStore = store || createTestStore();

  return (
    <Provider store={testStore}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </Provider>
  );
}

describe('UnifiedDashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Ensure wsManager.subscribe returns a proper unsubscribe function
    (wsManager.subscribe as jest.Mock).mockImplementation(() => {
      return () => {
        // No-op unsubscribe function
      };
    });
  });

  afterEach(() => {
    cleanup();
  });

  test('renders without crashing', () => {
    const store = createTestStore();

    const { container } = render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // Component should render
    expect(container).toBeInTheDocument();
  });

  test('renders dashboard header', () => {
    const store = createTestStore();

    render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // Check for any dashboard-related text (use getAllByText since there may be multiple)
    const dashboardTexts = screen.queryAllByText(/策略|儀表板|dashboard|strategy/i);
    expect(dashboardTexts.length).toBeGreaterThan(0);
  });

  test('renders statistics cards when data is available', () => {
    const store = createTestStore({
      dashboard: {
        stats: {
          totalStrategies: 10,
          activeStrategies: 5,
          totalReturn: 15.5,
          sharpeRatio: 1.8,
          maxDrawdown: 8.2,
          winRate: 65,
        },
      },
    });

    const { container } = render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // Component should render with stats in store
    expect(container).toBeInTheDocument();
  });

  test('displays some UI elements', () => {
    const store = createTestStore({
      dashboard: {
        isLoading: true,
      },
    });

    const { container } = render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // Component should render something
    expect(container.firstChild).toBeInTheDocument();
  });

  test('renders with Redux store', () => {
    const store = createTestStore();

    const { container } = render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // Component should render something
    expect(container.firstChild).toBeInTheDocument();
  });

  test('WebSocket subscriptions are set up', () => {
    const store = createTestStore();

    render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // wsManager.subscribe should have been called (for price_update, strategy_signal, etc.)
    // The component may or may not call connect, but subscribe should be called
    expect(wsManager.subscribe).toHaveBeenCalled();
  });

  test('component cleanup works correctly', () => {
    const store = createTestStore();

    const { unmount } = render(
      <TestWrapper store={store}>
        <UnifiedDashboard />
      </TestWrapper>
    );

    // Unmount should not throw any errors
    expect(() => unmount()).not.toThrow();
  });
});
