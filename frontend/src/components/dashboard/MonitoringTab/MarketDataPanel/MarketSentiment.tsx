/**
 * MarketSentiment Component
 * VIX and fund flow indicators
 */

import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

export const MarketSentiment: React.FC = () => {
  return (
    <Row gutter={[12, 12]}>
      <Col span={24}>
        <Card size="small">
          <Statistic
            title="VIX 恐慌指數"
            value={18.5}
            precision={2}
            prefix={<Activity size={16} />}
            valueStyle={{ color: '#10b981' }}
            suffix={
              <span style={{ fontSize: 14, color: '#10b981' }}>
                (-2.3%)
              </span>
            }
          />
        </Card>
      </Col>

      <Col span={12}>
        <Card size="small">
          <Statistic
            title="資金流入"
            value={125.6}
            suffix="M"
            prefix={<TrendingUp size={14} />}
            valueStyle={{ fontSize: 18, color: '#10b981' }}
          />
        </Card>
      </Col>

      <Col span={12}>
        <Card size="small">
          <Statistic
            title="資金流出"
            value={98.2}
            suffix="M"
            prefix={<TrendingDown size={14} />}
            valueStyle={{ fontSize: 18, color: '#ef4444' }}
          />
        </Card>
      </Col>
    </Row>
  );
};

export default MarketSentiment;
