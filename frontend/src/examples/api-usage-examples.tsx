/**
 * API Usage Examples
 * Demonstrates how to use the CBSC API integration layer
 */

import React, { useEffect, useState } from 'react';
import {
  // Auth API
  useLoginMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
  useAuthState,

  // Strategy API
  useGetStrategiesQuery,
  useCreateStrategyMutation,
  useExecuteStrategyMutation,
  useStrategiesWithFilters,

  // Market Data API
  useMarketData,
  useGetMarketOverviewQuery,

  // Dashboard API
  useDashboardManagement,
  useCBSCDashboard,

  // WebSocket Integration
  useStrategyWebSocketIntegration,
  useMarketDataWebSocketIntegration,

  // Store hooks
  useAppDispatch,
  useAppSelector,
} from '../store';

// Example 1: Authentication
export const AuthExample: React.FC = () => {
  const [login] = useLoginMutation();
  const [logout] = useLogoutMutation();
  const { data: user, isLoading } = useGetCurrentUserQuery();
  const { isAuthenticated } = useAuthState();
  const dispatch = useAppDispatch();

  const handleLogin = async () => {
    try {
      await login({
        email: 'user@example.com',
        password: 'password',
      }).unwrap();
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await logout().unwrap();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div>
      <h2>Authentication Example</h2>
      {isLoading ? (
        <p>Loading...</p>
      ) : isAuthenticated ? (
        <div>
          <p>Welcome, {user?.name}!</p>
          <button onClick={handleLogout}>Logout</button>
        </div>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
    </div>
  );
};

// Example 2: Strategy Management
export const StrategyManagementExample: React.FC = () => {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);

  // Get strategies with filters
  const { strategies, isLoading, error } = useStrategiesWithFilters({
    status: 'active',
    category: 'trend_following',
    page: 1,
    pageSize: 10,
  });

  // Create strategy mutation
  const [createStrategy, { isLoading: isCreating }] = useCreateStrategyMutation();

  // Execute strategy mutation
  const [executeStrategy, { isLoading: isExecuting }] = useExecuteStrategyMutation();

  const handleCreateStrategy = async () => {
    try {
      await createStrategy({
        name: 'New Strategy',
        description: 'A sample trading strategy',
        category: 'momentum',
        riskLevel: 'medium',
        parameters: {
          rsiPeriod: 14,
          rsiThreshold: 70,
        },
      }).unwrap();
    } catch (error) {
      console.error('Failed to create strategy:', error);
    }
  };

  const handleExecuteStrategy = async (strategyId: string) => {
    try {
      await executeStrategy({
        id: strategyId,
        config: {
          startDate: '2023-01-01',
          endDate: '2023-12-31',
          initialCapital: 100000,
        },
      }).unwrap();
    } catch (error) {
      console.error('Failed to execute strategy:', error);
    }
  };

  return (
    <div>
      <h2>Strategy Management Example</h2>

      <button onClick={handleCreateStrategy} disabled={isCreating}>
        {isCreating ? 'Creating...' : 'Create Strategy'}
      </button>

      {isLoading ? (
        <p>Loading strategies...</p>
      ) : error ? (
        <p>Error: {error.toString()}</p>
      ) : (
        <div>
          <h3>Active Strategies</h3>
          <ul>
            {strategies.map((strategy) => (
              <li key={strategy.id}>
                <span>{strategy.name}</span>
                <button
                  onClick={() => handleExecuteStrategy(strategy.id)}
                  disabled={isExecuting}
                >
                  {isExecuting ? 'Executing...' : 'Execute'}
                </button>
                <button onClick={() => setSelectedStrategy(strategy.id)}>
                  View Details
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Example 3: Market Data with WebSocket
export const MarketDataExample: React.FC = () => {
  const symbols = ['AAPL', 'GOOGL', 'MSFT'];

  // Get static market data
  const { data: overview, isLoading: overviewLoading } = useGetMarketOverviewQuery();

  // Real-time market data
  const {
    marketData,
    isConnected,
    subscribeSymbol,
    unsubscribeSymbol,
  } = useMarketDataWebSocketIntegration(symbols, ['price', 'volume']);

  return (
    <div>
      <h2>Market Data Example</h2>

      <div>
        <h3>Connection Status</h3>
        <p>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</p>
      </div>

      {overviewLoading ? (
        <p>Loading market overview...</p>
      ) : (
        <div>
          <h3>Market Overview</h3>
          <pre>{JSON.stringify(overview, null, 2)}</pre>
        </div>
      )}

      <div>
        <h3>Real-time Prices</h3>
        {symbols.map((symbol) => {
          const data = marketData.get(symbol);
          return (
            <div key={symbol}>
              <strong>{symbol}:</strong> ${data?.price || 'N/A'}
              <small>Last update: {data?.lastUpdate || 'N/A'}</small>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Example 4: Strategy Dashboard with Real-time Updates
export const StrategyDashboardExample: React.FC = () => {
  const strategyId = 'strategy-123';

  // Real-time strategy updates
  const {
    executionUpdates,
    signals,
    performance,
    isConnected,
  } = useStrategyWebSocketIntegration(strategyId);

  return (
    <div>
      <h2>Strategy Dashboard Example</h2>

      <div>
        <h3>Connection</h3>
        <p>{isConnected ? 'Real-time updates active' : 'Disconnected'}</p>
      </div>

      <div>
        <h3>Performance</h3>
        {performance ? (
          <div>
            <p>Total Return: {performance.totalReturn}%</p>
            <p>Sharpe Ratio: {performance.sharpeRatio}</p>
            <p>Max Drawdown: {performance.maxDrawdown}%</p>
          </div>
        ) : (
          <p>No performance data</p>
        )}
      </div>

      <div>
        <h3>Recent Signals</h3>
        <ul>
          {signals.slice(0, 5).map((signal, index) => (
            <li key={index}>
              {signal.type}: {signal.symbol} at {signal.price}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3>Execution Updates</h3>
        <ul>
          {executionUpdates.slice(0, 5).map((update, index) => (
            <li key={index}>
              {update.status}: {update.message}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Example 5: CBSC Dashboard Integration
export const CBSCDashboardExample: React.FC = () => {
  const {
    config,
    widgets,
    layout,
    isLoading,
  } = useDashboardManagement();

  const {
    tokenStatus,
    systemStatus,
    strategies,
    alerts,
    hasValidToken,
  } = useCBSCDashboard();

  const dispatch = useAppDispatch();

  const handleQuickAction = async (actionId: string) => {
    try {
      // Dispatch quick action
      dispatch({
        type: 'dashboard/executeQuickAction',
        payload: { actionId },
      });
    } catch (error) {
      console.error('Quick action failed:', error);
    }
  };

  if (isLoading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div>
      <h2>CBSC Dashboard Example</h2>

      {/* Token Status */}
      <div>
        <h3>Token Status</h3>
        <p>{hasValidToken ? 'Valid' : 'Invalid or Expired'}</p>
      </div>

      {/* System Status */}
      <div>
        <h3>System Status</h3>
        <pre>{JSON.stringify(systemStatus, null, 2)}</pre>
      </div>

      {/* Active Strategies */}
      <div>
        <h3>Active Strategies ({strategies.length})</h3>
        <ul>
          {strategies.slice(0, 5).map((strategy) => (
            <li key={strategy.id}>
              {strategy.name} - {strategy.status}
            </li>
          ))}
        </ul>
      </div>

      {/* Recent Alerts */}
      <div>
        <h3>Recent Alerts</h3>
        <ul>
          {alerts.slice(0, 5).map((alert) => (
            <li key={alert.id}>
              [{alert.severity}] {alert.message}
            </li>
          ))}
        </ul>
      </div>

      {/* Quick Actions */}
      <div>
        <h3>Quick Actions</h3>
        <button onClick={() => handleQuickAction('refresh-data')}>
          Refresh Data
        </button>
        <button onClick={() => handleQuickAction('emergency-stop')}>
          Emergency Stop
        </button>
      </div>
    </div>
  );
};

// Example 6: Error Handling
export const ErrorHandlingExample: React.FC = () => {
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, error: apiError } = useGetStrategiesQuery({
    // Invalid parameters to trigger error
    status: 'invalid-status',
  });

  useEffect(() => {
    if (apiError) {
      // Handle API error
      if (apiError.status === 400) {
        setError('Invalid request parameters');
      } else if (apiError.status === 401) {
        setError('Please log in to view strategies');
      } else {
        setError('Failed to load strategies');
      }
    }
  }, [apiError]);

  return (
    <div>
      <h2>Error Handling Example</h2>

      {error && (
        <div style={{ color: 'red' }}>
          <h3>Error:</h3>
          <p>{error}</p>
          <button onClick={() => setError(null)}>Clear Error</button>
        </div>
      )}

      {isLoading && <p>Loading...</p>}

      {data && (
        <div>
          <h3>Strategies loaded successfully!</h3>
          <p>Found {data.total} strategies</p>
        </div>
      )}
    </div>
  );
};

// Main example container
export const APIExamples: React.FC = () => {
  const [activeExample, setActiveExample] = useState<string>('auth');

  const examples = {
    auth: { component: AuthExample, title: 'Authentication' },
    strategy: { component: StrategyManagementExample, title: 'Strategy Management' },
    market: { component: MarketDataExample, title: 'Market Data' },
    dashboard: { component: StrategyDashboardExample, title: 'Strategy Dashboard' },
    cbsc: { component: CBSCDashboardExample, title: 'CBSC Dashboard' },
    error: { component: ErrorHandlingExample, title: 'Error Handling' },
  };

  const ActiveComponent = examples[activeExample as keyof typeof examples]?.component;

  return (
    <div>
      <h1>CBSC API Integration Examples</h1>

      <nav>
        {Object.entries(examples).map(([key, { title }]) => (
          <button
            key={key}
            onClick={() => setActiveExample(key)}
            style={{
              marginRight: '10px',
              fontWeight: activeExample === key ? 'bold' : 'normal',
            }}
          >
            {title}
          </button>
        ))}
      </nav>

      <hr />

      {ActiveComponent && <ActiveComponent />}
    </div>
  );
};