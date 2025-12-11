import React from 'react'
import { Spin } from 'antd'

const LoadingScreen: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#f0f2f5'
    }}>
      <Spin size="large" />
      <div style={{
        marginTop: '16px',
        fontSize: '16px',
        color: '#666'
      }}>
        CBSC Dashboard 加载中...
      </div>
    </div>
  )
}

export default LoadingScreen