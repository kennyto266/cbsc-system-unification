/**
 * 市场情绪指标卡片组件
 * Market Sentiment Indicator Card Component
 */

import React from 'react';
import { MarketSentiment } from '../../types/cbsc';

interface MarketSentimentCardProps {
  sentiment: MarketSentiment;
  loading?: boolean;
}

const MarketSentimentCard: React.FC<MarketSentimentCardProps> = ({ sentiment, loading = false }) => {
  // 根据情绪分数获取颜色
  const getSentimentColor = (score: number): string => {
    if (score >= 75) return 'text-red-600'; // 极度贪婪
    if (score >= 60) return 'text-orange-600'; // 贪婪
    if (score >= 45) return 'text-yellow-600'; // 中性
    if (score >= 25) return 'text-green-600'; // 恐惧
    return 'text-emerald-600'; // 极度恐惧
  };

  // 获取进度条颜色
  const getProgressBarColor = (score: number): string => {
    if (score >= 75) return 'bg-red-500';
    if (score >= 60) return 'bg-orange-500';
    if (score >= 45) return 'bg-yellow-500';
    if (score >= 25) return 'bg-green-500';
    return 'bg-emerald-500';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          <div className="h-3 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">📊</span>
        市场情绪指标
      </h3>

      {/* 恐惧贪婪指数 */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-600">恐惧贪婪指数</span>
          <span className={`text-sm font-bold ${getSentimentColor(sentiment.sentiment_score)}`}>
            {sentiment.sentiment_label}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${getProgressBarColor(sentiment.sentiment_score)}`}
            style={{ width: `${sentiment.sentiment_score}%` }}
          ></div>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {sentiment.fear_greed_index.toFixed(1)} / 100
        </div>
      </div>

      {/* 指标网格 */}
      <div className="grid grid-cols-2 gap-4">
        {/* 牛熊比率 */}
        <div className="bg-gray-50 rounded p-3">
          <div className="text-xs text-gray-500 mb-1">牛熊比率</div>
          <div className="text-lg font-semibold text-gray-800">
            {sentiment.bull_bear_ratio.toFixed(3)}
          </div>
          <div className="text-xs text-gray-400">
            {sentiment.bull_bear_ratio > 1 ? '偏多' : '偏空'}
          </div>
        </div>

        {/* 波动率 */}
        <div className="bg-gray-50 rounded p-3">
          <div className="text-xs text-gray-500 mb-1">已实现波动率</div>
          <div className="text-lg font-semibold text-gray-800">
            {(sentiment.realized_volatility * 100).toFixed(2)}%
          </div>
          <div className="text-xs text-gray-400">
            {sentiment.realized_volatility > 0.3 ? '高' : sentiment.realized_volatility > 0.2 ? '中' : '低'}
          </div>
        </div>

        {/* RSI 信号 */}
        <div className="bg-gray-50 rounded p-3">
          <div className="text-xs text-gray-500 mb-1">RSI 信号</div>
          <div className="text-lg font-semibold text-gray-800">
            {sentiment.rsi_signal.toFixed(1)}
          </div>
          <div className="text-xs text-gray-400">
            {sentiment.rsi_signal > 70 ? '超买' : sentiment.rsi_signal < 30 ? '超卖' : '正常'}
          </div>
        </div>

        {/* 情绪分数 */}
        <div className="bg-gray-50 rounded p-3">
          <div className="text-xs text-gray-500 mb-1">综合评分</div>
          <div className={`text-lg font-semibold ${getSentimentColor(sentiment.sentiment_score)}`}>
            {sentiment.sentiment_score.toFixed(0)}
          </div>
          <div className="text-xs text-gray-400">0-100</div>
        </div>
      </div>

      {/* 更新时间 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-400">
          最后更新: {new Date(sentiment.update_time).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  );
};

export default MarketSentimentCard;