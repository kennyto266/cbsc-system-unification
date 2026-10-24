import React from 'react'
import { Result, Button } from 'antd'

interface ComingSoonProps {
  title?: string
}

const ComingSoon: React.FC<ComingSoonProps> = ({ title = '功能開發中' }) => {
  return (
    <Result
      status="info"
      title={title}
      subTitle="此頁面正在開發中，敬請期待。"
      extra={<Button type="primary" href="/dashboard">返回儀表板</Button>}
    />
  )
}

export default ComingSoon
