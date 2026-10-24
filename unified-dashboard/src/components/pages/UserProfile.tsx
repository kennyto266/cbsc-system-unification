import React, { useState, useEffect } from 'react'
import {
  Row,
  Col,
  Card,
  Form,
  Input,
  Button,
  Upload,
  Avatar,
  Typography,
  Space,
  Divider,
  Alert,
  Modal,
  Select,
  DatePicker,
  Switch,
  Tag,
  Timeline,
  Statistic,
  List,
} from 'antd'
import {
  UserOutlined,
  CameraOutlined,
  EditOutlined,
  SaveOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  CalendarOutlined,
  TrophyOutlined,
  RocketOutlined,
  SecurityScanOutlined,
  HistoryOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

// Hooks and Services
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { selectAuth, updateUserProfile } from '../../store/slices/authSlice'

// Components
import PasswordChangeForm from '../common/PasswordChangeForm'
import TwoFactorSetup from '../common/TwoFactorSetup'
import ActivityHistory from '../common/ActivityHistory'

const { Title, Text } = Typography
const { Option } = Select

interface UserProfileProps {
  enableEditing?: boolean
  showActivityHistory?: boolean
  showSecuritySettings?: boolean
}

const UserProfile: React.FC<UserProfileProps> = ({
  enableEditing = true,
  showActivityHistory = true,
  showSecuritySettings = true
}) => {
  // Redux state
  const dispatch = useAppDispatch()
  const { user, isLoading } = useAppSelector(selectAuth)

  // Local state
  const [editing, setEditing] = useState(false)
  const [passwordModalVisible, setPasswordModalVisible] = useState(false)
  const [twoFactorModalVisible, setTwoFactorModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [avatarLoading, setAvatarLoading] = useState(false)

  // Initialize form with user data
  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        username: user.username,
        email: user.email,
        phone: user.phone || '',
        bio: user.bio || '',
        timezone: user.timezone || 'Asia/Shanghai',
        language: user.language || 'zh-CN',
        dateJoined: user.createdAt ? dayjs(user.createdAt) : null,
      })
    }
  }, [user, form])

  // Handle form submission
  const handleSubmit = async (values: any) => {
    try {
      const updatedProfile = {
        ...values,
        avatar: user?.avatar,
      }

      dispatch(updateUserProfile(updatedProfile))
      setEditing(false)
      Modal.success({
        title: '个人资料更新成功',
        content: '您的个人资料已成功更新',
      })
    } catch (error) {
      Modal.error({
        title: '更新失败',
        content: '个人资料更新失败，请重试',
      })
    }
  }

  // Handle avatar upload
  const handleAvatarUpload = async (file: File) => {
    setAvatarLoading(true)
    try {
      // Upload avatar to server
      // const avatarUrl = await api.uploadAvatar(file)

      // For now, use a placeholder
      const avatarUrl = URL.createObjectURL(file)

      dispatch(updateUserProfile({ ...user, avatar: avatarUrl }))
      Modal.success({
        title: '头像上传成功',
        content: '您的头像已成功更新',
      })
    } catch (error) {
      Modal.error({
        title: '头像上传失败',
        content: '头像上传失败，请重试',
      })
    } finally {
      setAvatarLoading(false)
    }
    return false // Prevent default upload behavior
  }

  // User statistics
  const userStats = {
    totalStrategies: user?.statistics?.totalStrategies || 12,
    activeStrategies: user?.statistics?.activeStrategies || 8,
    totalReturn: user?.statistics?.totalReturn || 0.156,
    joinDays: user?.createdAt ? Math.floor((new Date().getTime() - new Date(user.createdAt).getTime()) / (1000 * 60 * 60 * 24)) : 0,
    riskScore: user?.statistics?.riskScore || 'medium',
  }

  // Recent activities (mock data)
  const recentActivities = [
    {
      id: 1,
      action: '创建新策略',
      description: '创建了"RSI均值回归策略"',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      type: 'strategy',
    },
    {
      id: 2,
      action: '调整策略参数',
      description: '修改了"MACD动量策略"的参数',
      timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
      type: 'strategy',
    },
    {
      id: 3,
      action: '导出报告',
      description: '导出了月度性能报告',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
      type: 'report',
    },
    {
      id: 4,
      action: '修改个人资料',
      description: '更新了个人简介和头像',
      timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      type: 'profile',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            个人资料
          </Title>
          <Text type="secondary">
            管理您的个人信息和账户设置
          </Text>
        </div>

        {enableEditing && (
          <Space>
            {editing ? (
              <Space>
                <Button onClick={() => setEditing(false)}>
                  取消
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={() => form.submit()}
                  loading={isLoading}
                >
                  保存
                </Button>
              </Space>
            ) : (
              <Button
                icon={<EditOutlined />}
                onClick={() => setEditing(true)}
              >
                编辑资料
              </Button>
            )}
          </Space>
        )}
      </div>

      <Row gutter={[24, 24]}>
        {/* Profile Overview */}
        <Col xs={24} lg={8}>
          <Card className="text-center">
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* Avatar */}
              <div className="relative inline-block">
                <Avatar
                  size={120}
                  src={user?.avatar}
                  icon={<UserOutlined />}
                  className="mx-auto"
                />
                {enableEditing && (
                  <Upload
                    accept="image/*"
                    beforeUpload={handleAvatarUpload}
                    showUploadList={false}
                  >
                    <Button
                      type="primary"
                      shape="circle"
                      icon={<CameraOutlined />}
                      className="absolute bottom-0 right-0"
                      loading={avatarLoading}
                    />
                  </Upload>
                )}
              </div>

              {/* User Info */}
              <div>
                <Title level={3}>{user?.username || '用户名'}</Title>
                <Text type="secondary">{user?.email || 'email@example.com'}</Text>
                {user?.role && (
                  <div className="mt-2">
                    <Tag color="blue">{user.role}</Tag>
                  </div>
                )}
              </div>

              {/* Statistics */}
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Statistic
                    title="策略总数"
                    value={userStats.totalStrategies}
                    prefix={<RocketOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="运行中"
                    value={userStats.activeStrategies}
                    prefix={<TrophyOutlined />}
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="总收益"
                    value={userStats.totalReturn * 100}
                    precision={2}
                    suffix="%"
                    valueStyle={{ color: userStats.totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
                  />
                </Col>
              </Row>

              {/* Risk Profile */}
              <div className="mt-4">
                <Text strong>风险偏好: </Text>
                <Tag color={userStats.riskScore === 'high' ? 'red' : userStats.riskScore === 'medium' ? 'orange' : 'green'}>
                  {userStats.riskScore === 'high' ? '高风险' : userStats.riskScore === 'medium' ? '中等风险' : '低风险'}
                </Tag>
              </div>

              {/* Member Since */}
              <div>
                <Text type="secondary">
                  <CalendarOutlined /> 加入时间: {user?.createdAt ? dayjs(user.createdAt).format('YYYY年MM月DD日') : '未知'}
                </Text>
              </div>
            </Space>
          </Card>

          {/* Quick Actions */}
          <Card title="快速操作" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                block
                icon={<LockOutlined />}
                onClick={() => setPasswordModalVisible(true)}
              >
                修改密码
              </Button>
              {showSecuritySettings && (
                <Button
                  block
                  icon={<SecurityScanOutlined />}
                  onClick={() => setTwoFactorModalVisible(true)}
                >
                  两步验证设置
                </Button>
              )}
              <Button
                block
                icon={<SettingOutlined />}
              >
                通知偏好设置
              </Button>
            </Space>
          </Card>
        </Col>

        {/* Profile Details */}
        <Col xs={24} lg={16}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            disabled={!editing}
          >
            {/* Basic Information */}
            <Card title="基本信息" size="small">
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="用户名"
                    name="username"
                    rules={[
                      { required: true, message: '请输入用户名' },
                      { min: 3, message: '用户名至少3个字符' },
                    ]}
                  >
                    <Input prefix={<UserOutlined />} />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="邮箱地址"
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱地址' },
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input prefix={<MailOutlined />} />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="手机号码"
                    name="phone"
                    rules={[
                      { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
                    ]}
                  >
                    <Input prefix={<PhoneOutlined />} />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="加入时间"
                    name="dateJoined"
                  >
                    <DatePicker disabled style={{ width: '100%' }} />
                  </Form.Item>
                </Col>

                <Col xs={24}>
                  <Form.Item
                    label="个人简介"
                    name="bio"
                  >
                    <Input.TextArea
                      rows={4}
                      placeholder="介绍一下您自己..."
                      maxLength={500}
                      showCount
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>

            {/* Preferences */}
            <Card title="偏好设置" size="small">
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="时区"
                    name="timezone"
                  >
                    <Select>
                      <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                      <Option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</Option>
                      <Option value="America/New_York">America/New_York (UTC-5)</Option>
                      <Option value="Europe/London">Europe/London (UTC+0)</Option>
                      <Option value="UTC">UTC (UTC+0)</Option>
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="语言"
                    name="language"
                  >
                    <Select>
                      <Option value="zh-CN">简体中文</Option>
                      <Option value="zh-TW">繁体中文</Option>
                      <Option value="en-US">English</Option>
                      <Option value="ja-JP">日本語</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Card>

            {/* Trading Preferences */}
            <Card title="交易偏好" size="small">
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="默认风险等级"
                    name="defaultRiskLevel"
                  >
                    <Select>
                      <Option value="low">低风险</Option>
                      <Option value="medium">中等风险</Option>
                      <Option value="high">高风险</Option>
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="交易频率偏好"
                    name="tradingFrequency"
                  >
                    <Select>
                      <Option value="low">低频交易</Option>
                      <Option value="medium">中频交易</Option>
                      <Option value="high">高频交易</Option>
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="自动止损"
                    name="autoStopLoss"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="交易通知"
                    name="tradingNotifications"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Form>
        </Col>
      </Row>

      {/* Activity History */}
      {showActivityHistory && (
        <Card title="活动历史">
          <ActivityHistory
            activities={recentActivities}
            limit={10}
            showPagination={true}
          />
        </Card>
      )}

      {/* Password Change Modal */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => setPasswordModalVisible(false)}
        footer={null}
        width={500}
      >
        <PasswordChangeForm
          onSuccess={() => {
            setPasswordModalVisible(false)
            Modal.success({
              title: '密码修改成功',
              content: '您的密码已成功修改',
            })
          }}
        />
      </Modal>

      {/* Two Factor Setup Modal */}
      <Modal
        title="两步验证设置"
        open={twoFactorModalVisible}
        onCancel={() => setTwoFactorModalVisible(false)}
        footer={null}
        width={500}
      >
        <TwoFactorSetup
          onSuccess={() => {
            setTwoFactorModalVisible(false)
            Modal.success({
              title: '两步验证设置成功',
              content: '您的账户安全等级已提升',
            })
          }}
        />
      </Modal>
    </div>
  )
}

export default UserProfile