import React from 'react'
import { motion } from 'framer-motion'
import { Card, Row, Col, Statistic, Progress, Table, Tag, Space, Button } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  ThunderboltOutlined,
  MonitorOutlined,
  AlertOutlined,
  FundOutlined
} from '@ant-design/icons'
import { useAppSelector } from '../../hooks/redux'
import Header from '../../components/Layout/HeaderEnhanced'
import Sidebar from '../../components/Layout/Sidebar'
import Breadcrumb from '../../components/Layout/BreadcrumbEnhanced'
import QuickActions from '../../components/Layout/QuickActions'

const DashboardLayoutExample: React.FC = () => {
  const { themeMode } = useAppSelector(state => state.ui)
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)

  // Mock data
  const stats = [
    {
      title: '總資產',
      value: 1284500,
      precision: 2,
      valueStyle: { color: '#3f8600' },
      prefix: <DollarOutlined />,
      suffix: 'HKD',
      change: 5.2,
      trend: 'up'
    },
    {
      title: '今日收益',
      value: 15800,
      precision: 2,
      valueStyle: { color: '#3f8600' },
      prefix: <RiseOutlined />,
      suffix: 'HKD',
      change: 2.8,
      trend: 'up'
    },
    {
      title: '活躍策略',
      value: 12,
      valueStyle: { color: '#1890ff' },
      prefix: <ThunderboltOutlined />,
      change: 0,
      trend: 'neutral'
    },
    {
      title: '風險等級',
      value: '中等',
      valueStyle: { color: '#faad14' },
      prefix: <AlertOutlined />,
      change: -1.2,
      trend: 'down'
    }
  ]

  const columns = [
    {
      title: '策略名稱',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <span className="font-medium">{text}</span>
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === '均值回歸' ? 'blue' : type === '動量策略' ? 'green' : 'orange'}>
          {type}
        </Tag>
      )
    },
    {
      title: '收益率',
      dataIndex: 'return',
      key: 'return',
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-500' : 'text-red-500'}>
          {value >= 0 ? '+' : ''}{value}%
        </span>
      )
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === '運行中' ? 'success' : status === '已停止' ? 'default' : 'processing'}>
          {status}
        </Tag>
      )
    }
  ]

  const data = [
    { key: '1', name: 'RSI均值回歸', type: '均值回歸', return: 5.2, status: '運行中' },
    { key: '2', name: 'MACD動量策略', type: '動量策略', return: -1.8, status: '運行中' },
    { key: '3', name: '布林帶突破', type: '突破策略', return: 3.5, status: '暫停' },
    { key: '4', name: '均線交叉', type: '趨勢策略', return: 8.9, status: '運行中' },
    { key: '5', name: '網格交易', type: '量化策略', return: 2.1, status: '運行中' }
  ]

  const quickActions = [
    {
      key: 'new-strategy',
      label: '新建策略',
      icon: <ThunderboltOutlined />,
      onClick: () => console.log('Create new strategy')
    },
    {
      key: 'monitor',
      label: '實時監控',
      icon: <MonitorOutlined />,
      onClick: () => console.log('Open monitoring')
    },
    {
      key: 'portfolio',
      label: '投資組合',
      icon: <FundOutlined />,
      onClick: () => console.log('View portfolio')
    }
  ]

  return (
    <div className={`min-h-screen ${themeMode === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <Header
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Layout Container */}
      <div className="flex pt-16">
        {/* Sidebar */}
        <Sidebar
          collapsed={sidebarCollapsed}
          onCollapse={setSidebarCollapsed}
        />

        {/* Main Content */}
        <div
          className={`flex-1 transition-all duration-300 ${
            sidebarCollapsed ? 'ml-20' : 'ml-72'
          }`}
        >
          <div className="p-6">
            {/* Breadcrumb and Quick Actions */}
            <div className="flex items-center justify-between mb-6">
              <Breadcrumb />
              <QuickActions actions={quickActions} />
            </div>

            {/* Dashboard Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              {/* Statistics Cards */}
              <Row gutter={[16, 16]} className="mb-6">
                {stats.map((stat, index) => (
                  <Col xs={24} sm={12} lg={6} key={index}>
                    <Card>
                      <Statistic
                        title={stat.title}
                        value={stat.value}
                        precision={stat.precision}
                        valueStyle={stat.valueStyle}
                        prefix={stat.prefix}
                        suffix={stat.suffix}
                      />
                      {stat.change !== 0 && (
                        <div className="mt-2 flex items-center">
                          {stat.trend === 'up' ? (
                            <ArrowUpOutlined className="text-green-500 mr-1" />
                          ) : stat.trend === 'down' ? (
                            <ArrowDownOutlined className="text-red-500 mr-1" />
                          ) : null}
                          <span className={`text-sm ${
                            stat.trend === 'up' ? 'text-green-500' :
                            stat.trend === 'down' ? 'text-red-500' : 'text-gray-500'
                          }`}>
                            {stat.trend === 'up' ? '+' : ''}{stat.change}%
                          </span>
                        </div>
                      )}
                    </Card>
                  </Col>
                ))}
              </Row>

              {/* Strategy Performance Table */}
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Card title="策略表現" extra={<Button type="primary">查看全部</Button>}>
                    <Table
                      columns={columns}
                      dataSource={data}
                      pagination={false}
                      className="strategy-table"
                    />
                  </Card>
                </Col>
              </Row>

              {/* Additional Widgets */}
              <Row gutter={[16, 16]} className="mt-6">
                <Col xs={24} lg={12}>
                  <Card title="資產配置">
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between mb-1">
                          <span>股票</span>
                          <span>45%</span>
                        </div>
                        <Progress percent={45} strokeColor="#3f8600" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span>衍生品</span>
                          <span>30%</span>
                        </div>
                        <Progress percent={30} strokeColor="#1890ff" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span>現金</span>
                          <span>25%</span>
                        </div>
                        <Progress percent={25} strokeColor="#faad14" />
                      </div>
                    </div>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="市場概況">
                    <Space direction="vertical" className="w-full">
                      <div className="flex justify-between">
                        <span>恒生指數</span>
                        <span className="text-red-500">18,234.56 (-1.2%)</span>
                      </div>
                      <div className="flex justify-between">
                        <span>國企指數</span>
                        <span className="text-green-500">6,234.78 (+0.8%)</span>
                      </div>
                      <div className="flex justify-between">
                        <span>紅籌指數</span>
                        <span className="text-green-500">3,456.12 (+0.5%)</span>
                      </div>
                      <div className="flex justify-between">
                        <span>成交量</span>
                        <span>1,234.5億</span>
                      </div>
                    </Space>
                  </Card>
                </Col>
              </Row>
            </motion.div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .strategy-table .ant-table-thead > tr > th {
          background-color: ${themeMode === 'dark' ? '#1f1f1f' : '#fafafa'};
        }
      `}</style>
    </div>
  )
}

export default DashboardLayoutExample