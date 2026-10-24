import React, { useState } from 'react'
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Typography,
  Divider,
  Alert,
  Tabs,
  Timeline,
  Badge,
  Tooltip,
  Row,
  Col,
  Statistic,
  List,
  Collapse,
  message
} from 'antd'
import {
  CopyOutlined,
  BookOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  CalculatorOutlined,
  BulbOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  StarFilled,
  ShareAltOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'

import { TechnicalIndicator } from '../../types/technical-indicators'
import IndicatorParameterForm from './IndicatorParameterForm'
import IndicatorPerformanceChart from './IndicatorPerformanceChart'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { Panel } = Collapse

interface IndicatorDetailsProps {
  indicator: TechnicalIndicator
  onClose: () => void
}

const IndicatorDetails: React.FC<IndicatorDetailsProps> = ({
  indicator,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [showParameterForm, setShowParameterForm] = useState(false)

  const handleCopyFormula = () => {
    navigator.clipboard.writeText(indicator.formula || '')
    message.success('公式已复制到剪贴板')
  }

  const renderOverviewTab = () => (
    <div>
      {/* Basic Information */}
      <Card title="基本信息" size="small" className="mb-4">
        <Descriptions column={1} bordered>
          <Descriptions.Item label="指标名称">
            <Text strong>{indicator.name}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="指标类型">
            <Tag color="blue">{indicator.type}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="分类">
            <Tag color="geekblue">{indicator.category}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="描述">
            <Paragraph>{indicator.description}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="标签">
            <Space wrap>
              {indicator.tags.map(tag => (
                <Tag key={tag} size="small">{tag}</Tag>
              ))}
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Visual Settings */}
      <Card title="视觉设置" size="small" className="mb-4">
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="颜色"
              value={indicator.visualSettings.color}
              prefix={
                <div
                  style={{
                    width: 20,
                    height: 20,
                    backgroundColor: indicator.visualSettings.color,
                    borderRadius: 4,
                    display: 'inline-block'
                  }}
                />
              }
              formatter={(value) => <Text code>{value}</Text>}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="线条宽度"
              value={indicator.visualSettings.lineWidth}
              suffix="px"
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="样式"
              value={indicator.visualSettings.style}
              formatter={(value) => (
                <Tag color="blue">{value}</Tag>
              )}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="透明度"
              value={Math.round(indicator.visualSettings.opacity * 100)}
              suffix="%"
            />
          </Col>
        </Row>
      </Card>

      {/* Quick Actions */}
      <Card title="快速操作" size="small">
        <Space wrap>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowParameterForm(true)}
          >
            添加到图表
          </Button>
          <Button icon={<CopyOutlined />} onClick={handleCopyFormula}>
            复制公式
          </Button>
          <Button icon={<ShareAltOutlined />}>
            分享
          </Button>
          <Button icon={<DownloadOutlined />}>
            导出配置
          </Button>
        </Space>
      </Card>
    </div>
  )

  const renderParametersTab = () => (
    <div>
      <Alert
        message="参数配置"
        description="调整参数以优化指标表现。修改参数后会实时更新预览。"
        type="info"
        showIcon
        className="mb-4"
      />

      <Card title="参数列表" size="small">
        <List
          dataSource={indicator.parameters}
          renderItem={(param) => (
            <List.Item key={param.name}>
              <List.Item.Meta
                avatar={
                  <div className="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
                    <CalculatorOutlined className="text-blue-600" />
                  </div>
                }
                title={
                  <Space>
                    <Text strong>{param.name}</Text>
                    <Tag size="small" color="geekblue">
                      {param.type}
                    </Tag>
                    {param.validation?.required && (
                      <Tag size="small" color="red">必填</Tag>
                    )}
                  </Space>
                }
                description={
                  <div>
                    <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                      {param.description}
                    </Paragraph>
                    <Space>
                      <Text>默认值: </Text>
                      <Text code>{String(param.defaultValue)}</Text>
                      {param.min !== undefined && (
                        <>
                          <Text>最小值: </Text>
                          <Text code>{param.min}</Text>
                        </>
                      )}
                      {param.max !== undefined && (
                        <>
                          <Text>最大值: </Text>
                          <Text code>{param.max}</Text>
                        </>
                      )}
                      {param.step !== undefined && (
                        <>
                          <Text>步长: </Text>
                          <Text code>{param.step}</Text>
                        </>
                      )}
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Card title="参数模板" size="small" className="mt-4">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="快速预设"
            description="选择常用的参数预设以快速配置"
            type="success"
          />
          {/* Parameter presets would go here */}
        </Space>
      </Card>
    </div>
  )

  const renderSignalsTab = () => (
    <div>
      <Alert
        message="交易信号"
        description="该指标生成的买入、卖出和中性信号规则"
        type="info"
        showIcon
        className="mb-4"
      />

      <Row gutter={16}>
        <Col span={8}>
          <Card
            title={
              <Space>
                <Badge count={indicator.signals?.buy?.length || 0}>
                  <span>买入信号</span>
                </Badge>
              </Space>
            }
            size="small"
          >
            {indicator.signals?.buy?.length ? (
              <Timeline>
                {indicator.signals.buy.map((signal, index) => (
                  <Timeline.Item
                    key={index}
                    color="green"
                    dot={<ThunderboltOutlined />}
                  >
                    <Text>{signal}</Text>
                  </Timeline.Item>
                ))}
              </Timeline>
            ) : (
              <Text type="secondary">暂无买入信号规则</Text>
            )}
          </Card>
        </Col>

        <Col span={8}>
          <Card
            title={
              <Space>
                <Badge count={indicator.signals?.sell?.length || 0}>
                  <span>卖出信号</span>
                </Badge>
              </Space>
            }
            size="small"
          >
            {indicator.signals?.sell?.length ? (
              <Timeline>
                {indicator.signals.sell.map((signal, index) => (
                  <Timeline.Item
                    key={index}
                    color="red"
                    dot={<ThunderboltOutlined />}
                  >
                    <Text>{signal}</Text>
                  </Timeline.Item>
                ))}
              </Timeline>
            ) : (
              <Text type="secondary">暂无卖出信号规则</Text>
            )}
          </Card>
        </Col>

        <Col span={8}>
          <Card
            title={
              <Space>
                <Badge count={indicator.signals?.neutral?.length || 0}>
                  <span>中性信号</span>
                </Badge>
              </Space>
            }
            size="small"
          >
            {indicator.signals?.neutral?.length ? (
              <Timeline>
                {indicator.signals.neutral.map((signal, index) => (
                  <Timeline.Item
                    key={index}
                    color="gray"
                    dot={<InfoCircleOutlined />}
                  >
                    <Text>{signal}</Text>
                  </Timeline.Item>
                ))}
              </Timeline>
            ) : (
              <Text type="secondary">暂无中性信号规则</Text>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )

  const renderFormulaTab = () => (
    <div>
      {indicator.formula && (
        <Card title="计算公式" size="small" className="mb-4">
          <div className="relative">
            <SyntaxHighlighter
              language="mathematica"
              style={tomorrow}
              customStyle={{
                borderRadius: 8,
                padding: 16,
                backgroundColor: '#f5f5f5'
              }}
            >
              {indicator.formula}
            </SyntaxHighlighter>
            <Button
              type="text"
              icon={<CopyOutlined />}
              className="absolute top-2 right-2"
              onClick={handleCopyFormula}
            />
          </div>
        </Card>
      )}

      {indicator.documentation?.usage && (
        <Card title="使用说明" size="small" className="mb-4">
          <Paragraph>{indicator.documentation.usage}</Paragraph>
        </Card>
      )}

      {indicator.documentation?.examples && (
        <Card title="使用示例" size="small" className="mb-4">
          <List
            dataSource={indicator.documentation.examples}
            renderItem={(example) => (
              <List.Item>
                <Paragraph>
                  <Text code>{example}</Text>
                </Paragraph>
              </List.Item>
            )}
          />
        </Card>
      )}

      {indicator.documentation?.bestPractices && (
        <Card title="最佳实践" size="small">
          <Collapse ghost>
            {indicator.documentation.bestPractices.map((practice, index) => (
              <Panel
                header={`实践 ${index + 1}`}
                key={index}
                extra={<BulbOutlined className="text-yellow-500" />}
              >
                <Paragraph>{practice}</Paragraph>
              </Panel>
            ))}
          </Collapse>
        </Card>
      )}
    </div>
  )

  const renderPerformanceTab = () => (
    <div>
      <Alert
        message="性能分析"
        description="查看该指标在不同市场条件下的历史表现"
        type="info"
        showIcon
        className="mb-4"
      />

      <IndicatorPerformanceChart indicatorId={indicator.id} />
    </div>
  )

  return (
    <div className="indicator-details">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <Title level={3} className="!mb-0">
            {indicator.name}
          </Title>
          {indicator.favorite && (
            <StarFilled className="text-yellow-500 text-xl" />
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: '概览',
            children: renderOverviewTab()
          },
          {
            key: 'parameters',
            label: '参数',
            children: renderParametersTab()
          },
          {
            key: 'signals',
            label: '信号',
            children: renderSignalsTab()
          },
          {
            key: 'formula',
            label: '公式',
            children: renderFormulaTab()
          },
          {
            key: 'performance',
            label: '性能',
            children: renderPerformanceTab()
          }
        ]}
      />

      {/* Parameter Form Modal */}
      <IndicatorParameterForm
        visible={showParameterForm}
        indicator={indicator}
        onSubmit={() => {
          setShowParameterForm(false)
          message.success('已添加到图表')
        }}
        onCancel={() => setShowParameterForm(false)}
      />
    </div>
  )
}

export default IndicatorDetails