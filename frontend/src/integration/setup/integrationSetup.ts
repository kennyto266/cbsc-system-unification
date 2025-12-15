import '@testing-library/jest-dom';
import { server } from './mocks/server';

// Start MSW server for all integration tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn',
  });
});

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
});

// Close server after all tests
afterAll(() => {
  server.close();
});

// Global test utilities
global.integration = {
  // Helper to wait for async operations
  waitFor: (ms: number = 100) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Helper to create test data
  createTestData: {
    strategy: (overrides = {}) => ({
      id: 'test-strategy-1',
      name: 'Test Strategy',
      description: 'Test strategy description',
      status: 'active',
      parameters: {
        symbols: ['AAPL', 'GOOGL'],
        timeframe: '1d',
        risk_level: 0.02,
      },
      performance: {
        total_return: 0.15,
        sharpe_ratio: 1.5,
        max_drawdown: -0.08,
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      ...overrides,
    }),
    
    user: (overrides = {}) => ({
      id: 'test-user-1',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      ...overrides,
    }),
    
    portfolio: (overrides = {}) => ({
      id: 'test-portfolio-1',
      name: 'Test Portfolio',
      user_id: 'test-user-1',
      total_value: 100000,
      positions: [
        {
          symbol: 'AAPL',
          quantity: 100,
          avg_cost: 150.0,
          current_price: 155.0,
          unrealized_pnl: 500,
        },
      ],
      ...overrides,
    }),
  },
};

// Mock WebSocket for integration tests
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1, // OPEN
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
})) as any;

// Mock IntersectionObserver for components that use it
global.IntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock ResizeObserver for responsive components
global.ResizeObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Suppress console warnings in tests (unless debugging)
const originalWarn = console.warn;
const originalError = console.error;

beforeAll(() => {
  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('When testing, code that causes React state updates')
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };

  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render is deprecated') ||
        args[0].includes('Warning: An invalid form control'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.warn = originalWarn;
  console.error = originalError;
});

// Set up global test timeouts
jest.setTimeout(30000);