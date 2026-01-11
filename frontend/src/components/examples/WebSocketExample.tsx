/**
 * WebSocket Example Component
 * Demonstrates usage of the WebSocket service for real-time data
 */

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useWebSocketAdvanced } from '@/hooks/useWebSocketAdvanced';
import { MessageType } from '@/types/socket';
import { format } from 'date-fns';

interface PriceData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

interface StrategySignal {
  strategyId: string;
  signal: 'buy' | 'sell' | 'hold';
  symbol: string;
  confidence: number;
}

interface SystemAlert {
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  source: string;
}

export const WebSocketExample: React.FC = () => {
  const {
    connectionState,
    isConnected,
    isReconnecting,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send,
    metrics,
    latency,
    messageRate,
    getMessageHistory,
    getCachedData,
    setCachedData,
    clearCache,
  } = useWebSocketAdvanced({
    url: process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:3004',
    autoConnect: true,
    reconnectAttempts: 5,
    enableCaching: true,
    debug: true,
  });

  // State for different data types
  const [prices, setPrices] = useState<Record<string, PriceData>>({});
  const [signals, setSignals] = useState<StrategySignal[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [subscriptionIds, setSubscriptionIds] = useState<string[]>([]);

  // Subscribe to different message types
  useEffect(() => {
    if (isConnected) {
      // Subscribe to price updates
      const priceSubId = subscribe(
        MessageType.PRICE_UPDATE,
        (message: any) => {
          setPrices(prev => ({
            ...prev,
            [message.data.symbol]: message.data,
          }));
          // Cache latest price
          setCachedData(`price_${message.data.symbol}`, message.data, 5000);
        },
        {
          throttle: 100,
          cache: true,
          cacheKey: 'price_update',
        }
      );

      // Subscribe to strategy signals
      const signalSubId = subscribe(
        MessageType.STRATEGY_SIGNAL,
        (message: any) => {
          setSignals(prev => [message.data, ...prev.slice(0, 9)]);
        },
        {
          cache: true,
        }
      );

      // Subscribe to system alerts
      const alertSubId = subscribe(
        MessageType.SYSTEM_ALERT,
        (message: any) => {
          setAlerts(prev => [message.data, ...prev.slice(0, 4)]);
        },
        {
          filter: (msg) => msg.data.level !== 'info', // Filter out info messages
        }
      );

      setSubscriptionIds([priceSubId, signalSubId, alertSubId]);
    }

    return () => {
      subscriptionIds.forEach(id => unsubscribe(id));
    };
  }, [isConnected, subscribe, unsubscribe, setCachedData]);

  // Send test message
  const sendTestMessage = () => {
    send(MessageType.HEARTBEAT, {
      timestamp: Date.now(),
      clientId: 'example-client',
    });
  };

  // Get connection status color
  const getConnectionColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
      case 'reconnecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            WebSocket Connection Status
            <div className={`w-3 h-3 rounded-full ${getConnectionColor()}`} />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">State</p>
              <p className="font-semibold capitalize">{connectionState}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Latency</p>
              <p className="font-semibold">{latency.toFixed(2)}ms</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Message Rate</p>
              <p className="font-semibold">{messageRate}/sec</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Messages</p>
              <p className="font-semibold">{metrics.messagesReceived}</p>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={connect} disabled={isConnected}>
              Connect
            </Button>
            <Button onClick={disconnect} variant="outline" disabled={!isConnected}>
              Disconnect
            </Button>
            <Button onClick={sendTestMessage} variant="secondary" disabled={!isConnected}>
              Send Test Message
            </Button>
            <Button onClick={clearCache} variant="destructive">
              Clear Cache
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Real-time Data */}
      <Tabs defaultValue="prices" className="w-full">
        <TabsList>
          <TabsTrigger value="prices">Price Updates</TabsTrigger>
          <TabsTrigger value="signals">Strategy Signals</TabsTrigger>
          <TabsTrigger value="alerts">System Alerts</TabsTrigger>
          <TabsTrigger value="history">Message History</TabsTrigger>
        </TabsList>

        {/* Price Updates */}
        <TabsContent value="prices">
          <Card>
            <CardHeader>
              <CardTitle>Real-time Price Updates</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(prices).length === 0 ? (
                <p className="text-gray-500">No price data available</p>
              ) : (
                <div className="space-y-2">
                  {Object.entries(prices).map(([symbol, data]) => (
                    <div key={symbol} className="flex justify-between items-center p-2 border rounded">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{symbol}</Badge>
                        <span className="font-semibold">${data.price.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`text-sm ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {data.change >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%
                        </span>
                        <span className="text-sm text-gray-500">Vol: {data.volume.toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Strategy Signals */}
        <TabsContent value="signals">
          <Card>
            <CardHeader>
              <CardTitle>Strategy Signals</CardTitle>
            </CardHeader>
            <CardContent>
              {signals.length === 0 ? (
                <p className="text-gray-500">No signals received</p>
              ) : (
                <div className="space-y-2">
                  {signals.map((signal, index) => (
                    <div key={index} className="flex justify-between items-center p-2 border rounded">
                      <div className="flex items-center gap-2">
                        <Badge variant={signal.signal === 'buy' ? 'default' : signal.signal === 'sell' ? 'destructive' : 'secondary'}>
                          {signal.signal.toUpperCase()}
                        </Badge>
                        <span className="font-medium">{signal.symbol}</span>
                        <span className="text-sm text-gray-500">{signal.strategyId}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">Confidence: {(signal.confidence * 100).toFixed(1)}%</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${signal.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Alerts */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>System Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-gray-500">No alerts</p>
              ) : (
                <div className="space-y-2">
                  {alerts.map((alert, index) => (
                    <Alert key={index} variant={
                      alert.level === 'critical' ? 'destructive' :
                      alert.level === 'error' ? 'destructive' :
                      alert.level === 'warning' ? 'default' : 'default'
                    }>
                      <AlertDescription>
                        <div className="flex justify-between items-start">
                          <div>
                            <Badge variant="outline" className="mb-1">
                              {alert.level.toUpperCase()}
                            </Badge>
                            <p>{alert.message}</p>
                            <p className="text-xs text-gray-500 mt-1">Source: {alert.source}</p>
                          </div>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Message History */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Recent Messages</CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                const history = getMessageHistory(undefined, 20);
                return history.length === 0 ? (
                  <p className="text-gray-500">No messages</p>
                ) : (
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {history.map((msg) => (
                      <div key={msg.id} className="text-sm p-2 border-b">
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-xs">{msg.type}</span>
                          <span className="text-xs text-gray-500">
                            {format(msg.timestamp, 'HH:mm:ss.SSS')}
                          </span>
                        </div>
                        {msg.data && (
                          <pre className="text-xs text-gray-600 mt-1 truncate">
                            {JSON.stringify(msg.data, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                );
              })()}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WebSocketExample;