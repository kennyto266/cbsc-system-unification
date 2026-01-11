import React, { useState, useEffect, useRef, useCallback, memo } from 'react'
import { Card, Statistic, Row, Col, Progress, Button, Tooltip, Switch } from 'antd'
import {
  DashboardOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  MemoryStickOutlined,
  DeleteOutlined,
  SettingOutlined
} from '@ant-design/icons'

interface PerformanceMetrics {
  fps: number
  memoryUsed: number
  renderTime: number
  componentCount: number
  reRenderCount: number
}

interface PerformanceMonitorProps {
  visible?: boolean
  onMetricsUpdate?: (metrics: PerformanceMetrics) => void
}

// 性能监控组件
const PerformanceMonitor = memo<PerformanceMonitorProps>(({
  visible = true,
  onMetricsUpdate
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    memoryUsed: 0,
    renderTime: 0,
    componentCount: 0,
    reRenderCount: 0
  })

  const [isMonitoring, setIsMonitoring] = useState(true)
  const frameCountRef = useRef(0)
  const lastTimeRef = useRef(performance.now())
  const renderTimesRef = useRef<number[]>([])
  const componentRenderCountsRef = useRef<Map<string, number>>(new Map())

  // 计算 FPS
  const calculateFPS = useCallback(() => {
    frameCountRef.current++
    const currentTime = performance.now()
    const deltaTime = currentTime - lastTimeRef.current

    if (deltaTime >= 1000) {
      const fps = Math.round((frameCountRef.current * 1000) / deltaTime)
      frameCountRef.current = 0
      lastTimeRef.current = currentTime

      setMetrics(prev => {
        const newMetrics = { ...prev, fps }
        onMetricsUpdate?.(newMetrics)
        return newMetrics
      })
    }

    if (isMonitoring) {
      requestAnimationFrame(calculateFPS)
    }
  }, [isMonitoring, onMetricsUpdate])

  // 监控内存使用
  const monitorMemory = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      const usedMB = Math.round(memory.usedJSHeapSize / 1048576)
      const totalMB = Math.round(memory.totalJSHeapSize / 1048576)

      setMetrics(prev => {
        const newMetrics = {
          ...prev,
          memoryUsed: Math.round((usedMB / totalMB) * 100)
        }
        onMetricsUpdate?.(newMetrics)
        return newMetrics
      })
    }
  }, [onMetricsUpdate])

  // 监控渲染性能
  const measureRenderTime = useCallback(() => {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'measure' && entry.name.startsWith('render-')) {
          const renderTime = entry.duration
          renderTimesRef.current.push(renderTime)

          // 只保留最近100次的渲染时间
          if (renderTimesRef.current.length > 100) {
            renderTimesRef.current.shift()
          }

          const avgRenderTime = renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length

          setMetrics(prev => {
            const newMetrics = {
              ...prev,
              renderTime: Math.round(avgRenderTime * 100) / 100
            }
            onMetricsUpdate?.(newMetrics)
            return newMetrics
          })
        }
      }
    })

    observer.observe({ entryTypes: ['measure'] })

    return () => {
      observer.disconnect()
    }
  }, [onMetricsUpdate])

  // 监控组件渲染次数
  const trackComponentRenders = useCallback(() => {
    // 使用 Proxy 或自定义装饰器来追踪组件渲染
    const originalCreateElement = React.createElement

    React.createElement = function(type: any, props: any, ...children: any[]) {
      if (typeof type === 'function' && type.name) {
        const count = componentRenderCountsRef.current.get(type.name) || 0
        componentRenderCountsRef.current.set(type.name, count + 1)

        const totalRenders = Array.from(componentRenderCountsRef.current.values())
          .reduce((sum, count) => sum + count, 0)

        setMetrics(prev => {
          const newMetrics = {
            ...prev,
            reRenderCount: totalRenders
          }
          onMetricsUpdate?.(newMetrics)
          return newMetrics
        })
      }

      return originalCreateElement.call(this, type, props, ...children)
    }
  }, [onMetricsUpdate])

  // 清除性能数据
  const clearMetrics = useCallback(() => {
    renderTimesRef.current = []
    componentRenderCountsRef.current.clear()

    setMetrics({
      fps: 60,
      memoryUsed: 0,
      renderTime: 0,
      componentCount: 0,
      reRenderCount: 0
    })
  }, [])

  // 强制垃圾回收（仅在支持的环境中）
  const forceGC = useCallback(() => {
    if ('gc' in window) {
      (window as any).gc()
    } else {
      console.log('Manual garbage collection not available')
    }
  }, [])

  // 初始化监控
  useEffect(() => {
    if (isMonitoring) {
      // 开始 FPS 监控
      requestAnimationFrame(calculateFPS)

      // 开始内存监控
      const memoryInterval = setInterval(monitorMemory, 2000)

      // 开始渲染性能监控
      const cleanupRenderMonitor = measureRenderTime()

      // 开始组件渲染追踪
      trackComponentRenders()

      return () => {
        clearInterval(memoryInterval)
        cleanupRenderMonitor()
      }
    }
  }, [isMonitoring, calculateFPS, monitorMemory, measureRenderTime, trackComponentRenders])

  if (!visible) {
    return null
  }

  // 获取性能状态
  const getPerformanceStatus = () => {
    if (metrics.fps >= 55 && metrics.renderTime <= 16 && metrics.memoryUsed <= 80) {
      return { status: 'success', color: '#52c41a', text: '优秀' }
    } else if (metrics.fps >= 30 && metrics.renderTime <= 33 && metrics.memoryUsed <= 90) {
      return { status: 'normal', color: '#faad14', text: '正常' }
    } else {
      return { status: 'poor', color: '#ff4d4f', text: '需优化' }
    }
  }

  const performanceStatus = getPerformanceStatus()

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span className="flex items-center">
            <DashboardOutlined className="mr-2" />
            性能监控
          </span>
          <Switch
            checked={isMonitoring}
            onChange={setIsMonitoring}
            size="small"
            checkedChildren="监控中"
            unCheckedChildren="已暂停"
          />
        </div>
      }
      size="small"
      className="performance-monitor"
      extra={
        <Space>
          <Tooltip title="清除数据">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              onClick={clearMetrics}
            />
          </Tooltip>
          <Tooltip title="垃圾回收">
            <Button
              type="text"
              size="small"
              icon={<ThunderboltOutlined />}
              onClick={forceGC}
            />
          </Tooltip>
          <Tooltip title="高级设置">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
            />
          </Tooltip>
        </Space>
      }
    >
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="帧率 (FPS)"
            value={metrics.fps}
            prefix={<DashboardOutlined />}
            valueStyle={{
              color: metrics.fps >= 55 ? '#52c41a' : metrics.fps >= 30 ? '#faad14' : '#ff4d4f'
            }}
            suffix="/ 60"
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="内存使用"
            value={metrics.memoryUsed}
            prefix={<MemoryStickOutlined />}
            suffix="%"
            valueStyle={{
              color: metrics.memoryUsed <= 80 ? '#52c41a' : metrics.memoryUsed <= 90 ? '#faad14' : '#ff4d4f'
            }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="渲染时间"
            value={metrics.renderTime}
            prefix={<ClockCircleOutlined />}
            suffix="ms"
            valueStyle={{
              color: metrics.renderTime <= 16 ? '#52c41a' : metrics.renderTime <= 33 ? '#faad14' : '#ff4d4f'
            }}
          />
        </Col>
      </Row>

      <div className="mt-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">整体性能</span>
          <span
            className="text-sm font-medium"
            style={{ color: performanceStatus.color }}
          >
            {performanceStatus.text}
          </span>
        </div>
        <Progress
          percent={Math.round(
            (metrics.fps / 60 * 0.4 + (100 - metrics.renderTime) / 100 * 0.3 + (100 - metrics.memoryUsed) * 0.3) * 100
          )}
          strokeColor={performanceStatus.color}
          size="small"
          showInfo={false}
        />
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100">
        <Row gutter={16}>
          <Col span={12}>
            <div className="text-center">
              <div className="text-lg font-semibold">{metrics.reRenderCount}</div>
              <div className="text-xs text-gray-500">组件重渲染次数</div>
            </div>
          </Col>
          <Col span={12}>
            <div className="text-center">
              <div className="text-lg font-semibold">{componentRenderCountsRef.current.size}</div>
              <div className="text-xs text-gray-500">活跃组件数</div>
            </div>
          </Col>
        </Row>
      </div>
    </Card>
  )
})

PerformanceMonitor.displayName = 'PerformanceMonitor'

export default PerformanceMonitor