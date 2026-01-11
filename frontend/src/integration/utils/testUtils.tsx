import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { ReactElement, ReactNode } from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from '../../store';

// Custom render function that includes providers
interface AllTheProvidersProps {
  children: ReactNode;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ConfigProvider>
            {children}
          </ConfigProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </Provider>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
): RenderResult => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

// Re-export everything from testing-library
export * from '@testing-library/react';
export * from '@testing-library/user-event';
export { customRender as render };

// Helper functions for integration tests
export const integrationUtils = {
  // Login helper
  login: async (user?: { email?: string; password?: string }) => {
    const credentials = user || { email: 'test@example.com', password: 'password' };
    
    // Mock login by updating Redux store
    store.dispatch({
      type: 'auth/loginSuccess',
      payload: {
        user: {
          id: 'test-user-1',
          email: credentials.email,
          username: 'testuser',
          role: 'user',
        },
        token: 'test-token',
      },
    });
  },

  // Logout helper
  logout: async () => {
    store.dispatch({
      type: 'auth/logout',
    });
  },

  // Create mock store state
  createMockState: (overrides: any = {}) => {
    return {
      auth: {
        isAuthenticated: true,
        user: {
          id: 'test-user-1',
          email: 'test@example.com',
          username: 'testuser',
          role: 'user',
        },
        token: 'test-token',
      },
      strategies: {
        list: [],
        loading: false,
        error: null,
      },
      portfolio: {
        data: null,
        loading: false,
        error: null,
      },
      ...overrides,
    };
  },

  // Wait for Redux state update
  waitForState: (condition: (state: any) => boolean, timeout: number = 5000): Promise<void> => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const checkState = () => {
        const state = store.getState();
        
        if (condition(state)) {
          resolve();
        } else if (Date.now() - startTime > timeout) {
          reject(new Error('State condition not met within timeout'));
        } else {
          setTimeout(checkState, 100);
        }
      };
      
      checkState();
    });
  },

  // Create mock WebSocket connection
  createMockWebSocket: () => {
    const mockWs = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      readyState: 1,
      CONNECTING: 0,
      OPEN: 1,
      CLOSING: 2,
      CLOSED: 3,
    };
    
    global.WebSocket = jest.fn(() => mockWs) as any;
    return mockWs;
  },

  // Mock API responses
  mockApiResponse: (endpoint: string, response: any) => {
    const originalFetch = global.fetch;
    
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(response),
        text: () => Promise.resolve(JSON.stringify(response)),
      })
    ) as jest.Mock;

    return () => {
      global.fetch = originalFetch;
    };
  },

  // Helper to test async operations
  testAsyncOperation: async (
    operation: () => Promise<any>,
    assertions: (result: any) => void
  ) => {
    try {
      const result = await operation();
      assertions(result);
    } catch (error) {
      throw error;
    }
  },
};

// Custom matcher for testing Redux state changes
expect.extend({
  toHaveState(received: any, path: string, expectedValue: any) {
    const keys = path.split('.');
    let currentValue = received;
    
    for (const key of keys) {
      currentValue = currentValue?.[key];
    }
    
    const pass = currentValue === expectedValue;
    
    return {
      message: () =>
        `expected ${path} to ${pass ? 'not ' : ''}be ${expectedValue}, but it was ${currentValue}`,
      pass,
    };
  },
});

// Extend Jest matchers type
declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveState(path: string, expectedValue: any): R;
    }
  }
}