import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Calendar, Settings, TrendingUp } from 'lucide-react';
import { Button } from 'antd';

interface BacktestConfig {
  name: string;
  strategyId: string;
  symbol: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  commission: number;
  slippage: number;
}

interface BacktestCreateProps {}

const BacktestCreate: React.FC<BacktestCreateProps> = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<BacktestConfig>({
    name: '',
    strategyId: '',
    symbol: '',
    startDate: '',
    endDate: '',
    initialCapital: 100000,
    commission: 0.001,
    slippage: 0.001
  });

  const mockStrategies = [
    { id: '1', name: '动量策略' },
    { id: '2', name: '均值回归策略' },
    { id: '3', name: '突破策略' }
  ];

  const quickRanges = [
    { label: '最近一周', days: 7 },
    { label: '最近一月', days: 30 },
    { label: '最近三月', days: 90 },
    { label: '最近半年', days: 180 },
    { label: '最近一年', days: 365 }
  ];

  const handleChange = (field: keyof BacktestConfig, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleQuickRange = (days: number) => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    setFormData(prev => ({
      ...prev,
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // TODO: Create backtest via API
      await new Promise(resolve => setTimeout(resolve, 1000));
      navigate('/backtest');
    } catch (error) {
      console.error('Failed to create backtest:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/backtest')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              创建回测
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              配置回测参数并运行策略回测
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="p-6 max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Configuration */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              基本配置
            </h2>
            
            <div className="space-y-4">
              {/* Backtest Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  回测名称 <span className="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入回测名称"
                  required
                />
              </div>

              {/* Strategy Selection */}
              <div>
                <label htmlFor="strategyId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  选择策略 <span className="text-red-500">*</span>
                </label>
                <select
                  id="strategyId"
                  value={formData.strategyId}
                  onChange={(e) => handleChange('strategyId', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">请选择策略</option>
                  {mockStrategies.map(strategy => (
                    <option key={strategy.id} value={strategy.id}>{strategy.name}</option>
                  ))}
                </select>
              </div>

              {/* Symbol */}
              <div>
                <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  交易标的 <span className="text-red-500">*</span>
                </label>
                <input
                  id="symbol"
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => handleChange('symbol', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入股票代码或标的"
                  required
                />
              </div>
            </div>
          </div>

          {/* Date Range */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                回测时间范围
              </div>
            </h2>
            
            {/* Quick Range Buttons */}
            <div className="flex flex-wrap gap-2 mb-4">
              {quickRanges.map((range, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleQuickRange(range.days)}
                  className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  {range.label}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Start Date */}
              <div>
                <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  开始日期 <span className="text-red-500">*</span>
                </label>
                <input
                  id="startDate"
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => handleChange('startDate', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* End Date */}
              <div>
                <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  结束日期 <span className="text-red-500">*</span>
                </label>
                <input
                  id="endDate"
                  type="date"
                  value={formData.endDate}
                  onChange={(e) => handleChange('endDate', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* Capital and Costs */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                资金与成本设置
              </div>
            </h2>
            
            <div className="space-y-4">
              {/* Initial Capital */}
              <div>
                <label htmlFor="initialCapital" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  初始资金 (¥) <span className="text-red-500">*</span>
                </label>
                <input
                  id="initialCapital"
                  type="number"
                  value={formData.initialCapital}
                  onChange={(e) => handleChange('initialCapital', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Commission */}
              <div>
                <label htmlFor="commission" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  佣金率 (%)
                </label>
                <input
                  id="commission"
                  type="number"
                  step="0.001"
                  value={(formData.commission * 100).toFixed(3)}
                  onChange={(e) => handleChange('commission', parseFloat(e.target.value) / 100)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Slippage */}
              <div>
                <label htmlFor="slippage" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  滑点 (%)
                </label>
                <input
                  id="slippage"
                  type="number"
                  step="0.001"
                  value={(formData.slippage * 100).toFixed(3)}
                  onChange={(e) => handleChange('slippage', parseFloat(e.target.value) / 100)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              回测配置摘要
            </h3>
            <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <dt className="text-xs text-gray-600 dark:text-gray-400">初始资金</dt>
                <dd className="text-sm font-bold text-gray-900 dark:text-white">
                  ¥{formData.initialCapital.toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-gray-600 dark:text-gray-400">交易标的</dt>
                <dd className="text-sm font-bold text-gray-900 dark:text-white">
                  {formData.symbol || '-'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-gray-600 dark:text-gray-400">时间范围</dt>
                <dd className="text-sm font-bold text-gray-900 dark:text-white">
                  {formData.startDate && formData.endDate 
                    ? `${formData.startDate} ~ ${formData.endDate}`
                    : '-'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-gray-600 dark:text-gray-400">总成本</dt>
                <dd className="text-sm font-bold text-gray-900 dark:text-white">
                  {((formData.commission + formData.slippage) * 100).toFixed(2)}%
                </dd>
              </div>
            </dl>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/backtest')}
              disabled={loading}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  创建中...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  创建并运行回测
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BacktestCreate;
