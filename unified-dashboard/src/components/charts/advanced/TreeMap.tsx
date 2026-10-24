import React, { useMemo, useCallback, useState, lazy, Suspense } from 'react'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

// Vite-compatible lazy import of Plotly (no next/dynamic needed)
const Plot = lazy(() => import('react-plotly.js'))

export interface TreeMapNode {
  id: string
  name: string
  value: number
  parent?: string
  color?: string
  metadata?: Record<string, any>
  children?: TreeMapNode[]
}

export interface TreeMapProps {
  data: TreeMapNode[]
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
  showPath?: boolean
  onNodeClick?: (node: TreeMapNode) => void
  onNodeHover?: (node: TreeMapNode | null) => void
  animationDuration?: number
  fontSize?: number
  showValues?: boolean
  showLabels?: boolean
  padding?: number
}

export interface TreeMapRef {
  exportChart: (format: 'png' | 'svg' | 'pdf') => Promise<void>
  zoomToNode: (nodeId: string) => void
  resetZoom: () => void
  getLayout: () => any
}

const TreeMap = forwardRef<TreeMapRef, TreeMapProps>(({
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
  maxDepth = 3,
  showPath = true,
  onNodeClick,
  onNodeHover,
  animationDuration = 750,
  fontSize = 12,
  showValues = true,
  showLabels = true,
  padding = 2,
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

  // Build hierarchical structure
  const buildHierarchy = useCallback((nodes: TreeMapNode[]): any => {
    const nodeMap = new Map<string, any>()
    const roots: any[] = []

    // Create node map
    nodes.forEach(node => {
      nodeMap.set(node.id, {
        ...node,
        children: [],
      })
    })

    // Build tree
    nodes.forEach(node => {
      const treeNode = nodeMap.get(node.id)
      if (node.parent) {
        const parent = nodeMap.get(node.parent)
        if (parent) {
          parent.children.push(treeNode)
        }
      } else {
        roots.push(treeNode)
      }
    })

    return roots.length > 0 ? roots[0] : null
  }, [])

  // Generate colors based on strategy
  const generateColors = useCallback((nodes: any[]): string[] => {
    if (colorBy === 'category') {
      // Use predefined colors for different categories
      return nodes.map((node, index) => node.color || colors.levels![index % colors.levels!.length])
    } else if (colorBy === 'depth') {
      // Use colors based on depth level
      const getDepthColor = (node: any, depth: number = 0): string => {
        if (depth >= colors.levels!.length) return colors.levels![colors.levels!.length - 1]
        return colors.levels![depth]
      }

      const getColors = (node: any, depth: number = 0, result: string[] = []): string[] => {
        result.push(getDepthColor(node, depth))
        if (node.children) {
          node.children.forEach((child: any) => getColors(child, depth + 1, result))
        }
        return result
      }

      return getColors(nodes[0])
    } else {
      // Color by value
      const values = nodes.map(n => n.value)
      const minValue = Math.min(...values)
      const maxValue = Math.max(...values)

      return values.map(value => {
        const normalized = (value - minValue) / (maxValue - minValue)
        const hue = (1 - normalized) * 240 // Blue (240) to Red (0)
        return `hsl(${hue}, 70%, 50%)`
      })
    }
  }, [colorBy, colors])

  // Transform data for Plotly treemap
  const plotlyData = useMemo(() => {
    if (!data || data.length === 0) return []

    const hierarchy = buildHierarchy(data)
    if (!hierarchy) return []

    // Extract labels, values, and parents
    const labels: string[] = []
    const values: number[] = []
    const parents: string[] = []
    const colors: string[] = []
    const text: string[] = []

    const extractData = (node: any, parent: string = '') => {
      labels.push(node.name)
      values.push(node.value)
      parents.push(parent)

      if (showValues || showLabels) {
        const labelParts = []
        if (showLabels) labelParts.push(node.name)
        if (showValues) labelParts.push(formatValue(node.value))
        text.push(labelParts.join('<br>'))
      } else {
        text.push('')
      }

      if (node.children) {
        node.children.forEach((child: any) => extractData(child, node.name))
      }
    }

    extractData(hierarchy)
    const nodeColors = generateColors(labels.map((_, i) => data[i]))

    return [{
      type: 'treemap',
      labels,
      values,
      parents,
      branchvalues: 'total',
      hovertemplate: '%{label}<br>%{value}<extra></extra>',
      textinfo: showValues || showLabels ? 'text' : 'none',
      text: text,
      marker: {
        colors: nodeColors,
        line: {
          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          width: 1,
        },
        pad: {
          t: padding,
          l: padding,
          r: padding,
          b: padding,
        },
      },
      textfont: {
        size: fontSize,
        color: theme === 'dark' ? '#ffffff' : '#000000',
      },
      maxdepth: maxDepth,
    }]
  }, [
    data,
    buildHierarchy,
    generateColors,
    showValues,
    showLabels,
    formatValue,
    theme,
    fontSize,
    maxDepth,
    padding,
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
      filename: 'treemap',
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
        await plotRef.current.downloadImage(format, `treemap-${Date.now()}`)
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
    const node = data.find(n => n.name === point.label)
    if (node && onNodeClick) {
      onNodeClick(node)
      // Update path for breadcrumb
      const nodeIndex = data.indexOf(node)
      if (nodeIndex >= 0) {
        setCurrentPath([...currentPath, node.name])
      }
    }
  }, [data, onNodeClick, currentPath])

  // Handle hover events
  const handleHover = useCallback((event: any) => {
    if (event.points && event.points.length > 0) {
      const point = event.points[0]
      const node = data.find(n => n.name === point.label)
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
            <span className="text-sm text-gray-600">Loading TreeMap...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 bg-opacity-90 z-10">
          <div className="text-center">
            <div className="text-red-500 text-sm mb-2">Error loading TreeMap</div>
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

TreeMap.displayName = 'TreeMap'

export default TreeMap