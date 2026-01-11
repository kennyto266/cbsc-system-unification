'use client';

import React, { useState, useEffect } from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { TrendingUpIcon, TrendingDownIcon, MinusIcon } from 'lucide-react';

interface MarketSignal {
  type: string;
  signal: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  description: string;
}

interface MarketRegime {
  state: 'bull' | 'bear' | 'ranging' | 'volatile';
  confidence: number;
  signals: MarketSignal[];
}

interface MarketRegimeIndicatorProps {
  className?: string;
}

export default function MarketRegimeIndicator({ className }: MarketRegimeIndicatorProps) {
  const [regime, setRegime] = useState<MarketRegime | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMarketRegime();
    const interval = setInterval(fetchMarketRegime, 60000); // 每分鐘更新
    return () => clearInterval(interval);
  }, []);

  const fetchMarketRegime = async () => {
    try {
      // 模擬市場狀態數據
      // 實際應用中應該從後端 API 獲取
      const states: ('bull' | 'bear' | 'ranging' | 'volatile')[] = ['bull', 'bear', 'ranging', 'volatile'];
      const randomState = states[Math.floor(Math.random() * states.length)];

      const signals: MarketSignal[] = [
        {
          type: 'HIBOR',
          signal: randomState === 'bear' ? 'bearish' : randomState === 'bull' ? 'bullish' : 'neutral',
          strength: 70 + Math.random() * 30,
          description: '香港銀行同業拆借利率趨勢'
        },
        {
          type: '流動性',
          signal: randomState === 'bear' ? 'bearish' : 'bullish',
          strength: 65 + Math.random() * 35,
          description: '市場流動性指標'
        },
        {
          type: '貨幣基礎',
          signal: 'neutral',
          strength: 50 + Math.random() * 20,
          description: '貨幣基礎變化率'
        },
        {
          type: '技術指標',
          signal: randomState === 'bear' ? 'bearish' : randomState === 'bull' ? 'bullish' : 'neutral',
          strength: 60 + Math.random() * 40,
          description: '綜合技術指標信號'
        }
      ];

      setRegime({
        state: randomState,
        confidence: 75 + Math.random() * 20,
        signals
      });
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch market regime:', error);
      setLoading(false);
    }
  };

  const getRegimeInfo = (state: string) => {
    switch (state) {
      case 'bull':
        return {
          label: '牛市',
          color: 'text-green-600',
          bg: 'bg-green-100',
          icon: TrendingUpIcon,
          description: '市場呈現上升趨勢，投資信心強烈'
        };
      case 'bear':
        return {
          label: '熊市',
          color: 'text-red-600',
          bg: 'bg-red-100',
          icon: TrendingDownIcon,
          description: '市場呈現下降趨勢，風險偏好降低'
        };
      case 'ranging':
        return {
          label: '震盤',
          color: 'text-yellow-600',
          bg: 'bg-yellow-100',
          icon: MinusIcon,
          description: '市場缺乏明確方向，價格在一定區間內波動'
        };
      case 'volatile':
        return {
          label: '高波動',
          color: 'text-purple-600',
          bg: 'bg-purple-100',
          icon: TrendingUpIcon,
          description: '市場波動率顯著增加，價格波動劇烈'
        };
      default:
        return {
          label: '未知',
          color: 'text-gray-600',
          bg: 'bg-gray-100',
          icon: MinusIcon,
          description: '市場狀態不確定'
        };
    }
  };

  const getSignalIcon = (signal: 'bullish' | 'bearish' | 'neutral') => {
    switch (signal) {
      case 'bullish':
        return <TrendingUpIcon className="w-4 h-4 text-green-500" />;
      case 'bearish':
        return <TrendingDownIcon className="w-4 h-4 text-red-500" />;
      default:
        return <MinusIcon className="w-4 h-4 text-gray-500" />;
    }
  };

  if (loading || !regime) {
    return (
      <SquareCard className={className}>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              <div className="h-3 bg-gray-200 rounded w-full"></div>
              <div className="h-3 bg-gray-200 rounded w-full"></div>
            </div>
          </div>
        </div>
      </SquareCard>
    );
  }

  const regimeInfo = getRegimeInfo(regime.state);
  const Icon = regimeInfo.icon;

  return (
    <SquareCard className={className}>
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">市場狀態</h3>
      </div>
      <div className="p-6">
        {/* 主要狀態指示器 */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3">
              <Icon className={`w-8 h-8 ${regimeInfo.color}`} />
              <div>
                <h4 className={`text-xl font-semibold ${regimeInfo.color}`}>
                  {regimeInfo.label}
                </h4>
                <p className="text-sm text-gray-500">{regimeInfo.description}</p>
              </div>
            </div>
            <SquareBadge status="active" size="sm" className={regimeInfo.bg}>
              <span className={regimeInfo.color}>信心度: {regime.confidence.toFixed(1)}%</span>
            </SquareBadge>
          </div>

          {/* 信心度進度條 */}
          <div className="mt-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>信心度</span>
              <span>{regime.confidence.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  regime.state === 'bull' ? 'bg-green-600' :
                  regime.state === 'bear' ? 'bg-red-600' :
                  regime.state === 'ranging' ? 'bg-yellow-600' : 'bg-purple-600'
                }`}
                style={{ width: `${regime.confidence}%` }}
              />
            </div>
          </div>
        </div>

        {/* 信號詳細列表 */}
        <div className="space-y-3">
          <h5 className="text-sm font-medium text-gray-700">指標信號</h5>
          <div className="space-y-2">
            {regime.signals.map((signal, index) => (
              <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  {getSignalIcon(signal.signal)}
                  <span className="text-sm font-medium text-gray-900">{signal.type}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-xs text-gray-500">{signal.description}</span>
                  <span className={`text-sm font-semibold ${
                    signal.signal === 'bullish' ? 'text-green-600' :
                    signal.signal === 'bearish' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {signal.strength.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 更新時間 */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            最後更新：{new Date().toLocaleString('zh-TW')}
          </p>
        </div>
      </div>
    </SquareCard>
  );
}