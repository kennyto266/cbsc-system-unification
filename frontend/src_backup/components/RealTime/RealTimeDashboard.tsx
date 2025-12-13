import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Switch, Alert, Button, Space, Typography } from 'antd';
import {
  WifiOutlined,
  DisconnectOutlined,
  SyncOutlined,
  SignalFilled,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined
} from '@ant-design/icons';
import { useWebSocket } from '../../hooks/useWebSocket';
import './RealTimeDashboard.css';

const { Title, Text } = Typography;

interface RealTimeStats {
  activeConnections: number;
  totalStrategies: number;
  serverUptime: string;
  memoryUsage: string;
  cpuUsage: string;
  lastUpdate: string;
}

interface PerformanceUpdate {
  strategyId: string;
  strategyName: string;
  annualReturn: number;
  sharpeRatio: number;
  winRate: number;
  timestamp: string;
}

interface TradingSignal {
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  strength: number;
  timestamp: string;
}

const RealTimeDashboard: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [realTimeStats, setRealTimeStats] = useState<RealTimeStats | null>(null);
  const [performanceUpdates, setPerformanceUpdates] = useState<PerformanceUpdate[]>([]);
  const [signals, setSignals] = useState<Record<string, TradingSignal>>({});

  const {
    connected,
    connecting,
    error,
    connectionStatus,
    lastMessage,
    subscribeToPerformance,
    subscribeToSignals,
    reconnect
  } = useWebSocket('ws://localhost:3004/ws');

  useEffect(() => {
    if (connected) {
      // 訂閱實時數據流
      subscribeToPerformance();
      subscribeToSignals();
    }
  }, [connected, subscribeToPerformance, subscribeToSignals]);

  useEffect(() => {
    // 處理WebSocket消息
    if (lastMessage) {
      try {
        const data = typeof lastMessage.data === 'string' ? JSON.parse(lastMessage.data) : lastMessage.data;

        switch (data.type) {
          case 'performance_update':
            handlePerformanceUpdate(data);
            break;
          case 'signals_update':
            handleSignalsUpdate(data);
            break;
          case 'system_health':
            handleSystemHealth(data);
            break;
          default:
            console.log('Unhandled message type:', data.type);
        }
      } catch (error) {
        console.error('Failed to process message:', error);
      }
    }
  }, [lastMessage]);

  const handlePerformanceUpdate = (data: any) => {
    if (data.data?.updated_strategies) {
      const updates: PerformanceUpdate[] = data.data.updated_strategies.map((strategy: any) => ({
        strategyId: strategy.id,
        strategyName: strategy.name,
        annualReturn: strategy.annual_return,
        sharpeRatio: strategy.sharpe_ratio,
        winRate: strategy.win_rate,
        timestamp: strategy.last_updated
      }));

      setPerformanceUpdates(prev => [...updates.slice(-5), ...prev].slice(0, 10)); // 保留最新10條
    }
  };

  const handleSignalsUpdate = (data: any) => {
    if (data.data) {
      setSignals(prev => ({ ...data.data, ...prev }));
    }
  };

  const handleSystemHealth = (data: any) => {
    if (data.data) {
      setRealTimeStats({
        activeConnections: data.data.active_connections || 0,
        totalStrategies: data.data.total_strategies || 0,
        serverUptime: data.data.server_uptime || 'N/A',
        memoryUsage: data.data.memory_usage || '0%',
        cpuUsage: data.data.cpu_usage || '0%',
        lastUpdate: data.data.last_update || new Date().toISOString()
      });
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return '#52c41a';
      case 'SELL': return '#ff4d4f';
      case 'HOLD': return '#faad14';
      default: return '#d9d9d9';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'BUY': return <ArrowUpOutlined />;
      case 'SELL': return <ArrowDownOutlined />;
      case 'HOLD': return <MinusOutlined />;
      default: return <SignalFilled />;
    }
  };

  const getConnectionStatus = () => {
    if (connecting) return { color: 'warning', text: '連接中...', icon: <SyncOutlined spin /> };
    if (connected) return { color: 'success', text: '已連接', icon: <WifiOutlined /> };
    if (error) return { color: 'error', text: '連接失敗', icon: <DisconnectOutlined /> };
    return { color: 'default', text: '未連接', icon: <DisconnectOutlined /> };
  };

  const connectionStatus = getConnectionStatus();

  return (
    <div className="real-time-dashboard">
      {/* 連接狀態 */}
      <Card className="connection-status-card" size="small">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Tag color={connectionStatus.color} icon={connectionStatus.icon}>
                {connectionStatus.text}
              </Tag>
              <Text type="secondary">
                WebSocket狀態: {connectionStatus.replace('...', '')}
              </Text>
            </Space>
          </Col>
          <Col>
            <Space>
              <Text>自動刷新</Text>
              <Switch
                checked={autoRefresh}
                onChange={setAutoRefresh}
                size="small"
              />
              {!connected && (
                <Button
                  type="primary"
                  size="small"
                  icon={<SyncOutlined />}
                  onClick={reconnect}
                  loading={connecting}
                >
                  重新連接
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 錯誤提示 */}
      {error && (
        <Alert
          message="連接錯誤"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 實時統計 */}
      {realTimeStats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="活躍連接"
                value={realTimeStats.activeConnections}
                prefix={<WifiOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="策略總數"
                value={realTimeStats.totalStrategies}
                prefix={<SignalFilled />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="內存使用"
                value={realTimeStats.memoryUsage}
                valueStyle={{
                  color: parseFloat(realTimeStats.memoryUsage) > 70 ? '#ff4d4f' : '#52c41a'
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="CPU使用"
                value={realTimeStats.cpuUsage}
                valueStyle={{
                  color: parseFloat(realTimeStats.cpuUsage) > 50 ? '#ff4d4f' : '#52c41a'
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Row gutter={[16, 16]}>
        {/* 交易信號 */}
        <Col xs={24} lg={12}>
          <Card
            title="實時交易信號"
            extra={
              <Tag color="blue">
                {Object.keys(signals).length} 個信號
              </Tag>
            }
          >
            <div className="signals-container">
              {Object.entries(signals).map(([category, signal]) => (
                <div key={category} className="signal-item">
                  <div className="signal-header">
                    <Text strong>{category.replace(/_/g, ' ').toUpperCase()}</Text>
                    <Tag
                      color={getSignalColor(signal.signal)}
                      icon={getSignalIcon(signal.signal)}
                    >
                      {signal.signal}
                    </Tag>
                  </div>
                  <div className="signal-details">
                    <Space>
                      <Text type="secondary">信心度:</Text>
                      <Progress
                        percent={signal.confidence * 100}
                        size="small"
                        style={{ width: 80 }}
                        strokeColor={signal.confidence > 0.8 ? '#52c41a' : '#faad14'}
                      />
                      <Text type="secondary">強度:</Text>
                      <Progress
                        percent={signal.strength * 100}
                        size="small"
                        style={{ width: 80 }}
                        strokeColor={signal.strength > 0.8 ? '#52c41a' : '#1890ff'}
                      />
                    </Space>
                  </div>
                  <div className="signal-time">
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {new Date(signal.timestamp).toLocaleString()}
                    </Text>
                  </div>
                </div>
              ))}

              {Object.keys(signals).length === 0 && (
                <div className="no-data">
                  <Text type="secondary">暫無交易信號數據</Text>
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* 性能更新 */}
        <Col xs={24} lg={12}>
          <Card
            title="策略性能更新"
            extra={
              <Tag color="blue">
                {performanceUpdates.length} 條更新
              </Tag>
            }
          >
            <div className="performance-updates-container">
              {performanceUpdates.map((update, index) => (
                <div key={index} className="performance-item">
                  <div className="performance-header">
                    <Text strong>{update.strategyName}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {new Date(update.timestamp).toLocaleTimeString()}
                    </Text>
                  </div>
                  <div className="performance-metrics">
                    <Row gutter={8}>
                      <Col span={8}>
                        <div className="metric">
                          <Text type="secondary" style={{ fontSize: 11 }}>年化收益</Text>
                          <div style={{
                            color: update.annualReturn > 0 ? '#52c41a' : '#ff4d4f',
                            fontWeight: 'bold'
                          }}>
                            {(update.annualReturn * 100).toFixed(2)}%
                          </div>
                        </div>
                      </Col>
                      <Col span={8}>
                        <div className="metric">
                          <Text type="secondary" style={{ fontSize: 11 }}>夏普比率</Text>
                          <div style={{ fontWeight: 'bold' }}>
                            {update.sharpeRatio?.toFixed(2) || 'N/A'}
                          </div>
                        </div>
                      </Col>
                      <Col span={8}>
                        <div className="metric">
                          <Text type="secondary" style={{ fontSize: 11 }}>勝率</Text>
                          <Progress
                            percent={update.winRate * 100}
                            size="small"
                            format={() => `${(update.winRate * 100).toFixed(1)}%`}
                            strokeColor={update.winRate > 0.6 ? '#52c41a' : '#faad14'}
                          />
                        </div>
                      </Col>
                    </Row>
                  </div>
                </div>
              ))}

              {performanceUpdates.length === 0 && (
                <div className="no-data">
                  <Text type="secondary">暫無性能更新數據</Text>
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RealTimeDashboard;