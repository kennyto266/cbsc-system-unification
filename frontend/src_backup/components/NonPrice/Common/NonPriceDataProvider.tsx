import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { message } from 'antd';

// Non-price signal types
export interface NonPriceSignal {
  id: string;
  type: 'macro' | 'sentiment' | 'alternative';
  source: string;
  symbol?: string;
  timestamp: Date;
  value: number;
  confidence: number;
  metadata: Record<string, any>;
}

export interface MacroIndicator {
  symbol: string;
  name: string;
  value: number;
  change: number;
  changePercent: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
  timestamp: Date;
  historical: Array<{
    timestamp: Date;
    value: number;
  }>;
}

export interface SentimentData {
  symbol: string;
  sentiment: number; // -1 to 1
  confidence: number; // 0 to 1
  emotions: {
    fear: number;
    greed: number;
    neutral: number;
  };
  sources: {
    social: number;
    news: number;
    technical: number;
  };
  timestamp: Date;
}

export interface StrategyPerformance {
  name: string;
  type: 'price' | 'non-price' | 'combined';
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  volatility: number;
  alpha: number;
  beta: number;
  period: string;
}

// API Service class
class NonPriceService {
  private wsConnections: Map<string, WebSocket> = new Map();
  private subscribers: Map<string, Set<(signal: NonPriceSignal) => void>> = new Map();

  // Mock API calls - will be replaced with actual API
  async getMacroIndicators(indicatorType: string, symbol?: string): Promise<MacroIndicator> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const mockData: Record<string, MacroIndicator> = {
      hibor: {
        symbol: 'HIBOR',
        name: 'Hong Kong Interbank Offered Rate',
        value: 5.57,
        change: 0.02,
        changePercent: 0.36,
        trend: 'UP',
        timestamp: new Date(),
        historical: this.generateHistoricalData(5.0, 6.5, 30)
      },
      monetary_base: {
        symbol: 'HKMB',
        name: 'Hong Kong Monetary Base',
        value: 1850.5,
        change: 12.3,
        changePercent: 0.67,
        trend: 'UP',
        timestamp: new Date(),
        historical: this.generateHistoricalData(1800, 1900, 30)
      },
      exchange_rate: {
        symbol: 'USDHKD',
        name: 'USD/HKD Exchange Rate',
        value: 7.749,
        change: -0.001,
        changePercent: -0.01,
        trend: 'STABLE',
        timestamp: new Date(),
        historical: this.generateHistoricalData(7.75, 7.85, 30)
      }
    };

