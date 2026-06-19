import React, { memo, useMemo, useCallback, useState, useEffect } from 'react'
import { List } from 'react-window'
import AutoSizer from 'react-virtualized-auto-sizer'
import { Row, Col, Spin } from 'antd'
import OptimizedIndicatorCard from './OptimizedIndicatorCard'
import { TechnicalIndicator } from '../../types/technical-indicators'

interface VirtualizedIndicatorListProps {
  indicators: TechnicalIndicator[]
  onSelect: (indicator: TechnicalIndicator) => void
  onToggleFavorite: (indicatorId: string, e: React.MouseEvent) => void
  onAddToConfiguration: (indicator: TechnicalIndicator) => void
  loading?: boolean
  itemHeight?: number
  gap?: number
  columns?: {
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
    xxl?: number
  }
}

// 列表项组件
const ListItem = memo<{
  index: number
  style: React.CSSProperties
  data: {
    indicators: TechnicalIndicator[]
    columns: number
    onSelect: (indicator: TechnicalIndicator) => void
    onToggleFavorite: (indicatorId: string, e: React.MouseEvent) => void
    onAddToConfiguration: (indicator: TechnicalIndicator) => void
    gap: number
  }
}>(({ index, style, data }) => {
  const {
    indicators,
    columns,
    onSelect,
    onToggleFavorite,
    onAddToConfiguration,
    gap
  } = data

  // 计算当前行的指标
  const startIndex = index * columns
  const endIndex = Math.min(startIndex + columns, indicators.length)
  const rowIndicators = indicators.slice(startIndex, endIndex)

  return (
    <div style={style}>
      <Row gutter={[gap, gap]}>
        {rowIndicators.map((indicator) => (
          <Col
            key={indicator.id}
            xs={24 / columns}
            sm={24 / columns}
            md={24 / columns}
            lg={24 / columns}
            xl={24 / columns}
          >
            <OptimizedIndicatorCard
              indicator={indicator}
              onSelect={() => onSelect(indicator)}
              onToggleFavorite={(e) => onToggleFavorite(indicator.id, e)}
              onAddToConfiguration={() => onAddToConfiguration(indicator)}
            />
          </Col>
        ))}
      </Row>
    </div>
  )
})

ListItem.displayName = 'VirtualizedListItem'

const VirtualizedIndicatorList: React.FC<VirtualizedIndicatorListProps> = ({
  indicators,
  onSelect,
  onToggleFavorite,
  onAddToConfiguration,
  loading = false,
  itemHeight = 280,
  gap = 16,
  columns = {
    xs: 1,
    sm: 2,
    lg: 3,
    xl: 4,
    xxl: 5
  }
}) => {
  const [currentColumns, setCurrentColumns] = useState(columns.lg || 3)

  // 根据窗口大小计算列数
  const calculateColumns = useCallback(() => {
    const width = window.innerWidth
    if (width < 576) return columns.xs || 1
    if (width < 768) return columns.sm || 2
    if (width < 992) return columns.md || 3
    if (width < 1200) return columns.lg || 3
    if (width < 1600) return columns.xl || 4
    return columns.xxl || 5
  }, [columns])

  // 监听窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      setCurrentColumns(calculateColumns())
    }

    handleResize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [calculateColumns])

  // 计算行数
  const rowCount = useMemo(() => {
    return Math.ceil(indicators.length / currentColumns)
  }, [indicators.length, currentColumns])

  // 缓存列表项数据
  const itemData = useMemo(() => ({
    indicators,
    columns: currentColumns,
    onSelect,
    onToggleFavorite,
    onAddToConfiguration,
    gap
  }), [
    indicators,
    currentColumns,
    onSelect,
    onToggleFavorite,
    onAddToConfiguration,
    gap
  ])

  // 如果正在加载，显示加载中
  if (loading) {
    return (
      <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  // 如果没有数据，显示空状态
  if (indicators.length === 0) {
    return (
      <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#999' }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>📊</div>
          <div>暂无指标数据</div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: 'calc(100vh - 300px)', minHeight: 400 }}>
      <AutoSizer>
        {({ height, width }) => (
          <List
            height={height}
            width={width}
            itemCount={rowCount}
            itemSize={itemHeight}
            itemData={itemData}
            overscanCount={5} // 预渲染额外的行数
          >
            {ListItem}
          </List>
        )}
      </AutoSizer>
    </div>
  )
}

export default VirtualizedIndicatorList