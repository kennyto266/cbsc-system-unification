import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, X } from 'lucide-react';
import { Button } from 'antd';

interface StrategyCreateProps {}

interface StrategyForm {
  name: string;
  type: string;
  symbol: string;
  timeframe: string;
  riskLevel: string;
  description: string;
  parameters: {
    [key: string]: string | number | boolean;
  };
}

const StrategyCreate: React.FC<StrategyCreateProps> = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<StrategyForm>({
    name: '',
    type: 'momentum',
    symbol: '',
    timeframe: '1d',
    riskLevel: 'medium',
    description: '',
    parameters: {
      lookbackPeriod: 20,
      threshold: 0.02,
      stopLoss: 0.05,
      takeProfit: 0.1
    }
  });

  const strategyTypes = [
    { value: 'momentum', label: '动量策略' },
    { value: 'reversal', label: '均值回归' },
    { value: 'breakout', label: '突破策略' },
    { value: 'custom', label: '自定义策略' }
  ];

  const timeframes = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '1h', label: '1小时' },
    { value: '1d', label: '日线' },
    { value: '1w', label: '周线' }
  ];

  const riskLevels = [
    { value: 'low', label: '低风险' },
    { value: 'medium', label: '中等风险' },
    { value: 'high', label: '高风险' }
  ];

  const handleChange = (field: keyof StrategyForm, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleParameterChange = (key: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [key]: value
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // TODO: Create strategy via API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Navigate to strategy list
      navigate('/strategies');
    } catch (error) {
      console.error('Failed to create strategy:', error);
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
            onClick={() => navigate('/strategies')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              创建新策略
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              配置并启动新的交易策略
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="p-6 max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              基本信息
            </h2>
            
            <div className="space-y-4">
              {/* Strategy Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  策略名称 <span className="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入策略名称"
                  required
                />
              </div>

              {/* Strategy Type */}
              <div>
                <label htmlFor="type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  策略类型 <span className="text-red-500">*</span>
                </label>
                <select
                  id="type"
                  value={formData.type}
                  onChange={(e) => handleChange('type', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {strategyTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
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

              {/* Timeframe */}
              <div>
                <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  时间周期 <span className="text-red-500">*</span>
                </label>
                <select
                  id="timeframe"
                  value={formData.timeframe}
                  onChange={(e) => handleChange('timeframe', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {timeframes.map(tf => (
                    <option key={tf.value} value={tf.value}>{tf.label}</option>
                  ))}
                </select>
              </div>

              {/* Risk Level */}
              <div>
                <label htmlFor="riskLevel" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  风险等级 <span className="text-red-500">*</span>
                </label>
                <select
                  id="riskLevel"
                  value={formData.riskLevel}
                  onChange={(e) => handleChange('riskLevel', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {riskLevels.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  策略描述
                </label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="描述策略逻辑和特点"
                />
              </div>
            </div>
          </div>

          {/* Parameters */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              策略参数
            </h2>
            
            <div className="space-y-4">
              {/* Lookback Period */}
              <div>
                <label htmlFor="lookbackPeriod" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  回溯周期
                </label>
                <input
                  id="lookbackPeriod"
                  type="number"
                  value={formData.parameters.lookbackPeriod}
                  onChange={(e) => handleParameterChange('lookbackPeriod', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Threshold */}
              <div>
                <label htmlFor="threshold" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  触发阈值
                </label>
                <input
                  id="threshold"
                  type="number"
                  step="0.01"
                  value={formData.parameters.threshold}
                  onChange={(e) => handleParameterChange('threshold', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Stop Loss */}
              <div>
                <label htmlFor="stopLoss" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  止损比例 (%)
                </label>
                <input
                  id="stopLoss"
                  type="number"
                  step="0.01"
                  value={(formData.parameters.stopLoss as number) * 100}
                  onChange={(e) => handleParameterChange('stopLoss', parseFloat(e.target.value) / 100)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Take Profit */}
              <div>
                <label htmlFor="takeProfit" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  止盈比例 (%)
                </label>
                <input
                  id="takeProfit"
                  type="number"
                  step="0.01"
                  value={(formData.parameters.takeProfit as number) * 100}
                  onChange={(e) => handleParameterChange('takeProfit', parseFloat(e.target.value) / 100)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/strategies')}
              disabled={loading}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? '创建中...' : '创建策略'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StrategyCreate;
