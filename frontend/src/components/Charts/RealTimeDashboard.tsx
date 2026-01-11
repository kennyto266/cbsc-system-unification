import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { LineChart } from './chartjs/LineChart';
import { BarChart } from './chartjs/BarChart';
import { PieChart } from './chartjs/PieChart';
import { CandlestickChart } from './plotly/CandlestickChart';
import { RealTimeChart } from './plotly/RealTimeChart';
import { ThreeDChart } from './plotly/ThreeDChart';
import { useChartExport } from './hooks/useChartExport';

// 模拟数据生成函数
const generateMockData = (count: number, min: number, max: number) => {
  return Array.from({ length: count }, (_, i) => ({
    x: i,
    y: Math.random() * (max - min) + min
  }));
};

const generateTimeSeriesData = (hours: number) => {
  const now = new Date();
  return Array.from({ length: hours * 60 }, (_, i) => {
    const time = new Date(now.getTime() - (hours * 60 - i) * 60 * 1000);
    return {
      x: time,
      y: 100 + Math.sin(i / 20) * 20 + Math.random() * 10
    };
  });
};

// 数据流配置
const dataStreams = [
  { id: 'stream1', name: '策略收益', color: '#3b82f6', yaxis: 'y' },
  { id: 'stream2', name: '基准收益', color: '#10b981', yaxis: 'y2' },
  { id: 'stream3', name: '波动率', color: '#f59e0b', yaxis: 'y3' }
];

// Y轴配置
const yAxes = [
  { title: '收益率 (%)', side: 'left', range: [80, 140] },
  { title: '基准 (%)', side: 'right', position: 0.85, range: [80, 140] },
  { title: '波动率 (%)', side: 'right', position: 0.7, range: [0, 30] }
];

export const RealTimeDashboard: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('1d');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const { exportChart } = useChartExport(containerRef);

  // 图表数据
  const [performanceData] = useState(() => [
    {
      label: '时间序列数据',
      data: generateTimeSeriesData(24),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4,
      fill: true
    }
  ]);

  const [comparisonData] = useState(() => [
    {
      label: '策略A',
      data: generateMockData(10, 15, 30),
      backgroundColor: '#3b82f6'
    },
    {
      label: '策略B',
      data: generateMockData(10, 10, 25),
      backgroundColor: '#10b981'
    },
    {
      label: '策略C',
      data: generateMockData(10, 5, 20),
      backgroundColor: '#f59e0b'
    }
  ]);

  const [distributionData] = useState(() => [
    { label: '股票', value: 45, color: '#3b82f6' },
    { label: '债券', value: 25, color: '#10b981' },
    { label: '商品', value: 15, color: '#f59e0b' },
    { label: '现金', value: 10, color: '#8b5cf6' },
    { label: '其他', value: 5, color: '#ec4899' }
  ]);

  const [candlestickData] = useState(() => ({
    x: Array.from({ length: 100 }, (_, i) => {
      const date = new Date();
      date.setMinutes(date.getMinutes() - (100 - i) * 5);
      return date.toISOString();
    }),
    open: Array.from({ length: 100 }, () => 100 + Math.random() * 10),
    high: Array.from({ length: 100 }, () => 100 + Math.random() * 15),
    low: Array.from({ length: 100 }, () => 95 + Math.random() * 10),
    close: Array.from({ length: 100 }, () => 100 + Math.random() * 10),
    volume: Array.from({ length: 100 }, () => Math.random() * 1000000)
  }));

  const [threeDData] = useState(() => [
    {
      name: '收益分布',
      type: 'scatter3d' as const,
      data: Array.from({ length: 200 }, () => ({
        x: Math.random() * 100,
        y: Math.random() * 100,
        z: Math.random() * 100,
        value: Math.random() * 20,
        label: '数据点'
      }))
    }
  ]);

  return (
    <div ref={containerRef} className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 标题和控制栏 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            实时数据可视化仪表板
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            策略性能监控与实时数据分析
          </p>

          {/* 控制按钮 */}
          <div className="flex flex-wrap gap-4 mt-6">
            {/* 时间范围选择 */}
            <div className="flex gap-2">
              {['1h', '1d', '1w', '1m'].map(range => (
                <button
                  key={range}
                  onClick={() => setSelectedTimeRange(range)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedTimeRange === range
                      ? 'bg-blue-500 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>

            {/* 自动刷新 */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                autoRefresh
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              {autoRefresh ? '自动刷新: 开' : '自动刷新: 关'}
            </button>

            {/* 导出 */}
            <button
              onClick={() => exportChart({ filename: 'dashboard' })}
              className="px-4 py-2 rounded-lg font-medium bg-purple-500 text-white hover:bg-purple-600 transition-colors"
            >
              导出仪表板
            </button>
          </div>
        </motion.div>

        {/* 图表网格 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 实时性能曲线 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2"
          >
            <RealTimeChart
              title="实时策略性能"
              subtitle="多策略实时收益对比"
              streams={dataStreams}
              height={400}
              yAxes={yAxes}
              theme="light"
            />
          </motion.div>

          {/* K线图 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <CandlestickChart
              title="价格走势"
              subtitle="5分钟K线图"
              data={candlestickData}
              height={400}
              showVolume={true}
              showMA={true}
            />
          </motion.div>

          {/* 策略对比柱状图 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <BarChart
              title="策略月度收益"
              subtitle="最近10个月收益对比"
              datasets={comparisonData}
              height={400}
              showGrid={true}
              yAxisConfig={{
                label: '收益率 (%)',
                min: 0,
                max: 35
              }}
            />
          </motion.div>

          {/* 资产配置饼图 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
          >
            <PieChart
              title="资产配置"
              subtitle="当前投资组合分布"
              data={distributionData}
              height={400}
              centerText={{
                text: '资产总值',
                subtext: '¥1,234,567'
              }}
            />
          </motion.div>

          {/* 3D风险分析 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <ThreeDChart
              title="风险收益分布"
              subtitle="多维度风险评估"
              series={threeDData}
              height={400}
              axisLabels={{
                x: '收益率',
                y: '波动率',
                z: '夏普比率'
              }}
              showColorbar={true}
            />
          </motion.div>
        </div>

        {/* 状态栏 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-gray-600 dark:text-gray-400">
                  实时连接: 正常
                </span>
              </div>
              <div className="text-gray-600 dark:text-gray-400">
                最后更新: {new Date().toLocaleTimeString('zh-CN')}
              </div>
              <div className="text-gray-600 dark:text-gray-400">
                数据延迟: &lt; 100ms
              </div>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              © 2025 CBSC量化交易系统
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};