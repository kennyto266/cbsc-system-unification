import React from 'react'
import { Card, Progress, Row, Col, Statistic } from 'antd'

const SystemHealth: React.FC = () => {
  return (
    <Card title="系统健康">
      <Row gutter={16}>
        <Col span={12}>
          <Statistic title="CPU使用率" value={45} suffix="%" />
        </Col>
        <Col span={12}>
          <Statistic title="内存使用率" value={67} suffix="%" />
        </Col>
      </Row>
      <Progress percent={85} status="active" style={{ marginTop: '16px' }} />
    </Card>
  )
}

export default SystemHealth
