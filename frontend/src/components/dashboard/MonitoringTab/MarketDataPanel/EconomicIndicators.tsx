/**
 * EconomicIndicators Component
 * 5 core economic indicators with sparkline charts
 */

import React, { useEffect } from 'react';
import { Card, Col, Row } from 'antd';
import { useAppDispatch, useAppSelector } from '../../../../hooks/redux';
import { fetchAllEconomicIndicators } from '../../../store/slices/economicDataSlice';

interface IndicatorCardProps {
  name: string;
  nameEn: string;
  value: number;
  change: number;
  unit: string;
  trend: number[];
}

const IndicatorCard: React.FC<IndicatorCardProps> = ({
  name,
  nameEn,
  value,
  change,
  unit,
  trend
}) => {
  const generateSparkline = () => {
    if (!trend || trend.length === 0) return null;

    const min = Math.min(...trend);
    const max = Math.max(...trend);
    const range = max - min || 1;
    const points = trend.map((val, i) => {
      const x = (i / (trend.length - 1)) * 100;
      const y = 100 - ((val - min) / range) * 100;
      return `${x},${y}`;
    }).join(' ');

    const color = change >= 0 ? '#10b981' : '#ef4444';

    return (
      <svg width="100%" height="40" viewBox="0 0 100 40" className="indicator-sparkline">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
        />
      </svg>
    );
  };

  return (
    <Card size="small" className="indicator-card">
      <div className="indicator-header">
        <div className="indicator-names">
          <div className="indicator-name">{name}</div>
          <div className="indicator-name-en">{nameEn}</div>
        </div>
        <div className={`indicator-change ${change >= 0 ? 'positive' : 'negative'}`}>
          {change >= 0 ? '+' : ''}{change}%
        </div>
      </div>

      <div className="indicator-value">
        {value}
        <span className="indicator-unit">{unit}</span>
      </div>

      <div className="indicator-sparkline">
        {generateSparkline()}
      </div>
    </Card>
  );
};

export const EconomicIndicators: React.FC = () => {
  const dispatch = useAppDispatch();
  const indicators = useAppSelector((state) => state.economicData.indicators);

  useEffect(() => {
    dispatch(fetchAllEconomicIndicators({
      dateRange: {
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
      }
    }) as any);
  }, [dispatch]);

  // Show mock data if no indicators available
  const mockIndicators = [
    {
      id: '1',
      name: '美國國債收益率',
      nameEn: 'US 10Y Treasury',
      value: 4.25,
      change: 0.15,
      unit: '%',
      trend: [4.0, 4.05, 4.1, 4.08, 4.12, 4.18, 4.25]
    },
    {
      id: '2',
      name: '美元指數',
      nameEn: 'DXY',
      value: 103.5,
      change: -0.3,
      unit: '',
      trend: [104.2, 104.0, 103.8, 103.9, 103.7, 103.6, 103.5]
    },
    {
      id: '3',
      name: 'HIBOR',
      nameEn: 'HIBOR',
      value: 5.23,
      change: 0.05,
      unit: '%',
      trend: [5.1, 5.12, 5.15, 5.18, 5.2, 5.22, 5.23]
    }
  ];

  const displayIndicators = indicators.length > 0 ? indicators.slice(0, 5) : mockIndicators;

  return (
    <Row gutter={[12, 12]}>
      {displayIndicators.map((indicator) => (
        <Col span={24} key={indicator.id}>
          <IndicatorCard
            name={indicator.name}
            nameEn={indicator.nameEn}
            value={indicator.value}
            change={indicator.change}
            unit={indicator.unit}
            trend={indicator.trend || []}
          />
        </Col>
      ))}
    </Row>
  );
};

export default EconomicIndicators;
