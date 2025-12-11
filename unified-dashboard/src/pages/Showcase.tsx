import React, { useState } from 'react'
import {
  Button,
  Card,
  Input,
  Badge,
  Modal,
  Container,
  Grid,
  GridItem,
  Header,
  HeaderBrand,
  HeaderNav,
  HeaderActions,
  Table,
  Form,
  FormField,
  FormLabel,
  FormControl,
  FormMessage,
} from '@/components'

export const Showcase: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  })

  const tableData = [
    { id: 1, name: '策略 Alpha', status: '运行中', profit: '+15.2%', risk: '中等' },
    { id: 2, name: '策略 Beta', status: '已停止', profit: '-3.8%', risk: '低' },
    { id: 3, name: '策略 Gamma', status: '运行中', profit: '+28.5%', risk: '高' },
    { id: 4, name: '策略 Delta', status: '暂停', profit: '+7.1%', risk: '中等' },
  ]

  const tableColumns = [
    {
      key: 'name',
      title: '策略名称',
      render: (value: string) => <span className="font-medium">{value}</span>,
    },
    {
      key: 'status',
      title: '状态',
      render: (value: string) => {
        const statusMap = {
          '运行中': { variant: 'success', text: '运行中' },
          '已停止': { variant: 'error', text: '已停止' },
          '暂停': { variant: 'warning', text: '暂停' },
        }
        const status = statusMap[value] || { variant: 'default', text: value }
        return (
          <Badge variant={status.variant as any} size="sm">
            {status.text}
          </Badge>
        )
      },
    },
    {
      key: 'profit',
      title: '收益率',
      render: (value: string) => (
        <span className={value.startsWith('+') ? 'text-success-600' : 'text-error-600'}>
          {value}
        </span>
      ),
    },
    {
      key: 'risk',
      title: '风险等级',
      render: (value: string) => value,
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header>
        <HeaderBrand>
          <div className="text-xl font-bold text-gradient">CBSC Dashboard</div>
        </HeaderBrand>
        <HeaderNav>
          <Button variant="ghost" size="sm">组件</Button>
          <Button variant="ghost" size="sm">布局</Button>
          <Button variant="ghost" size="sm">表单</Button>
        </HeaderNav>
        <HeaderActions>
          <Button variant="outline" size="sm">文档</Button>
          <Button size="sm">开始使用</Button>
        </HeaderActions>
      </Header>

      <Container size="7xl" className="py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            企业级组件库
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            基于 React 18 + TypeScript + Tailwind CSS 构建的现代化组件库，
            为 CBSC 系统提供统一的用户体验和设计标准。
          </p>
        </div>

        {/* Button Components */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">按钮组件</h2>
          <Card className="p-8">
            <h3 className="text-lg font-medium text-gray-900 mb-6">基础按钮</h3>
            <div className="flex flex-wrap gap-4 mb-8">
              <Button variant="default">默认按钮</Button>
              <Button variant="secondary">次要按钮</Button>
              <Button variant="outline">边框按钮</Button>
              <Button variant="ghost">幽灵按钮</Button>
              <Button variant="link">链接按钮</Button>
            </div>

            <h3 className="text-lg font-medium text-gray-900 mb-6">状态按钮</h3>
            <div className="flex flex-wrap gap-4 mb-8">
              <Button variant="success">成功</Button>
              <Button variant="warning">警告</Button>
              <Button variant="destructive">危险</Button>
              <Button loading>加载中</Button>
              <Button disabled>禁用</Button>
            </div>

            <h3 className="text-lg font-medium text-gray-900 mb-6">尺寸变体</h3>
            <div className="flex items-center gap-4">
              <Button size="sm">小按钮</Button>
              <Button size="default">默认按钮</Button>
              <Button size="lg">大按钮</Button>
            </div>
          </Card>
        </section>

        {/* Form Components */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">表单组件</h2>
          <Grid cols={1} mdCols={2}>
            <GridItem>
              <Card className="p-8">
                <h3 className="text-lg font-medium text-gray-900 mb-6">基础表单</h3>
                <Form>
                  <FormField label="用户名" required>
                    <Input placeholder="请输入用户名" />
                  </FormField>
                  <FormField label="邮箱地址" helperText="我们不会分享您的邮箱">
                    <Input
                      type="email"
                      placeholder="user@example.com"
                      endIcon={
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                        </svg>
                      }
                    />
                  </FormField>
                  <FormField label="消息">
                    <textarea
                      className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-background placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      rows={4}
                      placeholder="请输入消息内容"
                    />
                  </FormField>
                </Form>
              </Card>
            </GridItem>

            <GridItem>
              <Card className="p-8">
                <h3 className="text-lg font-medium text-gray-900 mb-6">状态表单</h3>
                <Form>
                  <FormField label="正常输入">
                    <Input defaultValue="正常状态" />
                  </FormField>
                  <FormField label="错误状态" error="邮箱格式不正确">
                    <Input
                      type="email"
                      defaultValue="invalid-email"
                      variant="error"
                    />
                  </FormField>
                  <FormField label="成功状态" helperText="验证通过">
                    <Input
                      defaultValue="success@example.com"
                      variant="success"
                    />
                  </FormField>
                </Form>
              </Card>
            </GridItem>
          </Grid>
        </section>

        {/* Data Display */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">数据展示</h2>
          <Card>
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">策略数据表格</h3>
            </div>
            <Table
              columns={tableColumns}
              data={tableData}
              size="middle"
              striped
            />
          </Card>
        </section>

        {/* Badges */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">徽章组件</h2>
          <Card className="p-8">
            <h3 className="text-lg font-medium text-gray-900 mb-6">不同变体</h3>
            <div className="flex flex-wrap gap-3">
              <Badge>默认</Badge>
              <Badge variant="secondary">次要</Badge>
              <Badge variant="success">成功</Badge>
              <Badge variant="warning">警告</Badge>
              <Badge variant="error">错误</Badge>
              <Badge variant="outline">边框</Badge>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-6 mt-8">不同尺寸</h3>
            <div className="flex items-center gap-3">
              <Badge size="sm">小徽章</Badge>
              <Badge size="default">默认徽章</Badge>
              <Badge size="lg">大徽章</Badge>
            </div>
          </Card>
        </section>

        {/* Modal */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">弹窗组件</h2>
          <Card className="p-8">
            <h3 className="text-lg font-medium text-gray-900 mb-6">弹窗示例</h3>
            <Button onClick={() => setIsModalOpen(true)}>
              打开弹窗
            </Button>

            <Modal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              title="示例弹窗"
              description="这是一个弹窗组件的示例"
              size="md"
            >
              <div className="space-y-4">
                <p>弹窗内容可以包含任何React组件。</p>
                <Form>
                  <FormField label="弹窗内表单">
                    <Input placeholder="在此输入内容" />
                  </FormField>
                </Form>
                <div className="flex justify-end space-x-3 pt-4">
                  <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={() => setIsModalOpen(false)}>
                    确认
                  </Button>
                </div>
              </div>
            </Modal>
          </Card>
        </section>
      </Container>
    </div>
  )
}

export default Showcase