import React from 'react'
import { Card, List, Tag } from 'antd'

const RecentSignals: React.FC = () => {
  return (
    <Card title="最新信号">
      <List
        dataSource={[
          { title: '买入信号', type: 'success' },
          { title: '卖出信号', type: 'warning' },
          { title: '持有信号', type: 'default' },
        ]}
        renderItem={(item) => (
          <List.Item>
            <Tag color={item.type}>{item.title}</Tag>
          </List.Item>
        )}
      />
    </Card>
  )
}

export default RecentSignals
