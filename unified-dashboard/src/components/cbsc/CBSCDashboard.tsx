/**
 * CBSC Dashboard 综合组件
 * CBSC Dashboard Main Component
 */

import React, { useState, useEffect } from 'react';
import {
  getDashboardSummary,
  initWebSocketService,
  disconnectWebSocketService,
  CBSCDashboardData
} from '../../services/cbscService';
import MarketSentimentCard from './MarketSentimentCard';
import TopContractsTable from './TopContractsTable';
import SentimentTrendChart from './SentimentTrendChart';

const CBSCDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<CBSCDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // 获取初始数据
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getDashboardSummary();
        setDashboardData(data);
        setLastUpdate(new Date());
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('无法加载 Dashboard 数据');
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();

    // 设置定时刷新 (每30秒)
    const refreshInterval = setInterval(fetchInitialData, 30000);

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  // 设置 WebSocket 实时更新
  useEffect(() => {
    const wsService = initWebSocketService((data) => {
      if (data.type === 'cbsc_update') {
        setDashboardData(data.payload);
        setLastUpdate(new Date());
      }
    });

    return () => {
      disconnectWebSocketService();
    };
  }, []);

  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toFixed(decimals);
  };

  // 格式化大数字
  const formatLargeNumber = (num: number): string => {
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(1)}亿`;
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}万`;
    }
    return num.toString();
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-600">
            <h3 className="font-medium">加载错误</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CBSC 牛熊证市场监控</h1>
          <p className="text-gray-600 mt-1">实时市场情绪与牛熊证数据分析</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">最后更新</div>
          <div className="text-sm font-medium text-gray-700">
            {lastUpdate.toLocaleTimeString('zh-CN')}
          </div>
        </div>
      </div>

      {/* 关键指标卡片 */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* 恒指当前价 */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-500 mb-1">恒生指数</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatNumber(dashboardData.statistics.hsif_current)}
            </div>
            <div className={`text-sm font-medium mt-1 ${
              dashboardData.statistics.hsif_change >= 0 ? 'text-red-600' : 'text-green-600'
            }`}>
              {dashboardData.statistics.hsif_change >= 0 ? '+' : ''}
              {formatNumber(dashboardData.statistics.hsif_change)}
              ({formatNumber(dashboardData.statistics.hsif_change_percent)}%)
            </div>
          </div>

          {/* 总成交量 */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-500 mb-1">总成交量</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatLargeNumber(dashboardData.statistics.total_volume)}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              {dashboardData.statistics.active_contracts} 只活跃合约
            </div>
          </div>

          {/* 市值估算 */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-500 mb-1">市值估算</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatLargeNumber(dashboardData.statistics.market_capitalization)}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              港币
            </div>
          </div>

          {/* 市场状态 */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-500 mb-1">市场状态</div>
            <div className="text-2xl font-bold text-gray-900">
              {new Date().getHours() >= 9 && new Date().getHours() <= 16 ? '交易中' : '休市'}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              {dashboardData.market_sentiment.sentiment_label}
            </div>
          </div>
        </div>
      )}

      {/* 主要内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 市场情绪指标卡片 */}
        <MarketSentimentCard
          sentiment={dashboardData?.market_sentiment || {}}
          loading={loading}
        />

        {/* 市场情绪趋势图表 */}
        <SentimentTrendChart loading={loading} />
      </div>

      {/* 牛熊证前十名表格 */}
      <TopContractsTable
        contracts={dashboardData?.top_contracts || { bull_contracts: [], bear_contracts: [] }}
        loading={loading}
      />

      {/* 市场分析摘要 */}
      {dashboardData && !loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">市场分析摘要</h3>
          <div className="text-sm text-blue-800 space-y-1">
            <p>
              • 当前市场情绪为<strong>{dashboardData.market_sentiment.sentiment_label}</strong>，
              恐惧贪婪指数达到 {dashboardData.market_sentiment.fear_greed_index.toFixed(1)}
            </p>
            <p>
              • 牛熊比率为 {dashboardData.market_sentiment.bull_bear_ratio.toFixed(3)}，
              {dashboardData.market_sentiment.bull_bear_ratio > 1 ? '市场情绪偏多' : '市场情绪偏空'}
            </p>
            <p>
              • 已实现波动率为 {(dashboardData.market_sentiment.realized_volatility * 100).toFixed(2)}%，
              市场波动性{dashboardData.market_sentiment.realized_volatility > 0.3 ? '较高' : '正常'}
            </p>
            <p>
              • RSI 指标为 {dashboardData.market_sentiment.rsi_signal.toFixed(1)}，
              {dashboardData.market_sentiment.rsi_signal > 70 ? '市场可能超买' :
               dashboardData.market_sentiment.rsi_signal < 30 ? '市场可能超卖' : '市场情绪中性'}
            </p>
          </div>
        </div>
      )}

      {/* 数据刷新提示 */}
      {loading && (
        <div className="text-center text-gray-500 py-4">
          <div className="inline-flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2"></div>
            正在更新数据...
          </div>
        </div>
      )}
    </div>
  );
};

export default CBSCDashboard;