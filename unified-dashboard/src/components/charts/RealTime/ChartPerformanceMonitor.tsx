import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, Row, Col, Statistic, Progress, Tag, Button, Space, Tooltip, Switch } from 'antd'
import {
  DashboardOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  SettingOutlined,
  ReloadOutlined
} from '@ant-design/icons'

// Performance metrics interface
export interface PerformanceMetrics {
  fps: number
  renderTime: number
  dataPoints: number
  memoryUsage: number
  updateFrequency: number
  droppedFrames: number
  lastUpdate: Date
}

// Props interface
export interface ChartPerformanceMonitorProps {
  visible: boolean
  metrics: PerformanceMetrics
  onOptimize?: () => void
  onReset?: () => void
  onSettings?: () => void
}

// Performance thresholds
const PERFORMANCE_THRESHOLDS = {
  fps: { good: 55, warning: 30, bad: 15 },
  renderTime: { good: 16, warning: 33, bad: 100 }, // ms
  memoryUsage: { good: 50, warning: 100, bad: 200 }, // MB
  updateFrequency: { good: 60, warning: 30, bad: 10 } // updates per second
}

// Get performance status
const getPerformanceStatus = (value: number, thresholds: any) => {
  if (value >= thresholds.good) return { status: 'success', color: 'green' }
  if (value >= thresholds.warning) return { status: 'warning', color: 'orange' }
  return { status: 'exception', color: 'red' }
}

// Format memory usage
const formatMemoryUsage = (bytes: number): string => {
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}

