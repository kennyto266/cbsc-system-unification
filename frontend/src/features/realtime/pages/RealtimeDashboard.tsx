import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, TrendingDown, Signal, Zap, Pause } from 'lucide-react';
import { Button } from 'antd';
import { RealTimeChart } from '../../../shared/components/charts';

interface RealtimeDashboardProps {}

interface MarketData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

interface Signal {
  id: string;
  strategy: string;
  symbol: string;
  type: 'buy' | 'sell';
  price: number;
  time: string;
  status: 'pending' | 'executed' | 'failed';
}

const RealtimeDashboard: React.FC<RealtimeDashboardProps> = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['000001', '000002', '000300']);

  // Mock data source for real-time chart (returns value around 12.50)
  const mockDataSource = async (): Promise<number> => {
    const basePrice = 12.50;
    const fluctuation = (Math.random() - 0.5) * 0.5; // +/- 0.25 fluctuation
    return basePrice + fluctuation;
  };

  useEffect(() => {
    // Initialize mock market data
    const mockMarketData: MarketData[] = [
      { symbol: '000001', name: '平安银行', price: 12.5, change: 0.15, changePercent: 1.2, volume: 1500000 },
      { symbol: '000002', name: '万科A', price: 8.8, change: -0.08, changePercent: -0.9, volume: 2100000 },
      { symbol: '000300', name: '沪深300', price: 3850, change: 25, changePercent: 0.65, volume: 56000000 }
    ];
    setMarketData(mockMarketData);

    // Mock signals
    const mockSignals: Signal[] = [
      { id: '1', strategy: '动量策略', symbol: '000001', type: 'buy', price: 12.5, time: '10:30:05', status: 'executed' },
      { id: '2', strategy: '均值回归', symbol: '000002', type: 'sell', price: 8.8, time: '10:28:15', status: 'pending' },
      { id: '3', strategy: '突破策略', symbol: '000300', type: 'buy', price: 3850, time: '10:25:30', status: 'executed' }
    ];
    setSignals(mockSignals);

    // Simulate connection
    const timer = setTimeout(() => {
      setIsConnected(true);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  const handleToggleConnection = () => {
    setIsConnected(!isConnected);
  };

  const handleExecuteSignal = async (signalId: string) => {
    // TODO: Execute signal via API
    setSignals(prev => prev.map(s =>
      s.id === signalId ? { ...s, status: 'executed' as const } : s
    ));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              实时监控
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              实时行情数据和交易信号
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md ${
              isConnected
                ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
              <span className="text-sm font-medium">
                {isConnected ? '已连接' : '未连接'}
              </span>
            </div>
            <Button
              variant={isConnected ? 'destructive' : 'default'}
              onClick={handleToggleConnection}
              className={isConnected ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}
            >
              {isConnected ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  断开
                </>
              ) : (
                <>
                  <Activity className="h-4 w-4 mr-2" />
                  连接
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Market Data Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {marketData.map((data, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">{data.name}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{data.symbol}</p>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  data.changePercent >= 0
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                    : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                }`}>
                  {data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%
                </div>
              </div>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    ¥{data.price.toFixed(2)}
                  </p>
                  <p className={`text-sm flex items-center gap-1 mt-1 ${
                    data.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {data.change >= 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 dark:text-gray-400">成交量</p>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {(data.volume / 10000).toFixed(1)}万
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Real-time Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              实时价格
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">更新间隔:</span>
              <select className="text-sm bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1">
                <option>1秒</option>
                <option>5秒</option>
                <option>10秒</option>
              </select>
            </div>
          </div>
          <RealTimeChart
            title="000001 - 平安银行"
            dataSource={mockDataSource}
            updateInterval={1000}
            height={300}
          />
        </div>

        {/* Trading Signals */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Signal className="h-5 w-5" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                交易信号
              </h2>
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              今日信号: {signals.length}
            </span>
          </div>

          <div className="space-y-3">
            {signals.map((signal) => (
              <div
                key={signal.id}
                className={`flex items-center justify-between p-4 rounded-lg border ${
                  signal.type === 'buy'
                    ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                    : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    signal.type === 'buy'
                      ? 'bg-green-500 text-white'
                      : 'bg-red-500 text-white'
                  }`}>
                    {signal.type === 'buy' ? (
                      <TrendingUp className="h-5 w-5" />
                    ) : (
                      <TrendingDown className="h-5 w-5" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {signal.strategy}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {signal.symbol} @ ¥{signal.price.toFixed(2)} · {signal.time}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded ${
                    signal.status === 'executed'
                      ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                      : signal.status === 'pending'
                      ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300'
                      : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                  }`}>
                    {signal.status === 'executed' ? '已执行' :
                     signal.status === 'pending' ? '待执行' : '执行失败'}
                  </span>
                  {signal.status === 'pending' && (
                    <Button
                      size="sm"
                      onClick={() => handleExecuteSignal(signal.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <Zap className="h-3 w-3 mr-1" />
                      执行
                    </Button>
                  )}
                </div>
              </div>
            ))}

            {signals.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>暂无交易信号</p>
              </div>
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                <Activity className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">活跃策略</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">5</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                <Signal className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">今日信号</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{signals.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">信号胜率</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">68%</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealtimeDashboard;
