import React from 'react'
import { Card, Descriptions, Tag, Divider, Row, Col, Space } from 'antd'
import {
  SettingOutlined,
  InfoCircleOutlined,
  NumberOutlined,
  PercentageOutlined,
  DollarOutlined,
} from '@ant-design/icons'

interface ParameterDisplayProps {
  parameters: Record<string, any>
  showAdvanced?: boolean
  compact?: boolean
}

const ParameterDisplay: React.FC<ParameterDisplayProps> = ({
  parameters,
  showAdvanced = false,
  compact = false,
}) => {
  // Group parameters by category
  const parameterGroups = {
    basic: {
      title: '基础参数',
      icon: <SettingOutlined />,
      parameters: [
        { key: 'rsiPeriod', label: 'RSI周期', unit: '', type: 'number' },
        { key: 'oversoldLevel', label: '超卖水平', unit: '', type: 'number' },
        { key: 'overboughtLevel', label: '超买水平', unit: '', type: 'number' },
        { key: 'lookbackPeriod', label: '回望周期', unit: '天', type: 'number' },
        { key: 'fastPeriod', label: '快线周期', unit: '', type: 'number' },
        { key: 'slowPeriod', label: '慢线周期', unit: '', type: 'number' },
        { key: 'signalPeriod', label: '信号线周期', unit: '', type: 'number' },
        { key: 'bollingerPeriod', label: '布林带周期', unit: '', type: 'number' },
        { key: 'bollingerStdDev', label: '标准差倍数', unit: '', type: 'number' },
        { key: 'sentimentSource', label: '情感来源', unit: '', type: 'string' },
        { key: 'sentimentThreshold', label: '情感阈值', unit: '', type: 'number' },
        { key: 'leverage', label: '杠杆倍数', unit: 'x', type: 'number' },
      ],
    },
    risk: {
      title: '风险管理',
      icon: <InfoCircleOutlined />,
      parameters: [
        { key: 'maxPositionSize', label: '最大持仓', unit: '¥', type: 'currency' },
        { key: 'stopLossPercent', label: '止损比例', unit: '%', type: 'percentage' },
        { key: 'takeProfitPercent', label: '止盈比例', unit: '%', type: 'percentage' },
        { key: 'maxDrawdownPercent', label: '最大回撤', unit: '%', type: 'percentage' },
      ],
    },
    execution: {
      title: '执行设置',
      icon: <SettingOutlined />,
      parameters: [
        { key: 'signalConfirmation', label: '信号确认', unit: '', type: 'boolean' },
        { key: 'signalStrengthThreshold', label: '信号强度阈值', unit: '', type: 'number' },
        { key: 'dynamicAdjustment', label: '动态调整', unit: '', type: 'boolean' },
        { key: 'updateFrequency', label: '更新频率', unit: '', type: 'string' },
        { key: 'volumeConfirmation', label: '成交量确认', unit: '', type: 'boolean' },
      ],
    },
  }

  // Format parameter value based on type
  const formatValue = (value: any, type: string, unit: string) => {
    if (value === undefined || value === null) {
      return <Tag color="default">未设置</Tag>
    }

    switch (type) {
      case 'boolean':
        return (
          <Tag color={value ? 'success' : 'default'}>
            {value ? '开启' : '关闭'}
          </Tag>
        )
      case 'currency':
        return (
          <Tag color="blue" icon={<DollarOutlined />}>
            ¥{value.toLocaleString()}
          </Tag>
        )
      case 'percentage':
        return (
          <Tag color="green" icon={<PercentageOutlined />}>
            {value}%
          </Tag>
        )
      case 'number':
        return (
          <Tag color="purple" icon={<NumberOutlined />}>
            {value}{unit}
          </Tag>
        )
      case 'string':
      default:
        return <span>{value}{unit}</span>
    }
  }

  // Filter parameters that exist in the provided parameters object
  const getFilteredParameters = (paramList: Array<any>) => {
    return paramList.filter(param => parameters[param.key] !== undefined)
  }

  // Render compact version
  if (compact) {
    return (
      <div className="space-y-2">
        {Object.entries(parameterGroups).map(([groupKey, group]) => {
          const filteredParams = getFilteredParameters(group.parameters)
          if (filteredParams.length === 0) return null

          return (
            <div key={groupKey} className="mb-2">
              <div className="text-sm font-medium text-gray-600 mb-1">
                {group.title}
              </div>
              <div className="flex flex-wrap gap-1">
                {filteredParams.map(param => (
                  <span key={param.key} className="text-xs">
                    {param.label}: {formatValue(parameters[param.key], param.type, param.unit)}
                  </span>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  // Render full version
  return (
    <div className="space-y-4">
      {Object.entries(parameterGroups).map(([groupKey, group]) => {
        const filteredParams = getFilteredParameters(group.parameters)
        if (filteredParams.length === 0) return null

        return (
          <Card key={groupKey} size="small" title={
            <Space>
              {group.icon}
              {group.title}
            </Space>
          }>
            <Descriptions column={1} size="small">
              {filteredParams.map(param => (
                <Descriptions.Item
                  key={param.key}
                  label={param.label}
                  span={1}
                >
                  {formatValue(parameters[param.key], param.type, param.unit)}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        )
      })}

      {/* Additional parameters */}
      {showAdvanced && Object.keys(parameters).length > 0 && (
        <Card size="small" title="其他参数">
          <Row gutter={[16, 8]}>
            {Object.entries(parameters).map(([key, value]) => {
              // Skip already displayed parameters
              const allParamKeys = Object.values(parameterGroups)
                .flatMap(group => group.parameters)
                .map(p => p.key)

              if (allParamKeys.includes(key)) return null

              return (
                <Col span={12} key={key}>
                  <div className="text-sm">
                    <span className="text-gray-600">{key}:</span>
                    <span className="ml-2 font-medium">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                </Col>
              )
            })}
          </Row>
        </Card>
      )}

      {/* Selected indicators */}
      {parameters.indicators && parameters.indicators.length > 0 && (
        <Card size="small" title="技术指标">
          <Space wrap>
            {parameters.indicators.map((indicator: string) => (
              <Tag key={indicator} color="blue">
                {indicator}
              </Tag>
            ))}
          </Space>
        </Card>
      )}
    </div>
  )
}

export default ParameterDisplay