// Main component
const ChartPerformanceMonitor: React.FC<ChartPerformanceMonitorProps> = ({
  visible,
  metrics,
  onOptimize,
  onReset,
  onSettings
}) => {
  const [isMonitoring, setIsMonitoring] = useState(true)
  const [historicalData, setHistoricalData] = useState<PerformanceMetrics[]>([])
  const maxHistoryLength = 100

  // Update historical data
  useEffect(() => {
    if (!isMonitoring) return

    const interval = setInterval(() => {
      setHistoricalData(prev => {
        const updated = [...prev, metrics]
        return updated.slice(-maxHistoryLength)
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isMonitoring, metrics])

  // Calculate averages
  const averages = useMemo(() => {
    if (historicalData.length === 0) return null

    const sum = historicalData.reduce(
      (acc, curr) => ({
        fps: acc.fps + curr.fps,
        renderTime: acc.renderTime + curr.renderTime,
        memoryUsage: acc.memoryUsage + curr.memoryUsage,
        updateFrequency: acc.updateFrequency + curr.updateFrequency,
        droppedFrames: acc.droppedFrames + curr.droppedFrames
      }),
      { fps: 0, renderTime: 0, memoryUsage: 0, updateFrequency: 0, droppedFrames: 0 }
    )

    const count = historicalData.length
    return {
      fps: sum.fps / count,
      renderTime: sum.renderTime / count,
      memoryUsage: sum.memoryUsage / count,
      updateFrequency: sum.updateFrequency / count,
      droppedFrames: sum.droppedFrames / count
    }
  }, [historicalData])

  // Get performance grade
  const getOverallGrade = useCallback(() => {
    if (!averages) return 'N/A'

    const scores = [
      averages.fps >= PERFORMANCE_THRESHOLDS.fps.good ? 1 : 0,
      averages.renderTime <= PERFORMANCE_THRESHOLDS.renderTime.good ? 1 : 0,
      averages.memoryUsage <= PERFORMANCE_THRESHOLDS.memoryUsage.good ? 1 : 0,
      averages.updateFrequency >= PERFORMANCE_THRESHOLDS.updateFrequency.good ? 1 : 0
    ]

    const score = scores.reduce((a, b) => a + b, 0)
    if (score === 4) return { grade: 'A', color: 'green' }
    if (score === 3) return { grade: 'B', color: 'blue' }
    if (score === 2) return { grade: 'C', color: 'orange' }
    return { grade: 'D', color: 'red' }
  }, [averages])

  if (!visible) return null

  const grade = getOverallGrade()

  return (
    <Card
      title={
        <Space>
          <DashboardOutlined />
          Chart Performance Monitor
          <Tag color={grade?.color}>Grade {grade?.grade}</Tag>
        </Space>
      }
      size="small"
      extra={
        <Space>
          <Switch
            checked={isMonitoring}
            onChange={setIsMonitoring}
            size="small"
          />
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={onReset}
          />
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            onClick={onSettings}
          />
        </Space>
      }
    >
      <Row gutter={[16, 16]}>
        {/* Real-time Metrics */}
        <Col span={24}>
          <Row gutter={[16, 0]}>
            <Col span={6}>
              <Statistic
                title="FPS"
                value={metrics.fps}
                precision={0}
                valueStyle={{
                  color: getPerformanceStatus(metrics.fps, PERFORMANCE_THRESHOLDS.fps).color
                }}
                prefix={<ThunderboltOutlined />}
                suffix={
                  <Tag
                    color={getPerformanceStatus(metrics.fps, PERFORMANCE_THRESHOLDS.fps).color}
                    size="small"
                  >
                    {getPerformanceStatus(metrics.fps, PERFORMANCE_THRESHOLDS.fps).status}
                  </Tag>
                }
              />
            </Col>

            <Col span={6}>
              <Statistic
                title="Render Time"
                value={metrics.renderTime}
                precision={1}
                suffix="ms"
                valueStyle={{
                  color: getPerformanceStatus(1000/metrics.renderTime, PERFORMANCE_THRESHOLDS.renderTime).color
                }}
                prefix={<ClockCircleOutlined />}
              />
            </Col>

            <Col span={6}>
              <Statistic
                title="Memory"
                value={formatMemoryUsage(metrics.memoryUsage)}
                valueStyle={{
                  color: getPerformanceStatus(1000/metrics.memoryUsage, PERFORMANCE_THRESHOLDS.memoryUsage).color
                }}
                prefix={<DatabaseOutlined />}
              />
            </Col>

            <Col span={6}>
              <Statistic
                title="Updates/sec"
                value={metrics.updateFrequency}
                precision={1}
                valueStyle={{
                  color: getPerformanceStatus(metrics.updateFrequency, PERFORMANCE_THRESHOLDS.updateFrequency).color
                }}
                prefix={<ThunderboltOutlined />}
              />
            </Col>
          </Row>
        </Col>

        {/* Performance Bars */}
        <Col span={24}>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">Frame Rate</span>
                <span className="text-sm">{metrics.fps.toFixed(0)} / 60 FPS</span>
              </div>
              <Progress
                percent={(metrics.fps / 60) * 100}
                status={getPerformanceStatus(metrics.fps, PERFORMANCE_THRESHOLDS.fps).status}
                showInfo={false}
                size="small"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">Render Speed</span>
                <span className="text-sm">{metrics.renderTime.toFixed(1)}ms</span>
              </div>
              <Progress
                percent={Math.min((metrics.renderTime / 16.67) * 100, 100)}
                status={getPerformanceStatus(1000/metrics.renderTime, PERFORMANCE_THRESHOLDS.renderTime).status}
                showInfo={false}
                size="small"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">Memory Usage</span>
                <span className="text-sm">{formatMemoryUsage(metrics.memoryUsage)}</span>
              </div>
              <Progress
                percent={(metrics.memoryUsage / (512 * 1024 * 1024)) * 100} // 512MB max
                status={getPerformanceStatus(1000/metrics.memoryUsage, PERFORMANCE_THRESHOLDS.memoryUsage).status}
                showInfo={false}
                size="small"
              />
            </div>
          </div>
        </Col>

        {/* Averages */}
        {averages && (
          <Col span={24}>
            <div className="border-t pt-2">
              <h4 className="text-sm font-medium mb-2">Averages (Last {historicalData.length}s)</h4>
              <Row gutter={[16, 0]}>
                <Col span={6}>
                  <Statistic
                    title="Avg FPS"
                    value={averages.fps}
                    precision={1}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Avg Render"
                    value={averages.renderTime}
                    precision={1}
                    suffix="ms"
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Avg Memory"
                    value={formatMemoryUsage(averages.memoryUsage)}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Total Dropped"
                    value={averages.droppedFrames}
                    precision={0}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
              </Row>
            </div>
          </Col>
        )}

        {/* Optimization Suggestions */}
        <Col span={24}>
          <div className="border-t pt-2">
            <h4 className="text-sm font-medium mb-2">Optimization Suggestions</h4>
            <div className="space-y-1">
              {metrics.fps < 30 && (
                <Tag color="orange">Reduce animation complexity</Tag>
              )}
              {metrics.renderTime > 33 && (
                <Tag color="red">Lower data point count</Tag>
              )}
              {metrics.memoryUsage > 100 * 1024 * 1024 && (
                <Tag color="orange">Clear unused data</Tag>
              )}
              {metrics.updateFrequency < 10 && (
                <Tag color="blue">Check WebSocket connection</Tag>
              )}
              {metrics.fps >= 55 && metrics.renderTime <= 16 && (
                <Tag color="green">Performance optimal</Tag>
              )}
            </div>
            <div className="mt-2">
              <Button
                type="primary"
                size="small"
                onClick={onOptimize}
                block
              >
                Auto Optimize
              </Button>
            </div>
          </div>
        </Col>
      </Row>
    </Card>
  )
}

export default ChartPerformanceMonitor