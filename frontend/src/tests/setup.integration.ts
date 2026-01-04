// CBSC Trading System - Integration Test Setup
// Configuration for integration tests

import '@testing-library/jest-dom';

// Setup MSW (Mock Service Worker) for API mocking
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

// Create MSW server
export const server = setupServer(...handlers);

// Setup and teardown
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

// Integration test timeout
jest.setTimeout(30000);
