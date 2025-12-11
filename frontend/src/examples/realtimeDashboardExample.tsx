import React, { useEffect, useState } from 'react';
import { StrategyDashboardWithRealtime } from '../components/StrategyDashboard/StrategyDashboardWithRealtime';
import { getRealtimeManager } from '../services/realtimeManager';
import { Strategy, PerformanceMetrics } from '../types/index';

// Example component showing how to use real-time features
export const RealtimeDashboardExample: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const realtimeManager = getRealtimeManager();

  useEffect(() => {
    // Set up custom event listeners
    const handleStrategyUpdate = (strategies: Strategy[]) => {
      console.log('Strategies updated:', strategies);
      // Custom logic for strategy updates
    };

    const handlePerformanceUpdate = (performance: PerformanceMetrics[]) => {
      console.log('Performance updated:', performance);
      // Custom logic for performance updates
      // Could trigger alerts, notifications, etc.
    };

    const handleError = (error: Error, context: string) => {
      console.error(`Error in ${context}:`, error);
      // Custom error handling
      // Could show toast notifications, error modals, etc.
    };

    const handleNetworkChange = (status: any) => {
      console.log('Network status changed:', status);
      // Update UI based on network status
    };

    // Initialize real-time manager with custom callbacks
    realtimeManager.initialize({
      onStrategyUpdate: handleStrategyUpdate,
      onPerformanceUpdate: handlePerformanceUpdate,
      onError: handleError,
      onNetworkChange: handleNetworkChange,
      onSyncStart: () => console.log('Data sync started'),
      onSyncComplete: (duration) => console.log(`Sync completed in ${duration}ms`)
    }).then(() => {
      console.log('Real-time manager initialized');
    }).catch(error => {
      console.error('Failed to initialize real-time manager:', error);
    });

    // Update stats every second
    const interval = setInterval(() => {
      setStats(realtimeManager.getStats());
    }, 1000);

    return () => {
      clearInterval(interval);
      realtimeManager.destroy();
    };
  }, [realtimeManager]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Dashboard with real-time features */}
      <StrategyDashboardWithRealtime
        apiUrl="/api"
        wsUrl="ws://localhost:3003/ws"
        refreshInterval={10000} // 10 seconds
        enableRealtime={true}
      />

      {/* Debug Panel - Show in development only */}
      {process.env.NODE_ENV === 'development' && stats && (
        <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 text-xs">
          <h3 className="font-semibold mb-2">Real-time Stats</h3>
          <div className="space-y-1">
            <div>Active: {stats.isActive ? 'Yes' : 'No'}</div>
            <div>Paused: {stats.isPaused ? 'Yes' : 'No'}</div>
            <div>Updates: {stats.updateCount}</div>
            <div>Errors: {stats.errorCount}</div>
            <div>Online: {stats.networkStatus.isOnline ? 'Yes' : 'No'}</div>
            <div>Connection: {stats.networkStatus.connectionType}</div>
            {stats.lastSyncTime && (
              <div>Last Sync: {stats.lastSyncTime.toLocaleTimeString()}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Example of using real-time manager directly
export const DirectRealtimeExample: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [performance, setPerformance] = useState<PerformanceMetrics[]>([]);
  const realtimeManager = getRealtimeManager();

  useEffect(() => {
    // Initialize with callbacks
    realtimeManager.initialize({
      onStrategyUpdate: (updatedStrategies) => {
        setStrategies(updatedStrategies);
      },
      onPerformanceUpdate: (updatedPerformance) => {
        setPerformance(updatedPerformance);
      },
      onError: (error, context) => {
        console.error(`Real-time error in ${context}:`, error);
      }
    });

    // Start real-time updates
    realtimeManager.start();

    return () => {
      realtimeManager.destroy();
    };
  }, [realtimeManager]);

  const handleManualRefresh = async () => {
    try {
      await realtimeManager.triggerManualRefresh();
      console.log('Manual refresh triggered');
    } catch (error) {
      console.error('Manual refresh failed:', error);
    }
  };

  const handlePauseResume = () => {
    const stats = realtimeManager.getStats();
    if (stats.isPaused) {
      realtimeManager.resume();
    } else {
      realtimeManager.pause();
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Direct Real-time Manager Example</h1>

      {/* Control Panel */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Controls</h2>
        <div className="space-x-4">
          <button
            onClick={handleManualRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Manual Refresh
          </button>
          <button
            onClick={handlePauseResume}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Pause/Resume
          </button>
        </div>
      </div>

      {/* Data Display */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strategies */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Strategies ({strategies.length})</h2>
          <div className="space-y-2">
            {strategies.map(strategy => (
              <div key={strategy.id} className="border-b pb-2">
                <div className="font-medium">{strategy.name}</div>
                <div className="text-sm text-gray-600">
                  Status: {strategy.status} | Category: {strategy.category}
                </div>
                {strategy.performance && (
                  <div className="text-sm text-gray-600">
                    Sharpe: {strategy.performance.sharpeRatio?.toFixed(2)} |
                    Return: {(strategy.performance.totalReturn * 100).toFixed(2)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Performance ({performance.length})</h2>
          <div className="space-y-2">
            {performance.map(perf => (
              <div key={perf.strategyId} className="border-b pb-2">
                <div className="font-medium">Strategy: {perf.strategyId}</div>
                <div className="text-sm text-gray-600">
                  Total Return: {(perf.totalReturn * 100).toFixed(2)}%<br/>
                  Sharpe Ratio: {perf.sharpeRatio?.toFixed(2)}<br/>
                  Max Drawdown: {(perf.maxDrawdown * 100).toFixed(2)}%<br/>
                  Win Rate: {(perf.winRate * 100).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Example with custom real-time manager configuration
export const CustomConfigExample: React.FC = () => {
  const [customManager] = useState(() => {
    // Create real-time manager with custom configuration
    return getRealtimeManager({
      updateInterval: 5000, // 5 seconds
      maxRetries: 5,
      retryDelay: 1000,
      enableWebSocket: true,
      enablePeriodicRefresh: true
    });
  });

  useEffect(() => {
    const initManager = async () => {
      try {
        await customManager.initialize({
          onStrategyUpdate: (strategies) => {
            console.log('Custom config - Strategies updated:', strategies);
          },
          onError: (error, context) => {
            console.error('Custom config - Error:', error, context);

            // Custom error handling
            if (context === 'websocket') {
              // Handle WebSocket errors
              console.log('WebSocket error, attempting recovery...');
            } else if (context === 'data_sync') {
              // Handle data sync errors
              console.log('Data sync error, showing fallback data...');
            }
          }
        });

        customManager.start();

      } catch (error) {
        console.error('Failed to initialize custom manager:', error);
      }
    };

    initManager();

    return () => {
      customManager.destroy();
    };
  }, [customManager]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Custom Configuration Example</h1>
      <p className="text-gray-600">
        This example uses a custom real-time manager configuration with:
      </p>
      <ul className="list-disc list-inside mt-2 space-y-1 text-gray-600">
        <li>5-second update interval (instead of default 10 seconds)</li>
        <li>5 retry attempts (instead of default 3)</li>
        <li>Custom error handling logic</li>
      </ul>

      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">
          Check the browser console to see real-time update logs with custom configuration.
        </p>
      </div>
    </div>
  );
};

export default RealtimeDashboardExample;