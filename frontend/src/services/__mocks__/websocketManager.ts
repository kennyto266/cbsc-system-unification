/**
 * Mock for WebSocketManager
 */

// Create unsubscribe function factory
const createUnsubscribe = () => {
  const unsubscribeFn = () => {
    // No-op unsubscribe function
  };
  return unsubscribeFn;
};

export const wsManager = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  subscribe: jest.fn(() => createUnsubscribe()),
  unsubscribe: jest.fn(),
};

export class WebSocketManager {
  constructor(options?: any) {
    // Mock constructor
  }

  connect() {
    return Promise.resolve();
  }

  disconnect() {
    return Promise.resolve();
  }

  subscribe() {
    return createUnsubscribe();
  }

  unsubscribe() {
    // No-op
  }
}
