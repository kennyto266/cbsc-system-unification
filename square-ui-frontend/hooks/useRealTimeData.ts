/**
 * 實時數據管理 Hook
 * 整合 WebSocket 和模擬數據，提供統一的實時數據接口
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket, WS_CHANNELS } from '@/lib/websocket';
import { mockWebSocketServer, checkWebSocketAvailability } from '@/lib/mock-websocket-server';

interface RealTimeDataOptions {
  channel: string;
  useMockIfUnavailable?: boolean;
  updateInterval?: number;
}

interface RealTimeDataReturn<T> {
  data: T | null;
  isConnected: boolean;
  isUsingMock: boolean;
  lastUpdate: Date | null;
  error: string | null;
  forceRefresh: () => void;
}

export function useRealTimeData<T = any>({
  channel,
  useMockIfUnavailable = true,
  updateInterval = 5000
}: RealTimeDataOptions): RealTimeDataReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [isUsingMock, setIsUsingMock] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mockDataRef = useRef<T | null>(null);

  // 處理數據更新
  const handleDataUpdate = useCallback((newData: T) => {
    setData(newData);
    setLastUpdate(new Date());
    setError(null);
    mockDataRef.current = newData;
  }, []);

  // 嘗試使用 WebSocket
  const { isConnected, lastMessage, state: wsState } = useWebSocket(channel, handleDataUpdate);

  // 檢查並切換到模擬數據
  useEffect(() => {
    if (!isConnected && useMockIfAvailable && !isUsingMock) {
      const checkAndSwitchToMock = async () => {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3004/ws';
        const isWsAvailable = await checkWebSocketAvailability(wsUrl);

        if (!isWsAvailable && !isUsingMock) {
          console.log(`WebSocket not available for ${channel}, switching to mock data`);
          setIsUsingMock(true);

          // 啟動模擬數據更新
          mockWebSocketServer.startMockDataUpdates((ch, data) => {
            if (ch === channel) {
              handleDataUpdate(data as T);
            }
          });
        }
      };

      checkAndSwitchToMock();
    }
  }, [isConnected, isUsingMock, channel, useMockIfAvailable, handleDataUpdate]);

  // 強制刷新
  const forceRefresh = useCallback(() => {
    if (isUsingMock) {
      // 觸發模擬數據更新
      mockWebSocketServer.startMockDataUpdates((ch, data) => {
        if (ch === channel) {
          handleDataUpdate(data as T);
        }
      });
    }
  }, [isUsingMock, channel, handleDataUpdate]);

  // 獲取最後的消息
  useEffect(() => {
    if (lastMessage && !isUsingMock) {
      handleDataUpdate(lastMessage as T);
    }
  }, [lastMessage, isUsingMock, handleDataUpdate]);

  return {
    data,
    isConnected,
    isUsingMock,
    lastUpdate,
    error,
    forceRefresh
  };
}

// 策略表現數據 Hook
export function useStrategyPerformance() {
  return useRealTimeData({
    channel: WS_CHANNELS.STRATEGY_PERFORMANCE,
    updateInterval: 5000
  });
}

// 市場數據 Hook
export function useMarketData() {
  return useRealTimeData({
    channel: WS_CHANNELS.MARKET_DATA,
    updateInterval: 2000
  });
}

// HIBOR 利率 Hook
export function useHiborRates() {
  return useRealTimeData({
    channel: WS_CHANNELS.HIBOR_RATES,
    updateInterval: 30000
  });
}

// CBSC 牛熊證 Hook
export function useCBSCContracts() {
  return useRealTimeData({
    channel: WS_CHANNELS.CBSC_CONTRACTS,
    updateInterval: 10000
  });
}

// 政府數據 Hook
export function useGovernmentData() {
  return useRealTimeData({
    channel: WS_CHANNELS.GOVERNMENT_DATA,
    updateInterval: 60000
  });
}

// 系統狀態 Hook
export function useSystemStatus() {
  return useRealTimeData({
    channel: WS_CHANNELS.SYSTEM_STATUS,
    updateInterval: 5000
  });
}

// 多頻道實時數據 Hook
export function useMultipleRealTimeData(channels: string[]) {
  const [allData, setAllData] = useState<Record<string, any>>({});
  const [connections, setConnections] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const results: Record<string, any> = {};
    const connectionStatus: Record<string, boolean> = {};

    channels.forEach(channel => {
      const { data, isConnected } = useRealTimeData({ channel });
      results[channel] = data;
      connectionStatus[channel] = isConnected;
    });

    setAllData(results);
    setConnections(connectionStatus);
  }, [channels]);

  return {
    data: allData,
    connections
  };
}