    return mockData[indicatorType] || mockData.hibor;
  }

  async getSentimentData(symbol: string): Promise<SentimentData> {
    await new Promise(resolve => setTimeout(resolve, 300));

    const baseSentiment = Math.random() * 0.6 - 0.3; // -0.3 to 0.3
    const sentiment = baseSentiment + (Math.random() - 0.5) * 0.2;

    return {
      symbol,
      sentiment: Math.max(-1, Math.min(1, sentiment)),
      confidence: 0.6 + Math.random() * 0.35,
      emotions: {
        fear: Math.random() * 0.3,
        greed: Math.random() * 0.3,
        neutral: 0.7 - Math.random() * 0.3
      },
      sources: {
        social: Math.random(),
        news: Math.random(),
        technical: Math.random()
      },
      timestamp: new Date()
    };
  }

  async getStrategyPerformance(period: string): Promise<StrategyPerformance[]> {
    await new Promise(resolve => setTimeout(resolve, 400));

    return [
      {
        name: 'Traditional Momentum',
        type: 'price',
        totalReturn: 0.15 + Math.random() * 0.1,
        sharpeRatio: 1.2 + Math.random() * 0.3,
        maxDrawdown: 0.08 + Math.random() * 0.05,
        winRate: 0.55 + Math.random() * 0.1,
        volatility: 0.12 + Math.random() * 0.08,
        alpha: 0.02 + Math.random() * 0.03,
        beta: 0.9 + Math.random() * 0.2,
        period
      },
      {
        name: 'HIBOR-Based Strategy',
        type: 'non-price',
        totalReturn: 0.12 + Math.random() * 0.08,
        sharpeRatio: 1.5 + Math.random() * 0.2,
        maxDrawdown: 0.05 + Math.random() * 0.03,
        winRate: 0.65 + Math.random() * 0.1,
        volatility: 0.08 + Math.random() * 0.05,
        alpha: 0.04 + Math.random() * 0.02,
        beta: 0.3 + Math.random() * 0.2,
        period
      },
      {
        name: 'Sentiment-Based Strategy',
        type: 'non-price',
        totalReturn: 0.18 + Math.random() * 0.12,
        sharpeRatio: 1.3 + Math.random() * 0.3,
        maxDrawdown: 0.10 + Math.random() * 0.05,
        winRate: 0.60 + Math.random() * 0.1,
        volatility: 0.15 + Math.random() * 0.07,
        alpha: 0.05 + Math.random() * 0.03,
        beta: 0.7 + Math.random() * 0.2,
        period
      },
      {
        name: 'Combined Strategy',
        type: 'combined',
        totalReturn: 0.20 + Math.random() * 0.10,
        sharpeRatio: 1.6 + Math.random() * 0.2,
        maxDrawdown: 0.06 + Math.random() * 0.03,
        winRate: 0.70 + Math.random() * 0.08,
        volatility: 0.10 + Math.random() * 0.05,
        alpha: 0.07 + Math.random() * 0.03,
        beta: 0.8 + Math.random() * 0.15,
        period
      }
    ];
  }

  // WebSocket connection for real-time signals
  subscribeToRealTimeSignals(symbol: string, callback: (signal: NonPriceSignal) => void): () => void {
    if (!this.subscribers.has(symbol)) {
      this.subscribers.set(symbol, new Set());
    }

    this.subscribers.get(symbol)!.add(callback);

    // Simulate real-time signals
    const interval = setInterval(() => {
      const signal: NonPriceSignal = {
        id: `${symbol}-${Date.now()}`,
        type: Math.random() > 0.5 ? 'macro' : 'sentiment',
        source: 'WebSocket',
        symbol,
        timestamp: new Date(),
        value: Math.random() * 100,
        confidence: 0.6 + Math.random() * 0.4,
        metadata: {
          trend: Math.random() > 0.5 ? 'UP' : 'DOWN',
          strength: Math.random()
        }
      };

      callback(signal);
    }, 5000 + Math.random() * 5000); // 5-10 seconds interval

    return () => {
      clearInterval(interval);
      const subscribers = this.subscribers.get(symbol);
      if (subscribers) {
        subscribers.delete(callback);
        if (subscribers.size === 0) {
          this.subscribers.delete(symbol);
        }
      }
    };
  }

  // Generate mock historical data
  private generateHistoricalData(min: number, max: number, days: number): Array<{ timestamp: Date; value: number }> {
    const data = [];
    let currentValue = (min + max) / 2;
    const now = new Date();

    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      // Add random walk
      currentValue += (Math.random() - 0.5) * (max - min) * 0.02;
      currentValue = Math.max(min, Math.min(max, currentValue));

      data.push({
        timestamp: date,
        value: parseFloat(currentValue.toFixed(2))
      });
    }

    return data;
  }

  // Cleanup method
  cleanup() {
    // Close all WebSocket connections
    this.wsConnections.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    });
    this.wsConnections.clear();
    this.subscribers.clear();
  }
}

// Create singleton instance
export const nonPriceService = new NonPriceService();

// Context for sharing non-price data
interface NonPriceDataContextType {
  signals: NonPriceSignal[];
  isConnected: boolean;
  lastUpdate: Date | null;
  subscribe: (symbol: string, callback: (signal: NonPriceSignal) => void) => () => void;
}

const NonPriceDataContext = createContext<NonPriceDataContextType>({
  signals: [],
  isConnected: false,
  lastUpdate: null,
  subscribe: () => () => {}
});

export const useNonPriceData = () => useContext(NonPriceDataContext);

interface NonPriceDataProviderProps {
  children: ReactNode;
}

export const NonPriceDataProvider: React.FC<NonPriceDataProviderProps> = ({ children }) => {
  const [signals, setSignals] = useState<NonPriceSignal[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const subscribe = (symbol: string, callback: (signal: NonPriceSignal) => void) => {
    setIsConnected(true);

    const unsubscribe = nonPriceService.subscribeToRealTimeSignals(symbol, (signal) => {
      setSignals(prev => [...prev.slice(-99), signal]); // Keep last 100 signals
      setLastUpdate(new Date());
      callback(signal);
    });

    return () => {
      unsubscribe();
      // Check if there are any active subscriptions
      if (signals.length === 0) {
        setIsConnected(false);
      }
    };
  };

  useEffect(() => {
    return () => {
      nonPriceService.cleanup();
    };
  }, []);

  return (
    <NonPriceDataContext.Provider value={{
      signals,
      isConnected,
      lastUpdate,
      subscribe
    }}>
      {children}
    </NonPriceDataContext.Provider>
  );
};

export default NonPriceDataProvider;