import React, { useState, useEffect } from 'react'
import {
  Row,
  Col,
  Card,
  Form,
  Switch,
  Select,
  Slider,
  Input,
  Button,
  Space,
  Typography,
  Divider,
  Alert,
  Tabs,
  Upload,
  message,
  Modal,
  TimePicker,
  InputNumber,
} from 'antd'
import {
  UserOutlined,
  BellOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  UploadOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

// Hooks and Services
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { selectUI, updateSettings } from '../../store/slices/uiSlice'
import { selectAuth } from '../../store/slices/authSlice'

// Components
import ThemeSelector from '../common/ThemeSelector'
import LanguageSelector from '../common/LanguageSelector'
import NotificationSettings from '../common/NotificationSettings'
import SecuritySettings from '../common/SecuritySettings'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

interface SettingsProps {
  onSave?: (settings: any) => void
  onReset?: () => void
}

const Settings: React.FC<SettingsProps> = ({ onSave, onReset }) => {
  // Redux state
  const dispatch = useAppDispatch()
  const { theme, language, notifications, preferences } = useAppSelector(selectUI)
  const { user } = useAppSelector(selectAuth)

  // Local state
  const [activeTab, setActiveTab] = useState('general')
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [settingsChanged, setSettingsChanged] = useState(false)
  const [resetModalVisible, setResetModalVisible] = useState(false)

  // Initialize form with current settings
  useEffect(() => {
    form.setFieldsValue({
      theme,
      language,
      ...preferences,
      ...notifications,
    })
  }, [theme, language, preferences, notifications, form])

  // Handle form value change
  const handleFormChange = () => {
    setSettingsChanged(true)
  }

  // Save settings
  const handleSave = async (values: any) => {
    setLoading(true)
    try {
      // Update UI settings
      dispatch(updateSettings(values))

      // Save to backend
      // await api.saveUserSettings(values)

      setSettingsChanged(false)
      message.success('设置保存成功')
      onSave?.(values)
    } catch (error) {
      message.error('保存设置失败，请重试')
      console.error('Save settings error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Reset settings
  const handleReset = () => {
    setResetModalVisible(true)
  }

  const confirmReset = () => {
    form.resetFields()
    setSettingsChanged(false)
    setResetModalVisible(false)
    onReset?.()
    message.info('设置已重置为默认值')
  }

  // Export settings
  const handleExport = () => {
    const settings = form.getFieldsValue()
    const dataStr = JSON.stringify(settings, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)

    const exportFileDefaultName = `cbsc-settings-${dayjs().format('YYYY-MM-DD')}.json`

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()

    message.success('设置已导出')
  }

  // Import settings
  const handleImport = (file: any) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const settings = JSON.parse(e.target?.result as string)
        form.setFieldsValue(settings)
        setSettingsChanged(true)
        message.success('设置导入成功')
      } catch (error) {
        message.error('导入设置失败，文件格式不正确')
      }
    }
    reader.readAsText(file)
    return false // Prevent default upload behavior
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            系统设置
          </Title>
          <Text type="secondary">
            自定义您的CBSC Dashboard体验和偏好设置
          </Text>
        </div>

        <Space>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            导出设置
          </Button>
          <Upload
            accept=".json"
            beforeUpload={handleImport}
            showUploadList={false}
          >
            <Button icon={<UploadOutlined />}>
              导入设置
            </Button>
          </Upload>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleReset}
          >
            重置
          </Button>
        </Space>
      </div>

      {/* Settings Changed Alert */}
      {settingsChanged && (
        <Alert
          message="您有未保存的设置更改"
          description="请点击保存按钮来应用您的更改"
          type="warning"
          showIcon
          action={
            <Button size="small" type="primary" onClick={() => form.submit()}>
              立即保存
            </Button>
          }
        />
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        onValuesChange={handleFormChange}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* General Settings */}
          <TabPane
            tab={
              <Space>
                <SettingOutlined />
                常规设置
              </Space>
            }
            key="general"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Card title="界面设置" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong className="block mb-2">主题</Text>
                      <ThemeSelector
                        value={theme}
                        onChange={(value) => form.setFieldValue('theme', value)}
                      />
                    </div>

                    <div>
                      <Text strong className="block mb-2">语言</Text>
                      <LanguageSelector
                        value={language}
                        onChange={(value) => form.setFieldValue('language', value)}
                      />
                    </div>

                    <Form.Item name="autoRefresh" label="自动刷新数据" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="autoRefreshInterval" label="刷新间隔 (秒)">
                      <Slider
                        min={5}
                        max={300}
                        marks={{
                          5: '5s',
                          30: '30s',
                          60: '1m',
                          300: '5m'
                        }}
                      />
                    </Form.Item>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="显示设置" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="defaultView" label="默认视图">
                      <Select>
                        <Option value="dashboard">总览面板</Option>
                        <Option value="strategies">策略管理</Option>
                        <Option value="monitoring">实时监控</Option>
                        <Option value="analytics">数据分析</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item name="itemsPerPage" label="每页显示条数">
                      <Select>
                        <Option value={10}>10条</Option>
                        <Option value={20}>20条</Option>
                        <Option value={50}>50条</Option>
                        <Option value={100}>100条</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item name="showTooltips" label="显示工具提示" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="compactMode" label="紧凑模式" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* Notification Settings */}
          <TabPane
            tab={
              <Space>
                <BellOutlined />
                通知设置
              </Space>
            }
            key="notifications"
          >
            <NotificationSettings />
          </TabPane>

          {/* Security Settings */}
          <TabPane
            tab={
              <Space>
                <SecurityScanOutlined />
                安全设置
              </Space>
            }
            key="security"
          >
            <SecuritySettings />
          </TabPane>

          {/* Data Settings */}
          <TabPane
            tab={
              <Space>
                <DatabaseOutlined />
                数据设置
              </Space>
            }
            key="data"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Card title="数据源配置" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="primaryDataSource" label="主要数据源">
                      <Select>
                        <Option value="binance">Binance</Option>
                        <Option value="coinbase">Coinbase</Option>
                        <Option value="yahoo">Yahoo Finance</Option>
                        <Option value="alpha_vantage">Alpha Vantage</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item name="backupDataSource" label="备用数据源">
                      <Select allowClear>
                        <Option value="binance">Binance</Option>
                        <Option value="coinbase">Coinbase</Option>
                        <Option value="yahoo">Yahoo Finance</Option>
                        <Option value="alpha_vantage">Alpha Vantage</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item name="dataUpdateFrequency" label="数据更新频率">
                      <Select>
                        <Option value="realtime">实时</Option>
                        <Option value="1m">1分钟</Option>
                        <Option value="5m">5分钟</Option>
                        <Option value="15m">15分钟</Option>
                        <Option value="1h">1小时</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item name="maxDataAge" label="数据保留天数">
                      <InputNumber min={1} max={365} />
                    </Form.Item>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="性能设置" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="enableCaching" label="启用数据缓存" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="cacheExpiry" label="缓存过期时间 (分钟)">
                      <Slider
                        min={1}
                        max={60}
                        marks={{
                          1: '1m',
                          15: '15m',
                          30: '30m',
                          60: '1h'
                        }}
                      />
                    </Form.Item>

                    <Form.Item name="maxConcurrentRequests" label="最大并发请求数">
                      <Slider
                        min={1}
                        max={10}
                        marks={{
                          1: '1',
                          5: '5',
                          10: '10'
                        }}
                      />
                    </Form.Item>

                    <Form.Item name="enableCompression" label="启用数据压缩" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                  </Space>
                </Card>
              </Col>
            </Row>

            <Row gutter={[24, 24]}>
              <Col xs={24}>
                <Card title="数据管理" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                      message="数据管理"
                      description="以下操作将影响您的历史数据，请谨慎操作"
                      type="warning"
                      showIcon
                    />

                    <Row gutter={[16, 16]}>
                      <Col>
                        <Button danger>
                          清理缓存
                        </Button>
                      </Col>
                      <Col>
                        <Button danger>
                          重置数据
                        </Button>
                      </Col>
                      <Col>
                        <Button>
                          导出数据
                        </Button>
                      </Col>
                      <Col>
                        <Button>
                          导入数据
                        </Button>
                      </Col>
                    </Row>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* Advanced Settings */}
          <TabPane
            tab={
              <Space>
                <SettingOutlined />
                高级设置
              </Space>
            }
            key="advanced"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Card title="调试选项" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item name="enableDebugMode" label="启用调试模式" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="showConsoleLogs" label="显示控制台日志" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="enablePerformanceMonitoring" label="启用性能监控" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="logLevel" label="日志级别">
                      <Select>
                        <Option value="error">错误</Option>
                        <Option value="warn">警告</Option>
                        <Option value="info">信息</Option>
                        <Option value="debug">调试</Option>
                      </Select>
                    </Form.Item>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="实验性功能" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                      message="实验性功能"
                      description="这些功能正在开发中，可能不稳定"
                      type="info"
                      showIcon
                    />

                    <Form.Item name="enableBetaFeatures" label="启用Beta功能" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="enableAdvancedCharts" label="启用高级图表" valuePropName="checked">
                      <Switch />
                    </Form.Item>

                    <Form.Item name="enableAIModules" label="启用AI模块" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>

        {/* Save Button */}
        <div className="flex justify-end mt-6">
          <Space>
            <Button
              onClick={handleReset}
              disabled={!settingsChanged}
            >
              重置
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              disabled={!settingsChanged}
              icon={<SaveOutlined />}
            >
              保存设置
            </Button>
          </Space>
        </div>
      </Form>

      {/* Reset Confirmation Modal */}
      <Modal
        title="确认重置设置"
        open={resetModalVisible}
        onOk={confirmReset}
        onCancel={() => setResetModalVisible(false)}
        okText="确认重置"
        cancelText="取消"
      >
        <Space direction="vertical">
          <Text>您确定要重置所有设置到默认值吗？</Text>
          <Text type="secondary">此操作无法撤销。</Text>
        </Space>
      </Modal>
    </div>
  )
}

export default Settings