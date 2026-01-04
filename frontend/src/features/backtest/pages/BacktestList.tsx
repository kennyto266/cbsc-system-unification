import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Play, Calendar, TrendingUp, TrendingDown, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Button } from 'antd';

interface BacktestRecord {
  id: string;
  name: string;
  strategyName: string;
  status: 'completed' | 'running' | 'failed';
  startDate: string;
  endDate: string;
  return: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
}

interface BacktestListProps {}

const BacktestList: React.FC<BacktestListProps> = () => {
  const navigate = useNavigate();
  const [backtests, setBacktests] = useState<BacktestRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'running' | 'completed' | 'failed'>('all');

  useEffect(() => {
    // TODO: Fetch backtests from API
    const mockBacktests: BacktestRecord[] = [
      {
        id: '1',
        name: '动量策略回测 - 2024Q1',
        strategyName: '动量策略',
        status: 'completed',
        startDate: '2024-01-01',
        endDate: '2024-03-31',
        return: 0.25,
        sharpeRatio: 1.5,
        maxDrawdown: 0.15,
        winRate: 0.6
      },
      {
        id: '2',
        name: '均值回归策略回测',
        strategyName: '均值回归',
        status: 'running',
        startDate: '2024-01-01',
        endDate: '2024-03-31',
        return: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0
      },
      {
        id: '3',
        name: '突破策略回测',
        strategyName: '突破策略',
        status: 'failed',
        startDate: '2024-01-01',
        endDate: '2024-03-31',
        return: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0
      }
    ];
    setBacktests(mockBacktests);
    setLoading(false);
  }, []);

  const handleCreateBacktest = () => {
    navigate('/backtest/new');
  };

  const handleViewReport = (id: string) => {
    navigate(`/backtest/${id}`);
  };

  const filteredBacktests = filter === 'all' 
    ? backtests 
    : backtests.filter(bt => bt.status === filter);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'running':
        return <Clock className="h-4 w-4 text-yellow-600 animate-pulse" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'running': return '运行中';
      case 'failed': return '失败';
      default: return status;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              回测分析
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              查看和管理策略回测结果
            </p>
          </div>
          <Button
            onClick={handleCreateBacktest}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            新建回测
          </Button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            全部
          </button>
          <button
            onClick={() => setFilter('running')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filter === 'running'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            运行中
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filter === 'completed'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            已完成
          </button>
          <button
            onClick={() => setFilter('failed')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              filter === 'failed'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            失败
          </button>
        </div>
      </div>

      {/* Backtest List */}
      <div className="p-6">
        {filteredBacktests.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
            <Calendar className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              暂无回测记录
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              创建您的第一个回测任务来开始分析策略表现
            </p>
            <Button
              onClick={handleCreateBacktest}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="h-4 w-4 mr-2" />
              新建回测
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredBacktests.map((backtest) => (
              <div
                key={backtest.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handleViewReport(backtest.id)}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {backtest.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {backtest.strategyName}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    {getStatusIcon(backtest.status)}
                    <span className="text-xs text-gray-600 dark:text-gray-400 ml-1">
                      {getStatusText(backtest.status)}
                    </span>
                  </div>
                </div>

                {/* Date Range */}
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-4">
                  <Calendar className="h-3 w-3" />
                  <span>{backtest.startDate} 至 {backtest.endDate}</span>
                </div>

                {/* Performance Metrics */}
                {backtest.status === 'completed' && (
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">收益率</p>
                      <p className={`text-lg font-bold flex items-center gap-1 ${
                        backtest.return >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {backtest.return >= 0 ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : (
                          <TrendingDown className="h-4 w-4" />
                        )}
                        {(backtest.return * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">夏普比率</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-white">
                        {backtest.sharpeRatio.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">最大回撤</p>
                      <p className="text-lg font-bold text-red-600">
                        {(backtest.maxDrawdown * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">胜率</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-white">
                        {(backtest.winRate * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                )}

                {backtest.status === 'running' && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        回测运行中...
                      </span>
                    </div>
                  </div>
                )}

                {backtest.status === 'failed' && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-red-600">
                      回测失败，请检查参数配置
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BacktestList;
