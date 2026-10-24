import React from 'react'
import {
  Card,
  Form,
  InputNumber,
  Slider,
  Switch,
  Row,
  Col,
  Space,
  Tooltip,
  Alert,
} from 'antd'
import {
  InfoCircleOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
} from '@ant-design/icons'

interface RiskSettingsProps {
  settings: {
    maxPositionSize: number
    stopLossPercent: number
    takeProfitPercent: number
    maxDrawdownPercent: number
    leverage: number
  }
  onChange: (settings: any) => void
  disabled?: boolean
}

const RiskSettings: React.FC<RiskSettingsProps> = ({
  settings,
  onChange,
  disabled = false,
}) => {
  const riskLevel = calculateRiskLevel(settings)

  // Calculate risk level based on settings
  function calculateRiskLevel(s: typeof settings): 'low' | 'medium' | 'high' {
    let score = 0

    // Leverage contributes to risk
    if (s.leverage > 3) score += 3
    else if (s.leverage > 2) score += 2
    else if (s.leverage > 1) score += 1

    // Stop loss contributes to risk (lower stop loss = higher risk)
    if (s.stopLossPercent < 2) score += 3
    else if (s.stopLossPercent < 5) score += 2
    else if (s.stopLossPercent < 10) score += 1

    // Max drawdown contributes to risk
    if (s.maxDrawdownPercent > 30) score += 3
    else if (s.maxDrawdownPercent > 20) score += 2
    else if (s.maxDrawdownPercent > 10) score += 1

    if (score >= 6) return 'high'
    if (score >= 4) return 'medium'
    return 'low'
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return '#52c41a'
      case 'medium': return '#faad14'
      case 'high': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const getRiskText = (level: string) => {
    switch (level) {
      case 'low': return '低风险'
      case 'medium': return '中风险'
      case 'high': return '高风险'
      default: return '未知'
    }
  }

  const getRiskDescription = (level: string) => {
    switch (level) {
      case 'low':
        return '保守的风险设置，适合稳健型投资者'
      case 'medium':
        return '平衡的风险设置，适合风险承受能力中等的投资者'
      case 'high':
        return '激进的风险设置，适合风险承受能力较强的投资者'
      default:
        return ''
    }
  }

  return (
    <div className="space-y-4">
      {/* Risk Level Indicator */}
      <Alert
        message={
          <div className="flex items-center space-x-2">
            <SafetyCertificateOutlined />
            <span>当前风险等级：</span>
            <span style={{ color: getRiskColor(riskLevel), fontWeight: 'bold' }}>
              {getRiskText(riskLevel)}
            </span>
          </div>
        }
        description={getRiskDescription(riskLevel)}
        type={riskLevel === 'high' ? 'warning' : riskLevel === 'medium' ? 'info' : 'success'}
        showIcon
      />

      <Row gutter={[16, 16]}>
        {/* Maximum Position Size */}
        <Col xs={24} sm={12} md={8}>
          <Card size="small" title="最大持仓金额">
            <Form.Item label={
              <Space>
                持仓金额 (¥)
                <Tooltip title="单个策略的最大投资金额">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            }>
              <InputNumber
                style={{ width: '100%' }}
                min={1000}
                max={10000000}
                step={10000}
                value={settings.maxPositionSize}
                onChange={(value) => onChange({ ...settings, maxPositionSize: value || 100000 })}
                formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value!.replace(/¥\s?|(,*)/g, '')}
                disabled={disabled}
              />
              <Slider
                min={1000}
                max={1000000}
                step={10000}
                value={settings.maxPositionSize}
                onChange={(value) => onChange({ ...settings, maxPositionSize: value })}
                disabled={disabled}
                marks={{
                  10000: '1万',
                  100000: '10万',
                  500000: '50万',
                  1000000: '100万',
                }}
              />
            </Form.Item>
          </Card>
        </Col>

        {/* Stop Loss */}
        <Col xs={24} sm={12} md={8}>
          <Card size="small" title="止损设置">
            <Form.Item label={
              <Space>
                止损比例 (%)
                <Tooltip title="触发止损的价格下跌百分比">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            }>
              <InputNumber
                style={{ width: '100%' }}
                min={0.5}
                max={50}
                step={0.5}
                value={settings.stopLossPercent}
                onChange={(value) => onChange({ ...settings, stopLossPercent: value || 5 })}
                suffix="%"
                disabled={disabled}
              />
              <Slider
                min={0.5}
                max={20}
                step={0.5}
                value={settings.stopLossPercent}
                onChange={(value) => onChange({ ...settings, stopLossPercent: value })}
                disabled={disabled}
                marks={{
                  1: '1%',
                  5: '5%',
                  10: '10%',
                  20: '20%',
                }}
              />
            </Form.Item>
          </Card>
        </Col>

        {/* Take Profit */}
        <Col xs={24} sm={12} md={8}>
          <Card size="small" title="止盈设置">
            <Form.Item label={
              <Space>
                止盈比例 (%)
                <Tooltip title="触发止盈的价格上涨百分比">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            }>
              <InputNumber
                style={{ width: '100%' }}
                min={1}
                max={200}
                step={1}
                value={settings.takeProfitPercent}
                onChange={(value) => onChange({ ...settings, takeProfitPercent: value || 10 })}
                suffix="%"
                disabled={disabled}
              />
              <Slider
                min={1}
                max={100}
                step={1}
                value={settings.takeProfitPercent}
                onChange={(value) => onChange({ ...settings, takeProfitPercent: value })}
                disabled={disabled}
                marks={{
                  5: '5%',
                  10: '10%',
                  25: '25%',
                  50: '50%',
                  100: '100%',
                }}
              />
            </Form.Item>
          </Card>
        </Col>

        {/* Maximum Drawdown */}
        <Col xs={24} sm={12} md={8}>
          <Card size="small" title="回撤控制">
            <Form.Item label={
              <Space>
                最大回撤 (%)
                <Tooltip title="策略最大允许的资金回撤百分比">
                  <WarningOutlined style={{ color: '#ff4d4f' }} />
                </Tooltip>
              </Space>
            }>
              <InputNumber
                style={{ width: '100%' }}
                min={5}
                max={50}
                step={1}
                value={settings.maxDrawdownPercent}
                onChange={(value) => onChange({ ...settings, maxDrawdownPercent: value || 20 })}
                suffix="%"
                disabled={disabled}
              />
              <Slider
                min={5}
                max={50}
                step={1}
                value={settings.maxDrawdownPercent}
                onChange={(value) => onChange({ ...settings, maxDrawdownPercent: value })}
                disabled={disabled}
                marks={{
                  10: '10%',
                  20: '20%',
                  30: '30%',
                  40: '40%',
                }}
                tooltip={{
                  formatter: (value) => `${value}% - ${value! <= 10 ? '严格' : value! <= 20 ? '适中' : '宽松'}控制`,
                }}
              />
            </Form.Item>
          </Card>
        </Col>

        {/* Leverage */}
        <Col xs={24} sm={12} md={8}>
          <Card size="small" title="杠杆设置">
            <Form.Item label={
              <Space>
                杠杆倍数
                <Tooltip title="交易杠杆倍数，越高风险越大">
                  <WarningOutlined style={{ color: '#faad14' }} />
                </Tooltip>
              </Space>
            }>
              <InputNumber
                style={{ width: '100%' }}
                min={1}
                max={10}
                step={0.1}
                value={settings.leverage}
                onChange={(value) => onChange({ ...settings, leverage: value || 1 })}
                suffix="x"
                disabled={disabled}
              />
              <Slider
                min={1}
                max={5}
                step={0.1}
                value={Math.min(settings.leverage, 5)}
                onChange={(value) => onChange({ ...settings, leverage: value })}
                disabled={disabled}
                marks={{
                  1: '1x (无杠杆)',
                  2: '2x',
                  3: '3x',
                  5: '5x',
                }}
                tooltip={{
                  formatter: (value) => `${value}x 倍杠杆`,
                }}
              />
            </Form.Item>
          </Card>
        </Col>

        {/* Risk Management Features */}
        <Col xs={24} sm={12} md={8}>
          <Card size="small" title="风险管理功能">
            <Space direction="vertical" className="w-full">
              <div className="flex justify-between items-center">
                <span>动态止损</span>
                <Switch
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                  defaultChecked
                  disabled={disabled}
                />
              </div>
              <div className="flex justify-between items-center">
                <span>仓位保护</span>
                <Switch
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                  defaultChecked
                  disabled={disabled}
                />
              </div>
              <div className="flex justify-between items-center">
                <span>波动率限制</span>
                <Switch
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                  disabled={disabled}
                />
              </div>
              <div className="flex justify-between items-center">
                <span>时间止损</span>
                <Switch
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                  disabled={disabled}
                />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Risk Summary */}
      <Card title="风险概览" size="small">
        <Row gutter={[16, 8]}>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold" style={{ color: getRiskColor(riskLevel) }}>
                {getRiskText(riskLevel)}
              </div>
              <div className="text-gray-500">整体风险</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {settings.leverage}x
              </div>
              <div className="text-gray-500">杠杆倍数</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold" style={{ color: settings.stopLossPercent <= 5 ? '#ff4d4f' : '#52c41a' }}>
                {settings.stopLossPercent}%
              </div>
              <div className="text-gray-500">止损比例</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold">
                ¥{(settings.maxPositionSize / 10000).toFixed(0)}万
              </div>
              <div className="text-gray-500">最大持仓</div>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default RiskSettings