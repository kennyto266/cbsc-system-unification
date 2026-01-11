import React from 'react'
import { Card, Row, Col, Button } from 'antd'
import { PlayCircleOutlined, SettingOutlined, FileTextOutlined } from '@ant-design/icons'

const QuickActions: React.FC = () => {
  return (
    <Card title="快速操作">
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Button type="primary" icon={<PlayCircleOutlined />} block>
            启动策略
          </Button>
        </Col>
        <Col span={8}>
          <Button icon={<SettingOutlined />} block>
            配置
          </Button>
        </Col>
        <Col span={8}>
          <Button icon={<FileTextOutlined />} block>
            报告
          </Button>
        </Col>
      </Row>
    </Card>
  )
}

export default QuickActions
