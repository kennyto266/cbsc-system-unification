import React from 'react'
import { Card, Row, Col } from 'antd'

const MarketOverview: React.FC = () => {
  return (
    <Card title="市场概览">
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <div style={{ textAlign: 'center' }}>
            <div>📈</div>
            <div>市场趋势</div>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ textAlign: 'center' }}>
            <div>💰</div>
            <div>资金流动</div>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ textAlign: 'center' }}>
            <div>⚡</div>
            <div>交易活跃度</div>
          </div>
        </Col>
      </Row>
    </Card>
  )
}

export default MarketOverview
