import { useState, useCallback, useEffect, useMemo } from 'react'
import { GridLayout, GridItem, GridConfig, WidgetEvent } from '../../types/dashboard/grid'
import {
  createGridItem,
  moveWidget,
  resizeWidget,
  addWidget,
  removeWidget,
  duplicateWidget,
  updateWidgetConfig,
  validateGridLayout,
  exportLayout,
  importLayout,
  getLayoutStats
} from '../../utils/dashboard/gridHelpers'
import { debounce } from '../../utils/dashboard/responsiveUtils'

const STORAGE_KEY = 'cbsc_dashboard_layout'

const defaultConfig: GridConfig = {
  gridId: 'main',
  autoSave: true,
  saveInterval: 3000,
  maxHistory: 50,
  responsive: true,
  animateTransitions: true,
  preventCollision: true,
  useCSSTransforms: true,
  compactType: null,
}

const defaultLayout: GridLayout = {
  id: 'default',
  name: 'Default Layout',
  description: 'Default CBSC Dashboard layout',
  items: [],
  breakpoints: {
    xs: { cols: 1, rowHeight: 120, margin: [4, 4], containerPadding: [8, 8] },
    sm: { cols: 2, rowHeight: 100, margin: [8, 8], containerPadding: [12, 12] },
    md: { cols: 3, rowHeight: 100, margin: [12, 12], containerPadding: [16, 16] },
    lg: { cols: 4, rowHeight: 80, margin: [16, 16], containerPadding: [20, 20] },
    xl: { cols: 6, rowHeight: 80, margin: [20, 20], containerPadding: [24, 24] },
    '2xl': { cols: 8, rowHeight: 80, margin: [24, 24], containerPadding: [32, 32] },
    '4xl': { cols: 12, rowHeight: 80, margin: [32, 32], containerPadding: [40, 40] },
  },
  activeBreakpoint: 'lg',
  isCompact: false,
  isLocked: false,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
}

