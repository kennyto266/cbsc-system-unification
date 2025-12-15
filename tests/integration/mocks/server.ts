// MSW Server setup for integration tests
import { setupServer } from 'msw/node'
import { rest } from 'msw'

// Common API responses
const mockStrategies = {
  success: true,
  data: {
    items: [
      {
        id: 1,
        name: 'Moving Average Strategy',
        description: 'Simple MA crossover strategy',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        parameters: {
          short_period: 10,
          long_period: 20
        }
      },
      {
        id: 2,
        name: 'RSI Strategy',
        description: 'RSI based trading strategy',
        status: 'inactive',
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        parameters: {
          rsi_period: 14,
          rsi_oversold: 30,
          rsi_overbought: 70
        }
      }
    ],
    total: 2,
    page: 1,
    per_page: 10
  },
  message: 'Strategies retrieved successfully'
}

const mockPerformance = {
  success: true,
  data: {
    strategy_id: 1,
    total_return: 15.5,
    sharpe_ratio: 1.85,
    max_drawdown: -8.2,
    win_rate: 0.65,
    profit_factor: 1.8,
    total_trades: 125,
    profitable_trades: 81,
    losing_trades: 44,
    average_win: 2.3,
    average_loss: -1.1,
    metrics: {
      daily_returns: [0.1, 0.2, -0.1, 0.3, 0.1],
      equity_curve: [1000, 1010, 1030, 1029, 1060, 1071],
      monthly_returns: {
        '2024-01': 5.5,
        '2024-02': 3.2,
        '2024-03': -1.1,
        '2024-04': 7.9
      }
    }
  },
  message: 'Performance data retrieved successfully'
}

// API handlers
export const handlers = [
  // Strategy endpoints
  rest.get('/api/strategies', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockStrategies))
  }),

  rest.post('/api/strategies', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        success: true,
        data: {
          id: 3,
          name: 'New Test Strategy',
          description: 'Created from integration test',
          status: 'draft',
          created_at: '2024-01-03T00:00:00Z',
          updated_at: '2024-01-03T00:00:00Z',
          parameters: {}
        },
        message: 'Strategy created successfully'
      })
    )
  }),

  rest.put('/api/strategies/:id', (req, res, ctx) => {
    const { id } = req.params
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          id: parseInt(id as string),
          name: 'Updated Strategy',
          description: 'Updated from integration test',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-04T00:00:00Z',
          parameters: {
            updated_param: 'test_value'
          }
        },
        message: 'Strategy updated successfully'
      })
    )
  }),

  rest.delete('/api/strategies/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: null,
        message: 'Strategy deleted successfully'
      })
    )
  }),

  rest.get('/api/strategies/:id/performance', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockPerformance))
  }),

  // Authentication endpoints
  rest.post('/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          access_token: 'mock-jwt-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: 1,
            username: 'test_user',
            email: 'test@example.com'
          }
        },
        message: 'Login successful'
      })
    )
  }),

  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: null,
        message: 'Logout successful'
      })
    )
  }),

  // Market data endpoints
  rest.get('/api/market/data/:symbol', (req, res, ctx) => {
    const { symbol } = req.params
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          symbol,
          price: 50000.0,
          volume: 1000000,
          change_24h: 2.5,
          timestamp: new Date().toISOString()
        }
      })
    )
  }),

  // WebSocket endpoint for real-time data
  rest.get('/api/ws/strategies', (req, res, ctx) => {
    return res(
      ctx.status(101),
      ctx.body('WebSocket connection established')
    )
  }),

  // Error handlers
  rest.get('/api/strategies/error', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Internal server error'
        }
      })
    )
  }),

  rest.get('/api/strategies/unauthorized', (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'Authentication required'
        }
      })
    )
  })
]

// Create server instance
export const server = setupServer(...handlers)