import React, { useState, useCallback, useMemo } from 'react'
import {
  Card,
  List,
  Button,
  Space,
  Switch,
  Slider,
  Select,
  ColorPicker,
  Input,
  Typography,
  Row,
  Col,
  Divider,
  Tag,
  Tooltip,
  Alert,
  Modal,
  Form,
  InputNumber,
  message,
  Tree,
  Dropdown,
  MenuProps
} from 'antd'
import {
  SettingOutlined,
  DeleteOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  PlusOutlined,
  DragOutlined,
  SaveOutlined,
  CopyOutlined,
  ShareAltOutlined,
  DownloadOutlined,
  UploadOutlined,
  MoreOutlined,
  FullscreenOutlined,
  CompressOutlined,
  UnorderedListOutlined,
  AppstoreOutlined
} from '@ant-design/icons'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import type { Color } from 'antd/es/color-picker'
import { Rnd } from 'react-rnd'

import { TechnicalIndicator, IndicatorConfiguration } from '../../types/technical-indicators'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import {
  saveConfiguration,
  selectConfigurationsByUser
} from '../../store/slices/technicalIndicatorsSlice'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface DraggableIndicatorItemProps {
  indicator: TechnicalIndicator & { id: string; enabled: boolean; config?: any }
  index: number
  moveIndicator: (dragIndex: number, hoverIndex: number) => void
  onToggle: (id: string) => void
  onEdit: (indicator: TechnicalIndicator) => void
  onDelete: (id: string) => void
  onConfigChange: (id: string, config: any) => void
}

const DraggableIndicatorItem: React.FC<DraggableIndicatorItemProps> = ({
  indicator,
  index,
  moveIndicator,
  onToggle,
  onEdit,
  onDelete,
  onConfigChange
}) => {
  const ref = React.useRef<HTMLDivElement>(null)

  const [{ handlerId }, drop] = useDrop({
    accept: 'indicator',
    collect(monitor) {
      return {
        handlerId: monitor.getHandlerId(),
      }
    },
    hover(item: any, monitor) {
      if (!ref.current) {
        return
      }
      const dragIndex = item.index
      const hoverIndex = index
      if (dragIndex === hoverIndex) {
        return
      }
      const hoverBoundingRect = ref.current?.getBoundingClientRect()
      const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2
      const clientOffset = monitor.getClientOffset()
      const hoverClientY = clientOffset!.y - hoverBoundingRect.top
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return
      }
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return
      }
      moveIndicator(dragIndex, hoverIndex)
      item.index = hoverIndex
    },
  })

  const [{ isDragging }, drag] = useDrag({
    type: 'indicator',
    item: () => {
      return { index }
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  })

  drag(drop(ref))

  const moreMenuItems: MenuProps['items'] = [
    {
      key: 'edit',
      icon: <SettingOutlined />,
      label: '编辑参数',
      onClick: () => onEdit(indicator)
    },
    {
      key: 'duplicate',
      icon: <CopyOutlined />,
      label: '复制指标',
      onClick: () => {
        // Handle duplication
      }
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true,
      onClick: () => onDelete(indicator.id)
    }
  ]

  return (
    <div
      ref={ref}
      className={`bg-white rounded-lg shadow-sm border ${isDragging ? 'opacity-50' : ''} mb-2`}
      style={{ cursor: 'move' }}
      data-handler-id={handlerId}
    >
      <List.Item
        actions={[
          <Switch
            checked={indicator.enabled}
            onChange={() => onToggle(indicator.id)}
            size="small"
          />,
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => onEdit(indicator)}
          />,
          <Dropdown
            menu={{ items: moreMenuItems }}
            trigger={['click']}
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        ]}
      >
        <List.Item.Meta
          avatar={
            <div className="w-8 h-8 rounded flex items-center justify-center">
              <div
                className="w-4 h-4 rounded"
                style={{
                  backgroundColor: indicator.config?.visualSettings?.color || indicator.visualSettings.color
                }}
              />
            </div>
          }
          title={
            <Space>
              <Text strong={!indicator.enabled} style={{ opacity: indicator.enabled ? 1 : 0.5 }}>
                {indicator.name}
              </Text>
              <Tag color="blue" size="small">{indicator.type}</Tag>
            </Space>
          }
          description={
            <Space direction="vertical" style={{ width: '100%', opacity: indicator.enabled ? 1 : 0.5 }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {indicator.description}
              </Text>
              {/* Quick visual settings */}
              {indicator.config?.visualSettings && (
                <Row gutter={8} style={{ marginTop: 8 }}>
                  <Col>
                    <ColorPicker
                      size="small"
                      value={indicator.config.visualSettings.color}
                      onChange={(color: Color) =>
                        onConfigChange(indicator.id, {
                          ...indicator.config,
                          visualSettings: {
                            ...indicator.config.visualSettings,
                            color: color.toHexString()
                          }
                        })
                      }
                    />
                  </Col>
                  <Col flex="auto">
                    <Slider
                      min={1}
                      max={5}
                      value={indicator.config.visualSettings.lineWidth}
                      onChange={(value) =>
                        onConfigChange(indicator.id, {
                          ...indicator.config,
                          visualSettings: {
                            ...indicator.config.visualSettings,
                            lineWidth: value
                          }
                        })
                      }
                      style={{ marginTop: 8 }}
                    />
                  </Col>
                </Row>
              )}
            </Space>
          }
        />
      </List.Item>
    </div>
  )
}