export const useGridLayout = (config: Partial<GridConfig> = {}) => {
  const mergedConfig = { ...defaultConfig, ...config }
  const [layout, setLayout] = useState<GridLayout>(defaultLayout)
  const [isEditMode, setIsEditMode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>()
  const [selectedWidgets, setSelectedWidgets] = useState<string[]>([])
  const [history, setHistory] = useState<GridLayout[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [widgetEvents, setWidgetEvents] = useState<WidgetEvent[]>([])

  // Load layout from localStorage on mount
  useEffect(() => {
    const loadLayout = () => {
      try {
        const saved = localStorage.getItem(`${STORAGE_KEY}_${mergedConfig.gridId}`)
        if (saved) {
          const importedLayout = importLayout(saved)
          if (importedLayout) {
            setLayout(importedLayout)
            return
          }
        }
      } catch (error) {
        console.error('Failed to load saved layout:', error)
      }
    }
    loadLayout()
  }, [mergedConfig.gridId])

  // Auto-save layout
  const saveLayout = useCallback(
    debounce((layoutToSave: GridLayout) => {
      if (!mergedConfig.autoSave) return

      try {
        localStorage.setItem(
          `${STORAGE_KEY}_${mergedConfig.gridId}`,
          exportLayout(layoutToSave)
        )
      } catch (error) {
        console.error('Failed to save layout:', error)
        setError('Failed to save layout')
      }
    }, mergedConfig.saveInterval),
    [mergedConfig.autoSave, mergedConfig.saveInterval, mergedConfig.gridId]
  )

  // Save layout whenever it changes
  useEffect(() => {
    saveLayout(layout)
  }, [layout, saveLayout])

  // Add to history
  const addToHistory = useCallback((newLayout: GridLayout) => {
    setHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1)
      newHistory.push({ ...layout })
      return newHistory.slice(-mergedConfig.maxHistory)
    })
    setHistoryIndex(prev => Math.min(prev + 1, mergedConfig.maxHistory - 1))
  }, [layout, historyIndex, mergedConfig.maxHistory])

  // Add widget event
  const addEvent = useCallback((event: WidgetEvent) => {
    setWidgetEvents(prev => [...prev.slice(-99), event]) // Keep last 100 events
  }, [])

  // Update layout with history tracking
  const updateLayout = useCallback((updater: (prev: GridLayout) => GridLayout, skipHistory = false) => {
    setLayout(prev => {
      const newLayout = updater(prev)

      // Validate layout
      const errors = validateGridLayout(newLayout)
      if (errors.length > 0) {
        setError(errors.join(', '))
        return prev
      }

      setError(undefined)

      if (!skipHistory) {
        addToHistory(prev)
      }

      newLayout.updatedAt = new Date().toISOString()
      return newLayout
    })
  }, [addToHistory])

  // Widget operations
  const addNewWidget = useCallback((type: string, title: string, position?: { x: number; y: number }, size?: { w: number; h: number }) => {
    const cols = layout.breakpoints[layout.activeBreakpoint || 'lg'].cols
    const newWidget = createGridItem(
      type,
      title,
      position || { x: 0, y: 0 },
      size || { w: 2, h: 2 }
    )

    updateLayout(prev => ({
      ...prev,
      items: addWidget(prev.items, newWidget, cols),
    }))

    addEvent(createWidgetEvent('add', newWidget.id))
  }, [layout.activeBreakpoint, layout.breakpoints, updateLayout, addEvent])

  const removeWidgetById = useCallback((widgetId: string) => {
    updateLayout(prev => ({
      ...prev,
      items: removeWidget(prev.items, widgetId),
    }))

    setSelectedWidgets(prev => prev.filter(id => id !== widgetId))
    addEvent(createWidgetEvent('remove', widgetId))
  }, [updateLayout, addEvent])

  const moveWidgetById = useCallback((widgetId: string, position: { x: number; y: number }) => {
    updateLayout(prev => ({
      ...prev,
      items: moveWidget(prev.items, widgetId, position),
    }))

    addEvent(createWidgetEvent('move', widgetId, { position }))
  }, [updateLayout, addEvent])

  const resizeWidgetById = useCallback((widgetId: string, size: { w: number; h: number }) => {
    updateLayout(prev => ({
      ...prev,
      items: resizeWidget(prev.items, widgetId, size),
    }))

    addEvent(createWidgetEvent('resize', widgetId, { size }))
  }, [updateLayout, addEvent])

  const duplicateWidgetById = useCallback((widgetId: string) => {
    const cols = layout.breakpoints[layout.activeBreakpoint || 'lg'].cols

    updateLayout(prev => ({
      ...prev,
      items: duplicateWidget(prev.items, widgetId, cols),
    }))

    addEvent(createWidgetEvent('add', widgetId, { action: 'duplicate' }))
  }, [layout.activeBreakpoint, layout.breakpoints, updateLayout, addEvent])

  const updateWidget = useCallback((widgetId: string, updates: Partial<GridItem>) => {
    updateLayout(prev => ({
      ...prev,
      items: prev.items.map(item =>
        item.id === widgetId
          ? { ...item, ...updates, lastUpdated: new Date().toISOString() }
          : item
      ),
    }))

    addEvent(createWidgetEvent('update', widgetId, updates))
  }, [updateLayout, addEvent])

  const updateWidgetConfigById = useCallback((widgetId: string, config: Record<string, any>) => {
    updateLayout(prev => ({
      ...prev,
      items: updateWidgetConfig(prev.items, widgetId, config),
    }))

    addEvent(createWidgetEvent('update', widgetId, { config }))
  }, [updateLayout, addEvent])

  const toggleWidgetMinimized = useCallback((widgetId: string) => {
    const widget = layout.items.find(item => item.id === widgetId)
    if (!widget) return

    updateWidget(widgetId, { isMinimized: !widget.isMinimized })
    addEvent(createWidgetEvent(widget.isMinimized ? 'maximize' : 'minimize', widgetId))
  }, [layout.items, updateWidget, addEvent])

  const toggleWidgetMaximized = useCallback((widgetId: string) => {
    const widget = layout.items.find(item => item.id === widgetId)
    if (!widget) return

    updateWidget(widgetId, { isMaximized: !widget.isMaximized })
    addEvent(createWidgetEvent(widget.isMaximized ? 'minimize' : 'maximize', widgetId))
  }, [layout.items, updateWidget, addEvent])

  // Layout operations
  const resetLayout = useCallback(() => {
    updateLayout(() => defaultLayout, true)
    setSelectedWidgets([])
    setHistory([])
    setHistoryIndex(-1)
    addEvent(createWidgetEvent('update', 'layout', { action: 'reset' }))
  }, [updateLayout, addEvent])

  const clearLayout = useCallback(() => {
    updateLayout(prev => ({
      ...prev,
      items: [],
      updatedAt: new Date().toISOString(),
    }))
    setSelectedWidgets([])
    addEvent(createWidgetEvent('update', 'layout', { action: 'clear' }))
  }, [updateLayout, addEvent])

  const lockLayout = useCallback(() => {
    updateLayout(prev => ({
      ...prev,
      isLocked: true,
    }))
    setIsEditMode(false)
  }, [updateLayout])

  const unlockLayout = useCallback(() => {
    updateLayout(prev => ({
      ...prev,
      isLocked: false,
    }))
  }, [updateLayout])

  const toggleEditMode = useCallback(() => {
    if (layout.isLocked) return
    setIsEditMode(prev => !prev)
    if (!isEditMode) {
      setSelectedWidgets([])
    }
  }, [layout.isLocked, isEditMode])

  // History operations
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1]
      setLayout(prevState)
      setHistoryIndex(prev => prev - 1)
    }
  }, [history, historyIndex])

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1]
      setLayout(nextState)
      setHistoryIndex(prev => prev + 1)
    }
  }, [history, historyIndex])

  // Selection operations
  const selectWidget = useCallback((widgetId: string, multi = false) => {
    if (multi) {
      setSelectedWidgets(prev =>
        prev.includes(widgetId)
          ? prev.filter(id => id !== widgetId)
          : [...prev, widgetId]
      )
    } else {
      setSelectedWidgets([widgetId])
    }
  }, [])

  const selectAllWidgets = useCallback(() => {
    setSelectedWidgets(layout.items.map(item => item.id))
  }, [layout.items])

  const clearSelection = useCallback(() => {
    setSelectedWidgets([])
  }, [])

  const deleteSelected = useCallback(() => {
    updateLayout(prev => ({
      ...prev,
      items: prev.items.filter(item => !selectedWidgets.includes(item.id)),
    }))
    setSelectedWidgets([])

    selectedWidgets.forEach(id => {
      addEvent(createWidgetEvent('remove', id))
    })
  }, [selectedWidgets, updateLayout, addEvent])

  // Export/Import operations
  const exportCurrentLayout = useCallback(() => {
    return exportLayout(layout)
  }, [layout])

  const importLayoutData = useCallback((data: string) => {
    setIsLoading(true)
    try {
      const importedLayout = importLayout(data)
      if (importedLayout) {
        setLayout(importedLayout)
        setError(undefined)
        addEvent(createWidgetEvent('update', 'layout', { action: 'import' }))
      } else {
        setError('Invalid layout data')
      }
    } catch (error) {
      setError('Failed to import layout')
    } finally {
      setIsLoading(false)
    }
  }, [addEvent])

  // Computed values
  const stats = useMemo(() => getLayoutStats(layout), [layout])
  const canUndo = historyIndex > 0
  const canRedo = historyIndex < history.length - 1
  const hasSelection = selectedWidgets.length > 0

  return {
    // State
    layout,
    isEditMode,
    isLoading,
    error,
    selectedWidgets,
    history,
    historyIndex,
    widgetEvents,
    stats,
    canUndo,
    canRedo,
    hasSelection,
    config: mergedConfig,

    // Widget operations
    addNewWidget,
    removeWidgetById,
    moveWidgetById,
    resizeWidgetById,
    duplicateWidgetById,
    updateWidget,
    updateWidgetConfigById,
    toggleWidgetMinimized,
    toggleWidgetMaximized,

    // Layout operations
    resetLayout,
    clearLayout,
    lockLayout,
    unlockLayout,
    toggleEditMode,

    // History operations
    undo,
    redo,

    // Selection operations
    selectWidget,
    selectAllWidgets,
    clearSelection,
    deleteSelected,

    // Export/Import
    exportCurrentLayout,
    importLayoutData,

    // Event handling
    addEvent,

    // Utilities
    setError,
  }
}