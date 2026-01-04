import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Pause, Edit, Trash2, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { Button } from 'antd';
import { StrategyData, StrategyStatus } from '../types';
import { PerformanceChart } from '../../../shared/components/charts';

interface StrategyDetailProps {}

const StrategyDetail: React.FC<StrategyDetailProps> = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [strategy, setStrategy] = useState<StrategyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    // TODO: Fetch strategy from API
    // Mock data for now
    const mockStrategy: StrategyData = {
      id: id || '1',
      name: '动量策略',
      isActive: true,
      status: 'active',
      lastUpdated: new Date().toISOString(),
      performance: {
        sharpeRatio: 1.5,
        maxDrawdown: 0.15,
        totalReturn: 0.25,
        winRate: 0.6
      }
    };
    
    setStrategy(mockStrategy);
    setIsActive(mockStrategy.isActive);
    setLoading(false);
  }, [id]);

  const handleToggleStatus = () => {
    // TODO: Update strategy status via API
    setIsActive(!isActive);
  };

  const handleEdit = () => {
    navigate(`/strategies/${id}/edit`);
  };

  const handleDelete = () => {
    if (window.confirm('确定要删除此策略吗？')) {
      // TODO: Delete strategy via API
      navigate('/strategies');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            策略不存在
          </h2>
          <Button onClick={() => navigate('/strategies')}>
            返回策略列表
          </Button>
        </div>
      </div>
    );
  }

  const stats = [
    { label: '夏普比率', value: strategy.performance?.sharpeRatio.toFixed(2) || '-', icon: TrendingUp },
    { label: '最大回撤', value: strategy.performance ? `${(strategy.performance.maxDrawdown * 100).toFixed(1)}%` : '-', icon: TrendingDown },
    { label: '总收益率', value: strategy.performance ? `${(strategy.performance.totalReturn * 100).toFixed(1)}%` : '-', icon: Activity },
    { label: '胜率', value: strategy.performance ? `${(strategy.performance.winRate * 100).toFixed(1)}%` : '-', icon: TrendingUp }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              type="text"
              icon={<ArrowLeft className="h-5 w-5" />}
              onClick={() => navigate('/strategies')}
            />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {strategy.name}
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                策略 ID: {strategy.id}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              type={isActive ? 'primary' : 'primary'}
              danger={isActive}
              onClick={handleToggleStatus}
              className={isActive ? '' : 'bg-green-600'}
              style={isActive ? {} : { backgroundColor: '#16a34a', borderColor: '#16a34a' }}
            >
              {isActive ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  停止
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  启动
                </>
              )}
            </Button>
            <Button
              onClick={handleEdit}
            >
              <Edit className="h-4 w-4 mr-2" />
              编辑
            </Button>
            <Button
              danger
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              删除
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Status Banner */}
        <div className={`px-4 py-3 rounded-lg ${
          strategy.status === 'active'
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
            : strategy.status === 'inactive'
            ? 'bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
            : strategy.status === 'paused'
            ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
        }`}>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              strategy.status === 'active' ? 'bg-green-500' :
              strategy.status === 'inactive' ? 'bg-gray-400' :
              strategy.status === 'paused' ? 'bg-yellow-500' :
              'bg-red-500'
            }`} />
            <span className={`text-sm font-medium ${
              strategy.status === 'active' ? 'text-green-700 dark:text-green-300' :
              strategy.status === 'inactive' ? 'text-gray-700 dark:text-gray-300' :
              strategy.status === 'paused' ? 'text-yellow-700 dark:text-yellow-300' :
              'text-red-700 dark:text-red-300'
            }`}>
              状态: {strategy.status === 'active' ? '运行中' :
                     strategy.status === 'inactive' ? '未激活' :
                     strategy.status === 'paused' ? '已暂停' : '已停止'}
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-400 ml-auto">
              最后更新: {strategy.lastUpdated ? new Date(strategy.lastUpdated).toLocaleString('zh-CN') : '-'}
            </span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{stat.value}</p>
                </div>
                <stat.icon className="h-8 w-8 text-blue-600" />
              </div>
            </div>
          ))}
        </div>

        {/* Performance Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            策略绩效
          </h2>
          <PerformanceChart height={320} showBenchmark={true} />
        </div>

        {/* Strategy Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              策略配置
            </h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600 dark:text-gray-400">策略类型</dt>
                <dd className="text-sm font-medium text-gray-900 dark:text-white">动量策略</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600 dark:text-gray-400">交易品种</dt>
                <dd className="text-sm font-medium text-gray-900 dark:text-white">股票</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600 dark:text-gray-400">时间周期</dt>
                <dd className="text-sm font-medium text-gray-900 dark:text-white">日线</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600 dark:text-gray-400">风险等级</dt>
                <dd className="text-sm font-medium text-gray-900 dark:text-white">中等</dd>
              </div>
            </dl>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              运行记录
            </h2>
            <div className="space-y-3">
              {[
                { action: '策略启动', time: '5分钟前', status: 'success' },
                { action: '信号生成', time: '10分钟前', status: 'info' },
                { action: '交易执行', time: '15分钟前', status: 'info' },
                { action: '风控检查', time: '20分钟前', status: 'success' },
              ].map((record, index) => (
                <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-sm text-gray-900 dark:text-white">{record.action}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{record.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyDetail;
