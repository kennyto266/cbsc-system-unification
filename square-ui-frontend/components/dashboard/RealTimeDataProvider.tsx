'use client';

import React, { createContext, useContext, ReactNode, useState } from 'react';
import { useGovernmentWebSocket } from '@/hooks/useWebSocket';
import { SquareBadge } from '@/components/ui';

interface RealTimeData {
  hibor?: any;
  monetaryBase?: any;
  exchangeRate?: any;
  marketRegime?: any;
}

interface RealTimeDataContextType {
  data: RealTimeData;
  isConnected: boolean;
  lastUpdate: string | null;
  refresh: () => void;
}

const RealTimeDataContext = createContext<RealTimeDataContextType | undefined>(undefined);

export function RealTimeDataProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<RealTimeData>({});
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const governmentWs = useGovernmentWebSocket();
  const regimeWs = useMarketRegimeWebSocket();

  // Handle government data updates
  React.useEffect(() => {
    if (governmentWs.lastMessage?.type === 'government_data') {
      const messageData = governmentWs.lastMessage.data;
      setData(prev => ({
        ...prev,
        hibor: messageData.hibor || prev.hibor,
        monetaryBase: messageData.monetaryBase || prev.monetaryBase,
        exchangeRate: messageData.exchangeRate || prev.exchangeRate
      }));
      setLastUpdate(new Date().toLocaleTimeString('zh-TW'));
    }
  }, [governmentWs.lastMessage]);

  // Handle market regime updates
  React.useEffect(() => {
    if (regimeWs.lastMessage?.type === 'market_regime') {
      const messageData = regimeWs.lastMessage.data;
      setData(prev => ({
        ...prev,
        marketRegime: messageData
      }));
      setLastUpdate(new Date().toLocaleTimeString('zh-TW'));
    }
  }, [regimeWs.lastMessage]);

  const refresh = () => {
    // 手動刷新所有數據
    console.log('Refreshing real-time data...');
    // 這裡可以觸發所有 API 重新獲取
  };

  const value: RealTimeDataContextType = {
    data,
    isConnected: governmentWs.isConnected || regimeWs.isConnected,
    lastUpdate,
    refresh
  };

  return (
    <RealTimeDataContext.Provider value={value}>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${
          (governmentWs.isConnected || regimeWs.isConnected)
            ? 'bg-green-500'
            : 'bg-red-500'
        }`} />
        <span className="text-xs text-gray-600">
          {(governmentWs.isConnected || regimeWs.isConnected) ? '實時連接' : '連接斷開'}
        </span>
        {lastUpdate && (
          <span className="text-xs text-gray-500">
            更新: {lastUpdate}
          </span>
        )}
      </div>
      {children}
    </RealTimeDataContext.Provider>
  );
}

export function useRealTimeData() {
  const context = useContext(RealTimeDataContext);
  if (!context) {
    throw new Error('useRealTimeData must be used within RealTimeDataProvider');
  }
  return context;
}