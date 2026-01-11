/**
 * WebSocket Redux Slice
 * Manages WebSocket connection state and real-time data
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ConnectionState } from '@/types/socket';

// WebSocket state interface
interface WebSocketState {
  // Connection state
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;

  // Connection metrics
  metrics: {
    connectedAt?: number;
    disconnectedAt?: number;
    reconnectCount: number;
    messagesReceived: number;
    messagesSent: number;
    lastMessageAt?: number;
    averageLatency: number;
    errors: Array<{
      timestamp: number;
      message: string;
      code?: string;
    }>;
  };

  // Real-time data storage
  realtimeData: Record<string, {
    id: string;
    type: string;
    timestamp: number;
    data: any;
  }>;

  // Subscriptions
  subscriptions: Record<string, {
    topic: string;
    active: boolean;
    lastMessage?: number;
  }>;

  // Connection configuration
  config: {
    url?: string;
    reconnectAttempts: number;
    reconnectDelay: number;
    heartbeatInterval: number;
    autoConnect: boolean;
  };

  // UI state
  showConnectionStatus: boolean;
  lastError?: string;
}

// Initial state
const initialState: WebSocketState = {
  connectionState: ConnectionState.DISCONNECTED,
  isConnected: false,
  isReconnecting: false,
  metrics: {
    reconnectCount: 0,
    messagesReceived: 0,
    messagesSent: 0,
    averageLatency: 0,
    errors: [],
  },
  realtimeData: {},
  subscriptions: {},
  config: {
    reconnectAttempts: 5,
    reconnectDelay: 1000,
    heartbeatInterval: 30000,
    autoConnect: true,
  },
  showConnectionStatus: false,
};

// Create slice
const websocketSlice = createSlice({
  name: 'websocket',
  initialState,
  reducers: {
    // Connection actions
    updateConnectionState: (state, action: PayloadAction<ConnectionState>) => {
      state.connectionState = action.payload;
      state.isConnected = action.payload === ConnectionState.CONNECTED;
      state.isReconnecting = action.payload === ConnectionState.RECONNECTING;
    },

    setConnectionConfig: (state, action: PayloadAction<Partial<WebSocketState['config']>>) => {
      state.config = { ...state.config, ...action.payload };
    },

    // Metrics actions
    setConnectionMetrics: (state, action: PayloadAction<Partial<WebSocketState['metrics']>>) => {
      state.metrics = { ...state.metrics, ...action.payload };
    },

    incrementMessagesReceived: (state) => {
      state.metrics.messagesReceived += 1;
    },

    incrementMessagesSent: (state) => {
      state.metrics.messagesSent += 1;
    },

    addConnectionError: (state, action: PayloadAction<{ message: string; code?: string }>) => {
      state.metrics.errors.push({
        timestamp: Date.now(),
        ...action.payload,
      });

      // Keep only last 50 errors
      if (state.metrics.errors.length > 50) {
        state.metrics.errors = state.metrics.errors.slice(-50);
      }

      state.lastError = action.payload.message;
    },

    clearConnectionErrors: (state) => {
      state.metrics.errors = [];
      state.lastError = undefined;
    },

    // Real-time data actions
    addRealtimeData: (state, action: PayloadAction<{
      id: string;
      type: string;
      timestamp: number;
      data: any;
    }>) => {
      state.realtimeData[action.payload.id] = action.payload;

      // Keep only last 100 messages
      const dataEntries = Object.entries(state.realtimeData);
      if (dataEntries.length > 100) {
        const sortedEntries = dataEntries.sort((a, b) => a[1].timestamp - b[1].timestamp);
        const toRemove = sortedEntries.slice(0, dataEntries.length - 100);
        toRemove.forEach(([id]) => {
          delete state.realtimeData[id];
        });
      }
    },

    removeRealtimeData: (state, action: PayloadAction<string>) => {
      delete state.realtimeData[action.payload];
    },

    clearRealtimeData: (state) => {
      state.realtimeData = {};
    },

    // Subscription actions
    addSubscription: (state, action: PayloadAction<{
      id: string;
      topic: string;
    }>) => {
      state.subscriptions[action.payload.id] = {
        topic: action.payload.topic,
        active: true,
      };
    },

    updateSubscription: (state, action: PayloadAction<{
      id: string;
      updates: Partial<WebSocketState['subscriptions'][string]>;
    }>) => {
      const subscription = state.subscriptions[action.payload.id];
      if (subscription) {
        Object.assign(subscription, action.payload.updates);
      }
    },

    removeSubscription: (state, action: PayloadAction<string>) => {
      delete state.subscriptions[action.payload];
    },

    clearSubscriptions: (state) => {
      state.subscriptions = {};
    },

    // UI actions
    setShowConnectionStatus: (state, action: PayloadAction<boolean>) => {
      state.showConnectionStatus = action.payload;
    },

    // Reset action
    resetWebSocketState: (state) => {
      Object.assign(state, initialState);
    },
  },
});

// Export actions
export const {
  updateConnectionState,
  setConnectionConfig,
  setConnectionMetrics,
  incrementMessagesReceived,
  incrementMessagesSent,
  addConnectionError,
  clearConnectionErrors,
  addRealtimeData,
  removeRealtimeData,
  clearRealtimeData,
  addSubscription,
  updateSubscription,
  removeSubscription,
  clearSubscriptions,
  setShowConnectionStatus,
  resetWebSocketState,
} = websocketSlice.actions;

// Selectors
export const selectWebSocketState = (state: { websocket: WebSocketState }) => state.websocket;
export const selectConnectionState = (state: { websocket: WebSocketState }) => state.websocket.connectionState;
export const selectIsConnected = (state: { websocket: WebSocketState }) => state.websocket.isConnected;
export const selectIsReconnecting = (state: { websocket: WebSocketState }) => state.websocket.isReconnecting;
export const selectConnectionMetrics = (state: { websocket: WebSocketState }) => state.websocket.metrics;
export const selectRealtimeData = (state: { websocket: WebSocketState }) => state.websocket.realtimeData;
export const selectSubscriptions = (state: { websocket: WebSocketState }) => state.websocket.subscriptions;
export const selectConnectionErrors = (state: { websocket: WebSocketState }) => state.websocket.metrics.errors;
export const selectLastError = (state: { websocket: WebSocketState }) => state.websocket.lastError;

// Specific data selectors
export const selectPriceUpdates = (state: { websocket: WebSocketState }) => {
  return Object.values(state.websocket.realtimeData).filter(
    item => item.type === 'price_update'
  );
};

export const selectStrategySignals = (state: { websocket: WebSocketState }) => {
  return Object.values(state.websocket.realtimeData).filter(
    item => item.type === 'strategy_signal'
  );
};

export const selectSystemAlerts = (state: { websocket: WebSocketState }) => {
  return Object.values(state.websocket.realtimeData).filter(
    item => item.type === 'system_alert'
  );
};

export const selectStrategyExecutions = (state: { websocket: WebSocketState }, strategyId?: string) => {
  const executions = Object.values(state.websocket.realtimeData).filter(
    item => item.type === 'strategy_execution'
  );

  if (strategyId) {
    return executions.filter(item => item.data.strategyId === strategyId);
  }

  return executions;
};

// Memoized selectors for performance
export const selectConnectionStats = (state: { websocket: WebSocketState }) => {
  const { metrics, connectionState } = state.websocket;
  return {
    state: connectionState,
    uptime: metrics.connectedAt ? Date.now() - metrics.connectedAt : 0,
    messagesReceived: metrics.messagesReceived,
    messagesSent: metrics.messagesSent,
    averageLatency: metrics.averageLatency,
    reconnectCount: metrics.reconnectCount,
    errorCount: metrics.errors.length,
  };
};

export const selectRealtimeDataByType = (type: string) => (state: { websocket: WebSocketState }) => {
  return Object.values(state.websocket.realtimeData).filter(
    item => item.type === type
  );
};

export const selectLatestMessageByType = (type: string) => (state: { websocket: WebSocketState }) => {
  const messages = Object.values(state.websocket.realtimeData).filter(
    item => item.type === type
  );

  if (messages.length === 0) {
    return null;
  }

  return messages.reduce((latest, current) =>
    current.timestamp > latest.timestamp ? current : latest
  );
};

// Export reducer
export default websocketSlice.reducer;