import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  BarChart3,
  Users
} from 'lucide-react';
import { PerformanceChart, RealTimeChart } from '../../../shared/components/charts';

interface DashboardPageProps {}

const DashboardPage: React.FC<DashboardPageProps> = () => {
  // Mock data source for real-time chart
  const mockDataSource = async (): Promise<number> => {
    return Math.random() * 100;
  };

  const stats = [
    {
      title: '总资产',
      value: '¥1,234,567',
      change: '+12.5%',
      positive: true,
      icon: DollarSign
    },
    {
      title: '今日收益',
      value: '+¥12,345',
      change: '+8.3%',
      positive: true,
      icon: TrendingUp
    },
    {
      title: '活跃策略',
      value: '8',
      change: '+2',
      positive: true,
      icon: Activity
    },
    {
      title: '总收益率',
      value: '23.5%',
      change: '+2.1%',
      positive: true,
      icon: BarChart3
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Page Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          仪表板
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          欢迎回来，这是您的策略概览
        </p>
      </div>

      {/* Main Content */}
      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                    {stat.value}
                  </p>
                  <p className={`text-sm mt-2 ${
                    stat.positive ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.change}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${
                  stat.positive
                    ? 'bg-green-100 dark:bg-green-900/20'
                    : 'bg-red-100 dark:bg-red-900/20'
                }`}>
                  <stat.icon className={`h-6 w-6 ${
                    stat.positive ? 'text-green-600' : 'text-red-600'
                  }`} />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              策略绩效
            </h2>
            <PerformanceChart height={280} showBenchmark={true} />
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              实时监控
            </h2>
            <RealTimeChart
              title="实时价格"
              dataSource={mockDataSource}
              updateInterval={2000}
              height={280}
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            最近活动
          </h2>
          <div className="space-y-4">
            {[
              { action: '策略 "动量策略" 已启动', time: '5分钟前', type: 'success' },
              { action: '策略 "均值回归" 暂停运行', time: '15分钟前', type: 'warning' },
              { action: '回测任务完成', time: '1小时前', type: 'info' },
              { action: '新策略 "突破策略" 创建', time: '2小时前', type: 'info' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-3 px-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.type === 'success' ? 'bg-green-500' :
                    activity.type === 'warning' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`} />
                  <span className="text-sm text-gray-900 dark:text-white">
                    {activity.action}
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {activity.time}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
