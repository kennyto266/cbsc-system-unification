import React, { useMemo, useCallback, useState, lazy, Suspense } from 'react'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

// Vite-compatible lazy import of Plotly (no next/dynamic needed)
const Plot = lazy(() => import('react-plotly.js'))

export interface SunburstNode {
  id: string
  name: string
  value: number
  parent?: string
  color?: string
  metadata?: Record<string, any>
  children?: SunburstNode[]
}

export interface SunburstChartProps {
  data: SunburstNode[]
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    background?: string
    text?: string
    levels?: string[]
  }
  valueFormat?: 'decimal' | 'currency' | 'percentage'
  colorBy?: 'value' | 'category' | 'depth'
  maxDepth?: number
  branchValues?: 'total' | 'remainder'
  sortValues?: boolean
  showPath?: boolean
  onNodeClick?: (node: SunburstNode) => void
  onNodeHover?: (node: SunburstNode | null) => void
  animationDuration?: number
  fontSize?: number
  showValues?: boolean
  showLabels?: boolean
  hole?: number // Size of center hole (0-1)
}

export interface SunburstChartRef {
  exportChart: (format: 'png' | 'svg' | 'pdf') => Promise<void>
  zoomToNode: (nodeId: string) => void
  resetZoom: () => void
  getLayout: () => any
}