interface ChartLayoutItem {
  id: string
  indicators: string[]
  width: number
  height: number
  x: number
  y: number
}

interface ConfigurationPanelProps {
  indicators: TechnicalIndicator[]
  initialConfig?: IndicatorConfiguration
  onClose?: () => void
  onSave?: (config: IndicatorConfiguration) => void
  mode?: 'create' | 'edit'
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  indicators,
  initialConfig,
  onClose,
  onSave,
  mode = 'create'
}) => {
  const dispatch = useAppDispatch()
  const [form] = Form.useForm()

  const [configuredIndicators, setConfiguredIndicators] = useState<any[]>(() =>
    indicators.map(ind => ({
      ...ind,
      id: ind.id,
      enabled: true,
      config: {
        parameters: ind.parameters.reduce((acc, param) => {
          acc[param.name] = param.defaultValue
          return acc
        }, {} as Record<string, any>),
        visualSettings: ind.visualSettings
      }
    }))
  )

  const [layoutMode, setLayoutMode] = useState<'list' | 'grid'>('list')
  const [chartLayout, setChartLayout] = useState<ChartLayoutItem[]>([
    {
      id: 'main',
      indicators: indicators.map(ind => ind.id),
      width: 100,
      height: 400,
      x: 0,
      y: 0
    }
  ])
  const [configName, setConfigName] = useState(initialConfig?.name || '')
  const [configDescription, setConfigDescription] = useState(initialConfig?.description || '')
  const [isPublic, setIsPublic] = useState(initialConfig?.isPublic || false)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [tags, setTags] = useState<string[]>(initialConfig?.tags || [])

  const moveIndicator = useCallback((dragIndex: number, hoverIndex: number) => {
    setConfiguredIndicators((prevIndicators) => {
      const newIndicators = [...prevIndicators]
      const [removed] = newIndicators.splice(dragIndex, 1)
      newIndicators.splice(hoverIndex, 0, removed)
      return newIndicators
    })
  }, [])

  const handleToggleIndicator = (id: string) => {
    setConfiguredIndicators(prev =>
      prev.map(ind =>
        ind.id === id ? { ...ind, enabled: !ind.enabled } : ind
      )
    )
  }

  const handleEditIndicator = (indicator: TechnicalIndicator) => {
    // Open parameter edit modal
    Modal.info({
      title: `编辑 ${indicator.name}`,
      width: 800,
      content: (
        <div>
          <Paragraph>编辑指标的参数和视觉设置</Paragraph>
          {/* Parameter form would go here */}
        </div>
      )
    })
  }

  const handleDeleteIndicator = (id: string) => {
    setConfiguredIndicators(prev => prev.filter(ind => ind.id !== id))
  }

  const handleConfigChange = (id: string, config: any) => {
    setConfiguredIndicators(prev =>
      prev.map(ind =>
        ind.id === id ? { ...ind, config } : ind
      )
    )
  }

  const handleSaveConfiguration = async () => {
    try {
      const configuration: IndicatorConfiguration = {
        id: initialConfig?.id || `config-${Date.now()}`,
        userId: 'current-user', // Would come from auth context
        name: configName,
        indicators: configuredIndicators.map(ind => ({
          indicatorId: ind.id,
          parameters: ind.config.parameters,
          enabled: ind.enabled,
          visualSettings: ind.config.visualSettings
        })),
        layout: {
          grid: 2,
          charts: chartLayout
        },
        timeframe: '1h',
        symbol: 'BTC/USDT',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isPublic,
        tags
      }

      dispatch(saveConfiguration(configuration))
      onSave?.(configuration)
      message.success('配置已保存')
      onClose?.()
    } catch (error) {
      message.error('保存失败')
    }
  }

  const exportConfiguration = () => {
    const config = {
      name: configName,
      indicators: configuredIndicators,
      layout: chartLayout
    }
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${configName.replace(/\s+/g, '_')}_config.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const renderListMode = () => (
    <List
      dataSource={configuredIndicators}
      renderItem={(indicator, index) => (
        <DraggableIndicatorItem
          key={indicator.id}
          indicator={indicator}
          index={index}
          moveIndicator={moveIndicator}
          onToggle={handleToggleIndicator}
          onEdit={handleEditIndicator}
          onDelete={handleDeleteIndicator}
          onConfigChange={handleConfigChange}
        />
      )}
    />
  )

  const renderGridMode = () => (
    <div style={{ height: 600, position: 'relative', background: '#f0f0f0', borderRadius: 8 }}>
      {chartLayout.map((item) => (
        <Rnd
          key={item.id}
          default={{
            x: item.x,
            y: item.y,
            width: item.width,
            height: item.height
          }}
          onDragStop={(e, d) => {
            setChartLayout(prev =>
              prev.map(lay =>
                lay.id === item.id ? { ...lay, x: d.x, y: d.y } : lay
              )
            )
          }}
          onResizeStop={(e, direction, ref, delta, position) => {
            setChartLayout(prev =>
              prev.map(lay =>
                lay.id === item.id
                  ? { ...lay, width: ref.offsetWidth, height: ref.offsetHeight, x: position.x, y: position.y }
                  : lay
              )
            )
          }}
          style={{ border: '1px solid #d9d9d9', background: 'white' }}
        >
          <Card
            size="small"
            title={`图表 ${item.id}`}
            extra={<Button type="text" size="small" icon={<SettingOutlined />} />}
            style={{ height: '100%' }}
          >
            <div style={{ overflowY: 'auto', height: 'calc(100% - 40px)' }}>
              {item.indicators.map(indId => {
                const ind = configuredIndicators.find(c => c.id === indId)
                return ind ? (
                  <Tag
                    key={indId}
                    color={ind.enabled ? 'blue' : 'default'}
                    style={{ margin: 4 }}
                  >
                    {ind.name}
                  </Tag>
                ) : null
              })}
            </div>
          </Card>
        </Rnd>
      ))}
    </div>
  )

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="configuration-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Card size="small" className="mb-4">
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={4} className="!mb-0">
                指标配置
              </Title>
            </Col>
            <Col>
              <Space>
                <Button
                  type={layoutMode === 'list' ? 'primary' : 'default'}
                  size="small"
                  icon={<UnorderedListOutlined />}
                  onClick={() => setLayoutMode('list')}
                >
                  列表视图
                </Button>
                <Button
                  type={layoutMode === 'grid' ? 'primary' : 'default'}
                  size="small"
                  icon={<AppstoreOutlined />}
                  onClick={() => setLayoutMode('grid')}
                >
                  布局视图
                </Button>
                <Divider type="vertical" />
                <Button size="small" icon={<DownloadOutlined />} onClick={exportConfiguration}>
                  导出配置
                </Button>
                <Button size="small" icon={<SaveOutlined />} onClick={() => setShowSaveModal(true)}>
                  保存配置
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Configuration Info */}
        <Card size="small" className="mb-4">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="配置名称">
                <Input
                  value={configName}
                  onChange={(e) => setConfigName(e.target.value)}
                  placeholder="输入配置名称"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="描述">
                <Input
                  value={configDescription}
                  onChange={(e) => setConfigDescription(e.target.value)}
                  placeholder="输入配置描述"
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Main Content */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {layoutMode === 'list' ? renderListMode() : renderGridMode()}
        </div>

        {/* Footer Stats */}
        <Card size="small" className="mt-4">
          <Row gutter={16}>
            <Col span={6}>
              <Text>
                总指标数: <Text strong>{configuredIndicators.length}</Text>
              </Text>
            </Col>
            <Col span={6}>
              <Text>
                已启用: <Text strong>{configuredIndicators.filter(ind => ind.enabled).length}</Text>
              </Text>
            </Col>
            <Col span={6}>
              <Text>
                图表数: <Text strong>{chartLayout.length}</Text>
              </Text>
            </Col>
            <Col span={6}>
              <Text>
                公开: <Text strong>{isPublic ? '是' : '否'}</Text>
              </Text>
            </Col>
          </Row>
        </Card>

        {/* Save Modal */}
        <Modal
          title="保存配置"
          open={showSaveModal}
          onOk={handleSaveConfiguration}
          onCancel={() => setShowSaveModal(false)}
        >
          <Form layout="vertical">
            <Form.Item label="配置名称" required>
              <Input
                value={configName}
                onChange={(e) => setConfigName(e.target.value)}
                placeholder="输入配置名称"
              />
            </Form.Item>
            <Form.Item label="描述">
              <TextArea
                value={configDescription}
                onChange={(e) => setConfigDescription(e.target.value)}
                placeholder="输入配置描述"
                rows={3}
              />
            </Form.Item>
            <Form.Item label="标签">
              <Select
                mode="tags"
                value={tags}
                onChange={setTags}
                placeholder="添加标签"
                style={{ width: '100%' }}
              />
            </Form.Item>
            <Form.Item label="公开设置">
              <Switch
                checked={isPublic}
                onChange={setIsPublic}
              />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  公开的配置可以被其他用户查看和使用
                </Text>
              </div>
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </DndProvider>
  )
}

export default ConfigurationPanel