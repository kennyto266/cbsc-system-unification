import React, { createContext, useContext, useRef, useEffect, useState } from 'react';

// Chart context type
interface ChartContextType {
  charts: Map<string, any>;
  updateInterval: number;
  isRealTimeEnabled: boolean;
  registerChart: (name: string, chartInstance: any) => void;
  unregisterChart: (name: string) => void;
  updateChart: (name: string, data: any) => void;
  updateAllCharts: (data: Record<string, any>) => void;
  resizeCharts: () => void;
  destroyAllCharts: () => void;
  enableRealTimeUpdates: (enabled: boolean) => void;
  setUpdateInterval: (interval: number) => void;
}

// Create chart context
const ChartContext = createContext<ChartContextType | undefined>(undefined);

// Chart Manager Provider Component
export const ChartManagerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const chartsRef = useRef<Map<string, any>>(new Map());
  const [updateInterval, setUpdateIntervalState] = useState(10000); // 10 seconds default
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Register a chart instance
  const registerChart = (name: string, chartInstance: any) => {
    chartsRef.current.set(name, {
      instance: chartInstance,
      lastUpdate: new Date(),
      updateCount: 0
    });
    console.log(`Chart registered: ${name}`);
  };

  // Unregister a chart instance
  const unregisterChart = (name: string) => {
    const chart = chartsRef.current.get(name);
    if (chart?.instance && typeof chart.instance.destroy === 'function') {
      chart.instance.destroy();
    }
    chartsRef.current.delete(name);
    console.log(`Chart unregistered: ${name}`);
  };

  // Update a specific chart
  const updateChart = (name: string, data: any) => {
    const chart = chartsRef.current.get(name);
    if (chart?.instance) {
      try {
        if (typeof chart.instance.data === 'function') {
          chart.instance.data(data);
        } else if (chart.instance.data !== undefined) {
          // For Chart.js instances
          Object.assign(chart.instance.data, data);
        }

        if (typeof chart.instance.update === 'function') {
          chart.instance.update('none'); // Update without animation
        }

        // Update chart metadata
        chart.lastUpdate = new Date();
        chart.updateCount++;

        console.log(`Chart updated: ${name} (Update #${chart.updateCount})`);
      } catch (error) {
        console.error(`Failed to update chart ${name}:`, error);
      }
    }
  };

  // Update all charts with provided data
  const updateAllCharts = (data: Record<string, any>) => {
    Object.entries(data).forEach(([chartName, chartData]) => {
      updateChart(chartName, chartData);
    });
  };

  // Resize all charts (useful for responsive design)
  const resizeCharts = () => {
    chartsRef.current.forEach((chart, name) => {
      if (chart?.instance && typeof chart.instance.resize === 'function') {
        chart.instance.resize();
        console.log(`Chart resized: ${name}`);
      }
    });
  };

  // Destroy all charts and clean up
  const destroyAllCharts = () => {
    chartsRef.current.forEach((chart, name) => {
      if (chart?.instance && typeof chart.instance.destroy === 'function') {
        chart.instance.destroy();
        console.log(`Chart destroyed: ${name}`);
      }
    });
    chartsRef.current.clear();

    // Clear real-time updates
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  // Enable or disable real-time updates
  const enableRealTimeUpdates = (enabled: boolean) => {
    setIsRealTimeEnabled(enabled);

    if (enabled) {
      // Start real-time updates
      intervalRef.current = setInterval(() => {
        // Trigger custom event for real-time updates
        window.dispatchEvent(new CustomEvent('chart-realtime-update', {
          detail: { timestamp: new Date() }
        }));
      }, updateInterval);
      console.log(`Real-time updates enabled (interval: ${updateInterval}ms)`);
    } else {
      // Stop real-time updates
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      console.log('Real-time updates disabled');
    }
  };

  // Set update interval
  const setUpdateInterval = (interval: number) => {
    setUpdateIntervalState(interval);

    // Restart real-time updates with new interval if enabled
    if (isRealTimeEnabled) {
      enableRealTimeUpdates(false);
      setTimeout(() => enableRealTimeUpdates(true), 100);
    }
  };

  // Handle window resize events
  useEffect(() => {
    const handleResize = () => {
      resizeCharts();
    };

    // Debounce resize events
    let timeoutId: NodeJS.Timeout;
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleResize, 250);
    };

    window.addEventListener('resize', debouncedResize);

    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(timeoutId);
      destroyAllCharts();
    };
  }, []);

  // Handle visibility change (pause updates when tab is not visible)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isRealTimeEnabled) {
        enableRealTimeUpdates(false);
      } else if (!document.hidden && isRealTimeEnabled) {
        enableRealTimeUpdates(true);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isRealTimeEnabled]);

  const contextValue: ChartContextType = {
    charts: chartsRef.current,
    updateInterval,
    isRealTimeEnabled,
    registerChart,
    unregisterChart,
    updateChart,
    updateAllCharts,
    resizeCharts,
    destroyAllCharts,
    enableRealTimeUpdates,
    setUpdateInterval
  };

  return (
    <ChartContext.Provider value={contextValue}>
      {children}
    </ChartContext.Provider>
  );
};

// Hook to use chart manager
export const useChartManager = () => {
  const context = useContext(ChartContext);
  if (context === undefined) {
    throw new Error('useChartManager must be used within a ChartManagerProvider');
  }
  return context;
};

// Hook to register and manage a single chart
export const useChartRegistration = (chartName: string, chartInstance: any) => {
  const { registerChart, unregisterChart, updateChart } = useChartManager();

  useEffect(() => {
    if (chartInstance && chartName) {
      registerChart(chartName, chartInstance);
    }

    return () => {
      if (chartName) {
        unregisterChart(chartName);
      }
    };
  }, [chartName, chartInstance, registerChart, unregisterChart]);

  return { updateChart };
};

// Real-time data hook for charts
export const useRealTimeChartUpdate = (
  chartName: string,
  dataFetcher: () => Promise<any>,
  enabled: boolean = false
) => {
  const { updateChart, isRealTimeEnabled } = useChartManager();

  useEffect(() => {
    const handleRealTimeUpdate = async () => {
      if (enabled && isRealTimeEnabled) {
        try {
          const data = await dataFetcher();
          if (data) {
            updateChart(chartName, data);
          }
        } catch (error) {
          console.error(`Failed to fetch real-time data for ${chartName}:`, error);
        }
      }
    };

    // Listen for real-time update events
    const listener = (event: CustomEvent) => {
      handleRealTimeUpdate();
    };

    window.addEventListener('chart-realtime-update', listener as EventListener);

    // Initial fetch
    handleRealTimeUpdate();

    return () => {
      window.removeEventListener('chart-realtime-update', listener as EventListener);
    };
  }, [chartName, dataFetcher, enabled, isRealTimeEnabled, updateChart]);
};

// Performance monitoring for charts
export const useChartPerformance = () => {
  const { charts } = useChartManager();
  const [performanceData, setPerformanceData] = useState<Record<string, any>>({});

  const getPerformanceStats = () => {
    const stats: Record<string, any> = {};

    charts.forEach((chart, name) => {
      stats[name] = {
        updateCount: chart.updateCount || 0,
        lastUpdate: chart.lastUpdate,
        hasInstance: !!chart.instance,
        instanceType: chart.instance?.constructor?.name || 'Unknown'
      };
    });

    return stats;
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setPerformanceData(getPerformanceStats());
    }, 5000); // Update performance data every 5 seconds

    return () => clearInterval(interval);
  }, [charts]);

  return {
    performanceData,
    getPerformanceStats,
    chartCount: charts.size
  };
};

export default ChartManagerProvider;