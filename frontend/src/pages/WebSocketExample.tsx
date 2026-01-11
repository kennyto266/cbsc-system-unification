/**
 * WebSocket Example Page
 * Demonstrates WebSocket real-time communication functionality
 */

import React, { useState } from 'react';
import { WebSocketProvider } from '../contexts/WebSocketContext';
import { WebSocketStatus } from '../components/WebSocketStatus';
import { useWebSocket } from '../hooks/useWebSocketEnhanced';
import { useWebSocketChannel } from '../hooks/useWebSocketChannel';
import { ChannelType, MessageType } from '../types/websocket';

// Example component showing WebSocket usage
const WebSocketExampleContent: React.FC = () => {
  const [message, setMessage] = useState('');
  const [logs, setLogs] = useState<string[]>([]);

  // Basic WebSocket hook
  const { isConnected, connectionState, send, subscribe } = useWebSocket({
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:3004/ws',
    autoConnect: true,
    onConnect: () => addLog('Connected to WebSocket'),
    onDisconnect: () => addLog('Disconnected from WebSocket'),
    onError: (error) => addLog(`Error: ${error.message}`)
  });

  // Channel subscription hook for strategy updates
  const {
    data: strategyData,
    send: sendToStrategyChannel,
    isConnected: strategyConnected
  } = useWebSocketChannel(ChannelType.STRATEGY_UPDATES, {
    onMessage: (data) => addLog(`Strategy update: ${JSON.stringify(data)}`),
    filters: { active: true }
  });

  // Channel subscription hook for price feeds
  const {
    data: priceData,
    history: priceHistory,
    clearHistory
  } = useWebSocketChannel(ChannelType.PRICE_FEEDS, {
    onMessage: (data) => addLog(`Price update: ${data.symbol} - $${data.price}`),
    cacheKey: 'latest_prices',
    cacheTTL: 30000
  });

  // Add log entry
  const addLog = (entry: string) => {
    setLogs(prev => [...prev.slice(-99), `${new Date().toLocaleTimeString()}: ${entry}`]);
  };

  // Send message
  const handleSendMessage = () => {
    if (message.trim()) {
      const success = send({
        id: `example_${Date.now()}`,
        type: MessageType.DATA,
        data: { message: message.trim(), timestamp: Date.now() },
        timestamp: Date.now()
      });

      if (success) {
        addLog(`Sent: ${message}`);
        setMessage('');
      } else {
        addLog('Failed to send message');
      }
    }
  };

  // Send to strategy channel
  const handleSendStrategyCommand = () => {
    sendToStrategyChannel({
      command: 'refresh',
      timestamp: Date.now()
    });
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">WebSocket Example</h1>

        {/* WebSocket Status */}
        <WebSocketStatus showDetails position="top-right" />

        {/* Connection Info */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-gray-600">State:</span>
              <span className="ml-2 font-medium">{connectionState}</span>
            </div>
            <div>
              <span className="text-gray-600">Connected:</span>
              <span className={`ml-2 font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                {isConnected ? 'Yes' : 'No'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Strategy Channel:</span>
              <span className={`ml-2 font-medium ${strategyConnected ? 'text-green-600' : 'text-red-600'}`}>
                {strategyConnected ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Price History:</span>
              <span className="ml-2 font-medium">{priceHistory.length} items</span>
            </div>
          </div>
        </div>

        {/* Message Sending */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Send Message</h2>
          <div className="flex space-x-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type a message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!isConnected}
            />
            <button
              onClick={handleSendMessage}
              disabled={!isConnected || !message.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>

        {/* Channel Actions */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Channel Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={handleSendStrategyCommand}
              className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
            >
              Refresh Strategies
            </button>
            <button
              onClick={clearHistory}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Clear Price History
            </button>
          </div>
        </div>

        {/* Data Display */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Strategy Data</h2>
            <pre className="text-sm bg-gray-100 p-4 rounded overflow-auto">
              {strategyData ? JSON.stringify(strategyData, null, 2) : 'No data'}
            </pre>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Price Data</h2>
            <pre className="text-sm bg-gray-100 p-4 rounded overflow-auto">
              {priceData ? JSON.stringify(priceData, null, 2) : 'No data'}
            </pre>
          </div>
        </div>

        {/* Logs */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Activity Logs</h2>
            <button
              onClick={() => setLogs([])}
              className="px-4 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Clear Logs
            </button>
          </div>
          <div className="bg-gray-50 rounded p-4 h-64 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-gray-500">No activity yet</p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="text-sm font-mono text-gray-700 mb-1">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Wrap with WebSocket provider
const WebSocketExample: React.FC = () => {
  return (
    <WebSocketProvider>
      <WebSocketExampleContent />
    </WebSocketProvider>
  );
};

export default WebSocketExample;