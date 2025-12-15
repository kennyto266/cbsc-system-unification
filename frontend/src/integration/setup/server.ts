import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { integration } from './integrationSetup';

// Base URL for API
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:3004';

// Mock handlers for API endpoints
export const handlers = [
  // Auth endpoints
  rest.post(`${API_BASE}/auth/login`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          user: integration.createTestData.user(),
        },
      })
    );
  }),

  rest.post(`${API_BASE}/auth/logout`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: 'Logged out successfully',
      })
    );
  }),

  rest.post(`${API_BASE}/auth/refresh`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          access_token: 'new-test-access-token',
        },
      })
    );
  }),

  // Strategy endpoints
  rest.get(`${API_BASE}/strategies`, (req, res, ctx) => {
    const page = Number(req.url.searchParams.get('page')) || 1;
    const limit = Number(req.url.searchParams.get('limit')) || 10;
    
    const strategies = Array.from({ length: limit }, (_, i) =>
      integration.createTestData.strategy({
        id: `strategy-${page}-${i + 1}`,
        name: `Strategy ${page}-${i + 1}`,
      })
    );

    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          strategies,
          pagination: {
            page,
            limit,
            total: 100,
            pages: 10,
          },
        },
      })
    );
  }),

  rest.get(`${API_BASE}/strategies/:id`, (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: integration.createTestData.strategy({ id }),
      })
    );
  }),

  rest.post(`${API_BASE}/strategies`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        success: true,
        data: integration.createTestData.strategy({
          id: 'new-strategy-id',
        }),
      })
    );
  }),

  rest.put(`${API_BASE}/strategies/:id`, (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: integration.createTestData.strategy({ id }),
      })
    );
  }),

  rest.delete(`${API_BASE}/strategies/:id`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: 'Strategy deleted successfully',
      })
    );
  }),

  // Portfolio endpoints
  rest.get(`${API_BASE}/portfolio`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: integration.createTestData.portfolio(),
      })
    );
  }),

  rest.get(`${API_BASE}/portfolio/performance`, (req, res, ctx) => {
    const days = Number(req.url.searchParams.get('days')) || 30;
    
    const performance = Array.from({ length: days }, (_, i) => ({
      date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toISOString(),
      value: 100000 + Math.random() * 20000 - 10000,
      return: (Math.random() - 0.5) * 0.02,
    }));

    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: performance,
      })
    );
  }),

  // Market data endpoints
  rest.get(`${API_BASE}/market/symbols`, (req, res, ctx) => {
    const symbols = [
      { symbol: 'AAPL', name: 'Apple Inc.', price: 155.0, change: 0.5 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2800.0, change: -0.3 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', price: 380.0, change: 0.8 },
    ];

    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: symbols,
      })
    );
  }),

  rest.get(`${API_BASE}/market/quote/:symbol`, (req, res, ctx) => {
    const { symbol } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          symbol,
          price: 100 + Math.random() * 100,
          change: (Math.random() - 0.5) * 2,
          volume: Math.floor(Math.random() * 1000000),
          timestamp: new Date().toISOString(),
        },
      })
    );
  }),

  // Backtest endpoints
  rest.post(`${API_BASE}/backtest`, (req, res, ctx) => {
    const backtestId = `bt-${Date.now()}`;
    
    return res(
      ctx.status(202),
      ctx.json({
        success: true,
        data: {
          backtest_id: backtestId,
          status: 'pending',
        },
      })
    );
  }),

  rest.get(`${API_BASE}/backtest/:id`, (req, res, ctx) => {
    const { id } = req.params;
    
    // Simulate backtest completion after a delay
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          backtest_id: id,
          status: 'completed',
          results: {
            total_return: 0.15,
            sharpe_ratio: 1.5,
            max_drawdown: -0.08,
            win_rate: 0.55,
            trades: [
              {
                symbol: 'AAPL',
                type: 'long',
                entry_price: 150.0,
                exit_price: 155.0,
                quantity: 100,
                pnl: 500,
                timestamp: '2024-01-01T10:00:00Z',
              },
            ],
          },
        },
      })
    );
  }),

  // WebSocket endpoint for real-time data
  rest.get(`${API_BASE}/ws`, (req, res, ctx) => {
    return res(
      ctx.set('Connection', 'upgrade'),
      ctx.set('Upgrade', 'websocket'),
      ctx.status(101)
    );
  }),
];

// Create MSW server
export const server = setupServer(...handlers);