const SunburstChart = forwardRef<SunburstChartRef, SunburstChartProps>(({
  data,
  width = 800,
  height = 600,
  title,
  subtitle,
  loading,
  error,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    background: '#ffffff',
    text: '#000000',
    levels: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
  },
  valueFormat = 'decimal',
  colorBy = 'value',
  maxDepth = 4,
  branchValues = 'total',
  sortValues = true,
  showPath = true,
  onNodeClick,
  onNodeHover,
  animationDuration = 750,
  fontSize = 12,
  showValues = true,
  showLabels = true,
  hole = 0,
}, ref) => {
  const plotRef = useRef<any>(null)
  const [isClient, setIsClient] = useState(false)
  const [currentPath, setCurrentPath] = useState<string[]>([])

  useEffect(() => {
    setIsClient(true)
  }, [])

  // Format value
  const formatValue = useCallback((value: number): string => {
    switch (valueFormat) {
      case 'percentage':
        return `${value.toFixed(1)}%`
      case 'currency':
        return chartUtils.formatCurrency(value)
      default:
        return chartUtils.formatNumber(value)
    }
  }, [valueFormat])

  // Build hierarchical structure for Plotly
  const buildPlotlyData = useCallback((nodes: SunburstNode[]): any => {
    const nodeMap = new Map<string, any>()
    const result: any[] = []

    // Create node map with all nodes
    nodes.forEach(node => {
      nodeMap.set(node.id, {
        ...node,
        ids: [],
        labels: [],
        values: [],
        parents: [],
        colors: [],
      })
    })

    // Build hierarchical structure
    const processNode = (node: SunburstNode, parent: string = ''): void => {
      const plotlyNode = nodeMap.get(node.id)
      if (!plotlyNode) return

      plotlyNode.ids.push(node.id)
      plotlyNode.labels.push(node.name)
      plotlyNode.values.push(node.value)
      plotlyNode.parents.push(parent)

      if (node.children) {
        node.children.forEach(child => processNode(child, node.id))
      }
    }

    // Process all root nodes
    nodes
      .filter(node => !node.parent)
      .forEach(node => processNode(node))

    // Combine all data
    const allIds: string[] = []
    const allLabels: string[] = []
    const allValues: number[] = []
    const allParents: string[] = []
    const allColors: string[] = []

    nodeMap.forEach(node => {
      allIds.push(...node.ids)
      allLabels.push(...node.labels)
      allValues.push(...node.values)
      allParents.push(...node.parents)
    })

    // Generate colors
    const nodeColors = generateColors(allLabels)

    return {
      ids: allIds,
      labels: allLabels,
      values: allValues,
      parents: allParents,
      colors: nodeColors,
    }
  }, [])

  // Generate colors based on strategy
  const generateColors = useCallback((labels: string[]): string[] => {
    if (colorBy === 'category') {
      // Use predefined colors for different categories
      return labels.map((label, index) => {
        const node = data.find(n => n.name === label)
        return node?.color || colors.levels![index % colors.levels!.length]
      })
    } else if (colorBy === 'depth') {
      // Calculate depth for each label
      const getDepth = (label: string, currentDepth = 0): number => {
        const node = data.find(n => n.name === label)
        if (!node || !node.parent) return currentDepth

        const parent = data.find(n => n.id === node.parent)
        if (!parent) return currentDepth

        return getDepth(parent.name, currentDepth + 1)
      }

      return labels.map(label => {
        const depth = getDepth(label)
        return colors.levels![depth % colors.levels!.length]
      })
    } else {
      // Color by value
      return labels.map(label => {
        const node = data.find(n => n.name === label)
        const value = node?.value || 0

        const values = data.map(n => n.value)
        const minValue = Math.min(...values)
        const maxValue = Math.max(...values)

        const normalized = (value - minValue) / (maxValue - minValue)
        const hue = (1 - normalized) * 240 // Blue (240) to Red (0)
        return `hsl(${hue}, 70%, 50%)`
      })
    }
  }, [colorBy, data, colors])

  // Transform data for Plotly sunburst
  const plotlyData = useMemo(() => {
    if (!data || data.length === 0) return []

    const hierarchicalData = buildPlotlyData(data)

    // Generate text for each segment
    const text = hierarchicalData.labels.map((label: string, index: number) => {
      const value = hierarchicalData.values[index]
      const parts = []

      if (showLabels) parts.push(label)
      if (showValues) parts.push(formatValue(value))

      return parts.join('<br>')
    })

    return [{
      type: 'sunburst',
      ids: hierarchicalData.ids,
      labels: hierarchicalData.labels,
      values: hierarchicalData.values,
      parents: hierarchicalData.parents,
      branchvalues: branchValues,
      hovertemplate: '%{label}<br>%{value}<extra></extra>',
      textinfo: showValues || showLabels ? 'text' : 'none',
      text: text,
      marker: {
        colors: hierarchicalData.colors,
        line: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          width: 1,
        },
      },
      textfont: {
        size: fontSize,
        color: theme === 'dark' ? '#ffffff' : '#000000',
      },
      maxdepth: maxDepth,
      hole: hole,
      sort: sortValues,
    }]
  }, [
    data,
    buildPlotlyData,
    showValues,
    showLabels,
    formatValue,
    theme,
    fontSize,
    maxDepth,
    hole,
    sortValues,
    branchValues,
  ])

  // Plotly layout
  const layout = useMemo(() => {
    const isDark = theme === 'dark'
    const bgColor = isDark ? '#1a1a1a' : colors.background
    const textColor = isDark ? '#ffffff' : colors.text

    return {
      title: {
        text: title,
        font: {
          size: 18,
          color: textColor,
        },
      },
      paper_bgcolor: bgColor,
      plot_bgcolor: bgColor,
      font: {
        color: textColor,
      },
      showlegend: showLegend,
      hovermode: showTooltip ? 'closest' : false,
      margin: {
        l: 0,
        r: 0,
        t: title ? 40 : 0,
        b: 0,
        pad: 4,
      },
      annotations: subtitle ? [
        {
          text: subtitle,
          xref: 'paper',
          yref: 'paper',
          x: 0,
          y: 1,
          xanchor: 'left',
          yanchor: 'bottom',
          font: {
            size: 12,
            color: textColor,
          },
          showarrow: false,
        },
      ] : [],
      sunburstcolorway: colors.levels,
      extendsunburstcolorway: true,
      ...(showPath && currentPath.length > 0 ? {
        annotations: [
          ...subtitle ? [{
            text: subtitle,
            xref: 'paper',
            yref: 'paper',
            x: 0,
            y: 1,
            xanchor: 'left',
            yanchor: 'bottom',
            font: {
              size: 12,
              color: textColor,
            },
            showarrow: false,
          }] : [],
          {
            text: `Path: ${currentPath.join(' > ')}`,
            xref: 'paper',
            yref: 'paper',
            x: 0,
            y: -0.05,
            xanchor: 'left',
            yanchor: 'top',
            font: {
              size: 10,
              color: textColor,
            },
            showarrow: false,
          },
        ],
      } : {}),
    }
  }, [title, subtitle, theme, colors, showLegend, showTooltip, showPath, currentPath])

  // Plotly config
  const config = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['toImage'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'sunburst',
      height: height,
      width: width,
      scale: 2,
    },
    responsive: true,
  }), [width, height])

  // Chart ref methods
  useImperativeHandle(ref, () => ({
    exportChart: async (format: 'png' | 'svg' | 'pdf' = 'png') => {
      if (plotRef.current) {
        await plotRef.current.downloadImage(format, `sunburst-${Date.now()}`)
      }
    },
    zoomToNode: (nodeId: string) => {
      if (plotRef.current) {
        // Implementation for zooming to specific node
        console.log('Zooming to node:', nodeId)
      }
    },
    resetZoom: () => {
      if (plotRef.current) {
        plotRef.current.updateLayout({})
      }
    },
    getLayout: () => {
      return plotRef.current?.getLayout() || {}
    },
  }), [])

  // Handle click events
  const handleClick = useCallback((event: any) => {
    if (!event.points || event.points.length === 0) return

    const point = event.points[0]
    const node = data.find(n => n.id === point.id)
    if (node && onNodeClick) {
      onNodeClick(node)
      // Update path for breadcrumb
      const buildPath = (targetNode: SunburstNode): string[] => {
        const path: string[] = [targetNode.name]
        if (targetNode.parent) {
          const parent = data.find(n => n.id === targetNode.parent)
          if (parent) {
            path.unshift(...buildPath(parent))
          }
        }
        return path
      }
      setCurrentPath(buildPath(node))
    }
  }, [data, onNodeClick])

  // Handle hover events
  const handleHover = useCallback((event: any) => {
    if (event.points && event.points.length > 0) {
      const point = event.points[0]
      const node = data.find(n => n.id === point.id)
      onNodeHover?.(node || null)
    } else {
      onNodeHover?.(null)
    }
  }, [data, onNodeHover])

  if (!isClient) {
    return (
      <div style={{ width, height }} className="flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="relative" style={{ width, height }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600">Loading Sunburst...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 bg-opacity-90 z-10">
          <div className="text-center">
            <div className="text-red-500 text-sm mb-2">Error loading Sunburst</div>
            <div className="text-red-400 text-xs">{error}</div>
          </div>
        </div>
      )}

      <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>}>
        <Plot
          ref={plotRef}
          data={plotlyData}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '100%' }}
          onClick={handleClick}
          onHover={handleHover}
        />
      </Suspense>
    </div>
  )
})

SunburstChart.displayName = 'SunburstChart'

export default SunburstChart