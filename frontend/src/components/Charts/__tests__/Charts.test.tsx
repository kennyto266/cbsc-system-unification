import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ChartsDashboard } from '../ChartsDashboard';
import { ChartManagerProvider } from '../ChartManager';
import { Strategy } from '../../../types';

// Import chart test setup

// Mock strategy data for testing
const mockStrategies: Strategy[] = [
  {
    id: 'test-strategy-1',
    name: '測試策略1',
    type: 'direct_rsi',
    category: 'core_cbsc',
    status: 'active',
    performance: {
      totalReturn: 0.25,
      sharpeRatio: 1.5,
      maxDrawdown: 8.5,
      volatility: 12.0,
      winRate: 0.65,
      profitFactor: 1.8,
      calmarRatio: 1.0,
      var95: -0.03,
      cvar95: -0.045,
      lastUpdated: new Date('2025-12-11T10:30:00Z'),
      dataQualityScore: 98
    },
    description: '測用策略描述'
  },
  {
    id: 'test-strategy-2',
    name: '測試策略2',
    type: 'sentiment_momentum',
    category: 'core_cbsc',
    status: 'active',
    performance: {
      totalReturn: 0.18,
      sharpeRatio: 1.1,
      maxDrawdown: 12.0,
      volatility: 15.5,
      winRate: 0.58,
      profitFactor: 1.5,
      calmarRatio: 0.75,
      var95: -0.04,
      cvar95: -0.055,
      lastUpdated: new Date('2025-12-11T10:25:00Z'),
      dataQualityScore: 95
    },
    description: '另一個測試策略'
  }
];

// Create a minimal mock store
const mockStore = configureStore({
  reducer: {
    // Add minimal reducers if needed
    auth: (state = { user: null, token: null }) => state,
  },
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Provider store={mockStore}>
    <ChartManagerProvider>
      {children}
    </ChartManagerProvider>
  </Provider>
);

describe('Charts Components', () => {
  beforeEach(() => {
    // Ensure matchMedia is properly mocked before each test
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });
  });

  it('renders ChartsDashboard with strategy data', () => {
    const { container } = render(
      <TestWrapper>
        <ChartsDashboard
          strategies={mockStrategies}
          height={400}
          showControls={false}
        />
      </TestWrapper>
    );

    // Should render without crashing
    expect(container).toBeInTheDocument();
  });

  it('displays empty state when no strategies provided', () => {
    render(
      <TestWrapper>
        <ChartsDashboard
          strategies={[]}
          showControls={false}
        />
      </TestWrapper>
    );

    // Should display empty state message
    expect(screen.getByText('沒有策略數據')).toBeInTheDocument();
    expect(screen.getByText('請先添加策略或檢查數據源連接')).toBeInTheDocument();
  });
});
