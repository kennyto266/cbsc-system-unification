/**
 * 市场情绪趋势图表组件
 * Market Sentiment Trend Chart Component
 */

import React, { useState, useEffect, useRef } from 'react';
import { HistoricalDataPoint } from '../../types/cbsc';
import { getHistoricalData } from '../../services/cbscService';

interface SentimentTrendChartProps {
  loading?: boolean;
}

const SentimentTrendChart: React.FC<SentimentTrendChartProps> = ({ loading = false }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>('fear_greed_index');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取历史数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getHistoricalData(30, selectedMetric);
        setHistoricalData(data.historical_data);
      } catch (err) {
        console.error('Error fetching historical data:', err);
        setError('无法加载历史数据');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [selectedMetric]);

  // 绘制图表
  useEffect(() => {
    if (!canvasRef.current || historicalData.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // 图表配置
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = canvas.width - padding.left - padding.right;
    const chartHeight = canvas.height - padding.top - padding.bottom;

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 获取数据范围
    const values = historicalData.map(d => d[selectedMetric as keyof HistoricalDataPoint] || 0);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = maxValue - minValue || 1;

    // 绘制网格线
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;

    // 水平网格线
    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight * i) / 5;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();

      // Y轴标签
      const value = maxValue - (valueRange * i) / 5;
      ctx.fillStyle = '#6b7280';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(1), padding.left - 10, y + 4);
    }

    // 垂直网格线
    const dayInterval = Math.ceil(historicalData.length / 6);
    for (let i = 0; i < historicalData.length; i += dayInterval) {
      const x = padding.left + (chartWidth * i) / (historicalData.length - 1);
      ctx.beginPath();
      ctx.moveTo(x, padding.top);
      ctx.lineTo(x, padding.top + chartHeight);
      ctx.stroke();

      // X轴标签
      const date = new Date(historicalData[i].date);
      ctx.fillStyle = '#6b7280';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.save();
      ctx.translate(x, padding.top + chartHeight + 20);
      ctx.rotate(-Math.PI / 4);
      ctx.fillText(`${date.getMonth() + 1}/${date.getDate()}`, 0, 0);
      ctx.restore();
    }

    // 绘制数据线
    ctx.strokeStyle = selectedMetric === 'fear_greed_index' ? '#ef4444' : '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();

    historicalData.forEach((point, index) => {
      const x = padding.left + (chartWidth * index) / (historicalData.length - 1);
      const y = padding.top + chartHeight * ((maxValue - (point[selectedMetric as keyof HistoricalDataPoint] || 0)) / valueRange);

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // 绘制数据点
    historicalData.forEach((point, index) => {
      const x = padding.left + (chartWidth * index) / (historicalData.length - 1);
      const y = padding.top + chartHeight * ((maxValue - (point[selectedMetric as keyof HistoricalDataPoint] || 0)) / valueRange);

      ctx.fillStyle = selectedMetric === 'fear_greed_index' ? '#ef4444' : '#3b82f6';
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // 绘制图表标题
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    const title = selectedMetric === 'fear_greed_index' ? '恐惧贪婪指数趋势' :
                  selectedMetric === 'bull_bear_ratio' ? '牛熊比率趋势' :
                  selectedMetric === 'realized_volatility' ? '波动率趋势' : '成交量趋势';
    ctx.fillText(title, canvas.width / 2, 15);

  }, [historicalData, selectedMetric]);

  if (loading || isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500 py-8">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center">
          <span className="mr-2">📈</span>
          市场情绪趋势
        </h3>

        {/* 指标选择器 */}
        <select
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="fear_greed_index">恐惧贪婪指数</option>
          <option value="bull_bear_ratio">牛熊比率</option>
          <option value="realized_volatility">波动率</option>
          <option value="volume">成交量</option>
        </select>
      </div>

      {/* 图表容器 */}
      <div className="relative" style={{ height: '300px' }}>
        <canvas
          ref={canvasRef}
          className="w-full h-full"
          style={{ display: 'block' }}
        />
      </div>

      {/* 图例 */}
      <div className="mt-4 flex justify-center space-x-6 text-sm text-gray-600">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${
            selectedMetric === 'fear_greed_index' ? 'bg-red-500' : 'bg-blue-500'
          }`}></div>
          <span>{selectedMetric === 'fear_greed_index' ? '恐惧贪婪指数' :
                  selectedMetric === 'bull_bear_ratio' ? '牛熊比率' :
                  selectedMetric === 'realized_volatility' ? '已实现波动率' : '成交量'}</span>
        </div>
        <div className="text-gray-400">
          最近 30 天数据
        </div>
      </div>
    </div>
  );
};

export default SentimentTrendChart;