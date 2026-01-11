import React from 'react'
import { Card, Form, Input, Button, Typography } from 'antd'

const { Title, Link } = Typography

const LoginPage: React.FC = () => {
  const onFinish = (values: any) => {
    console.log('Login values:', values)
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: '400px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
            CBSC 统一管理平台
          </Title>
          <p style={{ color: '#666', margin: 0 }}>
            现代化量化交易策略管理平台
          </p>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              style={{
                width: '100%',
                height: '48px',
                fontSize: '16px',
                background: '#1890ff',
                borderColor: '#1890ff'
              }}
            >
              登录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center', color: '#666' }}>
            <Link href="/register">注册账户</Link> |
            <Link href="/forgot-password" style={{ marginLeft: '8px' }}>
              忘记密码
            </Link>
          </div>
        </Form>

        <div style={{
          marginTop: '24px',
          padding: '16px',
          background: '#f6ffed',
          border: '1px solid #b7eb8f',
          borderRadius: '6px',
          fontSize: '12px',
          color: '#52c41a',
          textAlign: 'center'
        }}>
          💡 提示：使用演示账户 admin/admin 快速体验
        </div>
      </Card>
    </div>
  )
}

export default LoginPage