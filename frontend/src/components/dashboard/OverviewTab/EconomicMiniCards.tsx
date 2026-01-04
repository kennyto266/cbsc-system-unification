/**
 * Economic Mini Cards Component
 * Displays 5 economic indicators with sparkline charts
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { selectEconomicData } from '../../../store/slices/economicDataSlice';
import './EconomicMiniCards.css';

// Economic indicator interface
interface EconomicIndicator {
  id: string;
  name: string;
  nameEn: string;
  value: number;
  unit: string;
  change: number;
  trend: number[]; // Sparkline data
  color: string;
  icon: string;
  updatedAt: string;
  isStale: boolean;
}

/**
 * EconomicMiniCards Component
 */
export const EconomicMiniCards: React.FC = () => {
  const navigate = useNavigate();
  const economicData = useSelector(selectEconomicData);

  // Generate sparkline SVG path
  const generateSparklinePath = (data: number[], width: number, height: number): string => {
    if (!data || data.length === 0) return '';

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const stepX = width / (data.length - 1);

    let path = `M 0 ${height - ((data[0] - min) / range) * height}`;

    for (let i = 1; i < data.length; i++) {
      const x = i * stepX;
      const y = height - ((data[i] - min) / range) * height;
      path += ` L ${x} ${y}`;
    }

    return path;
  };

  // Build economic indicators from data
  const indicators: EconomicIndicator[] = useMemo(() => {
    if (!economicData || !economicData.hibor) {
      // Return mock data for demo
      return [
        {
          id: 'hibor',
          name: 'HIBOR利率',
          nameEn: 'HIBOR Rate',
          value: 5.23,
          unit: '%',
          change: 0.12,
          trend: [5.01, 5.05, 5.10, 5.08, 5.15, 5.20, 5.23],
          color: '#10b981',
          icon: '📈',
          updatedAt: new Date().toISOString(),
          isStale: false
        },
        {
          id: 'gdp',
          name: 'GDP增長',
          nameEn: 'GDP Growth',
          value: 3.20,
          unit: '%',
          change: 0.15,
          trend: [2.8, 2.9, 3.0, 3.05, 3.10, 3.15, 3.20],
          color: '#8b5cf6',
          icon: '📊',
          updatedAt: new Date().toISOString(),
          isStale: false
        },
        {
          id: 'pmi',
          name: 'PMI指數',
          nameEn: 'PMI Index',
          value: 50.10,
          unit: '',
          change: -0.3,
          trend: [51.2, 51.0, 50.8, 50.6, 50.4, 50.2, 50.1],
          color: '#f59e0b',
          icon: '📉',
          updatedAt: new Date().toISOString(),
          isStale: false
        },
        {
          id: 'visitors',
          name: '訪港旅客',
          nameEn: 'Visitor Arrivals',
          value: 3525000,
          unit: ' 人次',
          change: 2.5,
          trend: [3200000, 3300000, 3350000, 3400000, 3450000, 3500000, 3525000],
          color: '#3b82f6',
          icon: '✈️',
          updatedAt: new Date().toISOString(),
          isStale: false
        },
        {
          id: 'unemployment',
          name: '失業率',
          nameEn: 'Unemployment Rate',
          value: 3.00,
          unit: '%',
          change: -0.1,
          trend: [3.15, 3.12, 3.10, 3.08, 3.05, 3.02, 3.00],
          color: '#ef4444',
          icon: '📉',
          updatedAt: new Date().toISOString(),
          isStale: false
        }
      ];
    }

    // Extract from real data
    const hiborData = economicData.hibor?.[0];
    const gdpData = economicData.gdp?.[0];
    const pmiData = economicData.pmi?.[0];
    const visitorsData = economicData.visitors?.[0];
    const unemploymentData = economicData.unemployment?.[0];

    return [
      {
        id: 'hibor',
        name: 'HIBOR利率',
        nameEn: 'HIBOR Rate',
        value: hiborData?.rate || 5.23,
        unit: '%',
        change: 0.12,
        trend: [5.01, 5.05, 5.10, 5.08, 5.15, 5.20, 5.23],
        color: '#10b981',
        icon: '📈',
        updatedAt: hiborData?.date || new Date().toISOString(),
        isStale: false
      },
      {
        id: 'gdp',
        name: 'GDP增長',
        nameEn: 'GDP Growth',
        value: gdpData?.gdp_growth || 3.20,
        unit: '%',
        change: 0.15,
        trend: [2.8, 2.9, 3.0, 3.05, 3.10, 3.15, 3.20],
        color: '#8b5cf6',
        icon: '📊',
        updatedAt: gdpData?.quarter || new Date().toISOString(),
        isStale: false
      },
      {
        id: 'pmi',
        name: 'PMI指數',
        nameEn: 'PMI Index',
        value: pmiData?.pmi || 50.10,
        unit: '',
        change: -0.3,
        trend: [51.2, 51.0, 50.8, 50.6, 50.4, 50.2, 50.1],
        color: '#f59e0b',
        icon: '📉',
        updatedAt: pmiData?.month || new Date().toISOString(),
        isStale: false
      },
      {
        id: 'visitors',
        name: '訪港旅客',
        nameEn: 'Visitor Arrivals',
        value: visitorsData?.visitors || 3525000,
        unit: ' 人次',
        change: 2.5,
        trend: [3200000, 3300000, 3350000, 3400000, 3450000, 3500000, 3525000],
        color: '#3b82f6',
        icon: '✈️',
        updatedAt: visitorsData?.month || new Date().toISOString(),
        isStale: false
      },
      {
        id: 'unemployment',
        name: '失業率',
        nameEn: 'Unemployment Rate',
        value: unemploymentData?.rate || 3.00,
        unit: '%',
        change: -0.1,
        trend: [3.15, 3.12, 3.10, 3.08, 3.05, 3.02, 3.00],
        color: '#ef4444',
        icon: '📉',
        updatedAt: unemploymentData?.month || new Date().toISOString(),
        isStale: false
      }
    ];
  }, [economicData]);

  // Handle card click
  const handleCardClick = (indicatorId: string) => {
    // Navigate to strategy generator with pre-selected indicator
    navigate('/strategies/generator', {
      state: { focusIndicator: indicatorId }
    });
  };

  // Format value
  const formatValue = (value: number, unit: string): string => {
    if (unit === '人次') {
      return new Intl.NumberFormat('zh-HK', { notation: 'compact', compactDisplay: 'short' }).format(value);
    }
    return `${value.toFixed(2)}${unit}`;
  };

  return (
    <div className="economic-mini-cards-container">
      <div className="economic-mini-cards-header">
        <h3 className="economic-mini-cards-title">經濟數據監控</h3>
        <button
          className="economic-mini-cards-refresh"
          onClick={() => navigate('/strategies/generator')}
        >
          查看詳情 →
        </button>
      </div>

      <div className="economic-mini-cards-grid">
        {indicators.map((indicator, index) => (
          <motion.div
            key={indicator.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="economic-mini-card"
            onClick={() => handleCardClick(indicator.id)}
            style={{
              borderLeftColor: indicator.color,
              borderLeftWidth: '3px'
            }}
          >
            {/* Card Header */}
            <div className="economic-mini-card-header">
              <div className="economic-mini-card-title">
                <span className="indicator-icon">{indicator.icon}</span>
                <span className="indicator-name">{indicator.name}</span>
              </div>
              <div className="economic-mini-card-change">
                {indicator.change > 0 ? (
                  <TrendingUp size={14} className="trend-up" />
                ) : indicator.change < 0 ? (
                  <TrendingDown size={14} className="trend-down" />
                ) : (
                  <Minus size={14} className="trend-neutral" />
                )}
                <span className={indicator.change >= 0 ? 'trend-up' : 'trend-down'}>
                  {indicator.change >= 0 ? '+' : ''}{indicator.change.toFixed(2)}%
                </span>
              </div>
            </div>

            {/* Card Value */}
            <div className="economic-mini-card-value">
              {formatValue(indicator.value, indicator.unit)}
            </div>

            {/* Sparkline Chart */}
            <div className="economic-mini-card-sparkline">
              <svg
                width="100%"
                height="40"
                viewBox="0 0 100 40"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient
                    id={`gradient-${indicator.id}`}
                    x1="0%"
                    y1="0%"
                    x2="0%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      style={{
                        stopColor: indicator.color,
                        stopOpacity: 0.3
                      }}
                    />
                    <stop
                      offset="100%"
                      style={{
                        stopColor: indicator.color,
                        stopOpacity: 0
                      }}
                    />
                  </linearGradient>
                </defs>
                <path
                  d={generateSparklinePath(indicator.trend, 100, 40)}
                  fill="none"
                  stroke={indicator.color}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d={generateSparklinePath(indicator.trend, 100, 40)}
                  fill={`url(#gradient-${indicator.id})`}
                  stroke="none"
                />
              </svg>
            </div>

            {/* Card Footer */}
            <div className="economic-mini-card-footer">
              <span className="indicator-name-en">{indicator.nameEn}</span>
              {indicator.isStale && (
                <span className="stale-badge">數據過期</span>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default EconomicMiniCards;
