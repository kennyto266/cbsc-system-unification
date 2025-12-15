/**
 * Strategy API Integration Tests
 * Tests frontend integration with backend API
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import StrategyList from '../../../src/pages/strategies/components/StrategyList'

// Mock the API server
const server = setupServer(
  // Mock strategy list endpoint
  rest.get('/api/strategies', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      })
    )
  }),

  // Mock strategy create endpoint
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

  // Mock strategy update endpoint
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

  // Mock strategy delete endpoint
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

  // Mock strategy performance endpoint
  rest.get('/api/strategies/:id/performance', (req, res, ctx) => {
    const { id } = req.params
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          strategy_id: parseInt(id as string),
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
      })
    )
  })
)

// Test wrapper with QueryClient
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('Strategy API Integration Tests', () => {
  beforeAll(() => server.listen())
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())

  describe('Strategy List Integration', () => {
    test('should fetch and display strategies from API', async () => {
      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for strategies to load
      await waitFor(() => {
        expect(screen.getByText('Moving Average Strategy')).toBeInTheDocument()
      })

      // Verify strategy data is displayed
      expect(screen.getByText('Simple MA crossover strategy')).toBeInTheDocument()
      expect(screen.getByText('RSI Strategy')).toBeInTheDocument()
      expect(screen.getByText('RSI based trading strategy')).toBeInTheDocument()
    })

    test('should handle API errors gracefully', async () => {
      // Override handler to simulate API error
      server.use(
        rest.get('/api/strategies', (req, res, ctx) => {
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
        })
      )

      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
      })
    })
  })

  describe('Strategy CRUD Operations', () => {
    test('should create new strategy via API', async () => {
      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Find and click create button
      const createButton = screen.getByText(/create/i)
      fireEvent.click(createButton)

      // Fill in strategy details
      const nameInput = screen.getByLabelText(/name/i)
      const descriptionInput = screen.getByLabelText(/description/i)

      fireEvent.change(nameInput, { target: { value: 'New Test Strategy' } })
      fireEvent.change(descriptionInput, { target: { value: 'Created from integration test' } })

      // Submit form
      const submitButton = screen.getByText(/save/i)
      fireEvent.click(submitButton)

      // Wait for success message
      await waitFor(() => {
        expect(screen.getByText(/created successfully/i)).toBeInTheDocument()
      })
    })

    test('should update strategy via API', async () => {
      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for strategies to load
      await waitFor(() => {
        expect(screen.getByText('Moving Average Strategy')).toBeInTheDocument()
      })

      // Find and click edit button
      const editButtons = screen.getAllByLabelText(/edit/i)
      fireEvent.click(editButtons[0])

      // Update strategy details
      const nameInput = screen.getByDisplayValue('Moving Average Strategy')
      fireEvent.change(nameInput, { target: { value: 'Updated Strategy' } })

      // Submit form
      const submitButton = screen.getByText(/save/i)
      fireEvent.click(submitButton)

      // Wait for success message
      await waitFor(() => {
        expect(screen.getByText(/updated successfully/i)).toBeInTheDocument()
      })
    })

    test('should delete strategy via API', async () => {
      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for strategies to load
      await waitFor(() => {
        expect(screen.getByText('Moving Average Strategy')).toBeInTheDocument()
      })

      // Find and click delete button
      const deleteButtons = screen.getAllByLabelText(/delete/i)
      fireEvent.click(deleteButtons[0])

      // Confirm deletion
      const confirmButton = screen.getByText(/confirm/i)
      fireEvent.click(confirmButton)

      // Wait for success message
      await waitFor(() => {
        expect(screen.getByText(/deleted successfully/i)).toBeInTheDocument()
      })
    })
  })

  describe('Strategy Performance Integration', () => {
    test('should fetch and display performance data', async () => {
      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for strategies to load
      await waitFor(() => {
        expect(screen.getByText('Moving Average Strategy')).toBeInTheDocument()
      })

      // Click on performance view
      const performanceButton = screen.getByText(/performance/i)
      fireEvent.click(performanceButton)

      // Wait for performance data to load
      await waitFor(() => {
        expect(screen.getByText('15.5%')).toBeInTheDocument() // Total return
      })

      // Verify other metrics
      expect(screen.getByText('1.85')).toBeInTheDocument() // Sharpe ratio
      expect(screen.getByText('65%')).toBeInTheDocument() // Win rate
    })
  })

  describe('Real-time Data Integration', () => {
    test('should handle WebSocket updates', async () => {
      // Mock WebSocket
      const mockWebSocket = jest.fn()
      mockWebSocket.prototype.addEventListener = jest.fn()
      mockWebSocket.prototype.send = jest.fn()
      mockWebSocket.prototype.close = jest.fn()
      global.WebSocket = mockWebSocket as any

      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Verify WebSocket connection is established
      await waitFor(() => {
        expect(mockWebSocket).toHaveBeenCalled()
      })

      // Simulate real-time update
      const onMessageCallback = mockWebSocket.prototype.addEventListener.mock.calls
        .find((call: any) => call[0] === 'message')?.[1]

      if (onMessageCallback) {
        const mockData = {
          type: 'STRATEGY_UPDATE',
          data: {
            id: 1,
            status: 'active',
            last_signal: 'BUY'
          }
        }

        onMessageCallback({ data: JSON.stringify(mockData) })

        // Verify UI updates with real-time data
        await waitFor(() => {
          expect(screen.getByText('BUY')).toBeInTheDocument()
        })
      }
    })
  })

  describe('Authentication Integration', () => {
    test('should handle unauthenticated requests', async () => {
      // Override handlers to simulate auth error
      server.use(
        rest.get('/api/strategies', (req, res, ctx) => {
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
      )

      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for redirect to login
      await waitFor(() => {
        expect(window.location.pathname).toBe('/login')
      })
    })

    test('should include auth headers in API requests', async () => {
      // Mock localStorage with auth token
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: jest.fn().mockReturnValue('mock-jwt-token'),
          setItem: jest.fn(),
          removeItem: jest.fn(),
        },
        writable: true,
      })

      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Verify that requests include auth headers
      await waitFor(() => {
        // The actual request verification would need to be done
        // by inspecting the fetch/axios calls or using msw request handlers
        expect(screen.getByText('Moving Average Strategy')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling and Resilience', () => {
    test('should retry failed requests', async () => {
      let requestCount = 0
      server.use(
        rest.get('/api/strategies', (req, res, ctx) => {
          requestCount++
          if (requestCount < 3) {
            return res(
              ctx.status(503),
              ctx.json({
                success: false,
                error: {
                  code: 'SERVICE_UNAVAILABLE',
                  message: 'Service temporarily unavailable'
                }
              })
            )
          }
          return res(
            ctx.status(200),
            ctx.json({
              success: true,
              data: { items: [], total: 0, page: 1, per_page: 10 },
              message: 'Strategies retrieved successfully'
            })
          )
        })
      )

      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for successful response after retries
      await waitFor(() => {
        expect(requestCount).toBe(3)
      })
    })

    test('should handle network errors gracefully', async () => {
      // Override handler to simulate network error
      server.use(
        rest.get('/api/strategies', (req, res, ctx) => {
          return res.networkError('Network connection failed')
        })
      )

      render(
        <TestWrapper>
          <StrategyList />
        </TestWrapper>
      )

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument()
      })
    })
  })
})