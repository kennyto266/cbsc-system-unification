/**
 * Widget Persistence Utilities - Save and load widget configurations
 */

import { GridLayout, GridItem } from '../types/grid'
import { Widget } from '../types/widget'

// Storage keys
const STORAGE_KEYS = {
  LAYOUT: 'cbsc-dashboard-layout',
  WIDGETS: 'cbsc-dashboard-widgets',
  USER_PREFERENCES: 'cbsc-dashboard-preferences',
} as const

// Layout persistence
export const saveLayout = async (layout: GridLayout): Promise<void> => {
  try {
    localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(layout))
  } catch (error) {
    console.error('Failed to save layout:', error)
    throw error
  }
}

export const loadLayout = async (): Promise<GridLayout> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.LAYOUT)
    if (saved) {
      return JSON.parse(saved)
    }
    return []
  } catch (error) {
    console.error('Failed to load layout:', error)
    return []
  }
}

export const removeLayout = async (): Promise<void> => {
  try {
    localStorage.removeItem(STORAGE_KEYS.LAYOUT)
  } catch (error) {
    console.error('Failed to remove layout:', error)
    throw error
  }
}

// Widget persistence
export const saveWidgets = async (widgets: Widget[]): Promise<void> => {
  try {
    localStorage.setItem(STORAGE_KEYS.WIDGETS, JSON.stringify(widgets))
  } catch (error) {
    console.error('Failed to save widgets:', error)
    throw error
  }
}

export const loadWidgets = async (): Promise<Widget[]> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.WIDGETS)
    if (saved) {
      return JSON.parse(saved)
    }
    return []
  } catch (error) {
    console.error('Failed to load widgets:', error)
    return []
  }
}

export const removeWidgets = async (): Promise<void> => {
  try {
    localStorage.removeItem(STORAGE_KEYS.WIDGETS)
  } catch (error) {
    console.error('Failed to remove widgets:', error)
    throw error
  }
}

// Save both layout and widgets atomically
export const saveDashboard = async (layout: GridLayout, widgets: Widget[]): Promise<void> => {
  try {
    const dashboardData = {
      layout,
      widgets,
      savedAt: new Date().toISOString(),
      version: '1.0',
    }
    localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(dashboardData))
    localStorage.setItem(STORAGE_KEYS.WIDGETS, JSON.stringify(dashboardData))
  } catch (error) {
    console.error('Failed to save dashboard:', error)
    throw error
  }
}

// Load both layout and widgets
export const loadDashboard = async (): Promise<{
  layout: GridLayout
  widgets: Widget[]
}> => {
  try {
    const [layout, widgets] = await Promise.all([loadLayout(), loadWidgets()])
    return { layout, widgets }
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    return { layout: [], widgets: [] }
  }
}

// Export configuration to file
export const exportConfiguration = async (
  layout: GridLayout,
  widgets: Widget[],
  filename?: string
): Promise<void> => {
  try {
    const config = {
      layout,
      widgets,
      metadata: {
        exportedAt: new Date().toISOString(),
        version: '1.0',
        description: 'CBSC Dashboard Configuration',
      },
    }

    const blob = new Blob([JSON.stringify(config, null, 2)], {
      type: 'application/json',
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `cbsc-dashboard-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export configuration:', error)
    throw error
  }
}

// Import configuration from file
export const importConfiguration = async (
  file: File
): Promise<{
  layout: GridLayout
  widgets: Widget[]
}> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const config = JSON.parse(content)

        // Validate configuration structure
        if (!config.layout || !Array.isArray(config.layout)) {
          throw new Error('Invalid layout configuration')
        }

        if (!config.widgets || !Array.isArray(config.widgets)) {
          throw new Error('Invalid widgets configuration')
        }

        resolve({
          layout: config.layout,
          widgets: config.widgets,
        })
      } catch (error) {
        reject(error)
      }
    }

    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }

    reader.readAsText(file)
  })
}

// Save user preferences
export const saveUserPreferences = async (preferences: Record<string, any>): Promise<void> => {
  try {
    localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(preferences))
  } catch (error) {
    console.error('Failed to save user preferences:', error)
    throw error
  }
}

// Load user preferences
export const loadUserPreferences = async (): Promise<Record<string, any>> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES)
    if (saved) {
      return JSON.parse(saved)
    }
    return {}
  } catch (error) {
    console.error('Failed to load user preferences:', error)
    return {}
  }
}

// Clear all dashboard data
export const clearAllData = async (): Promise<void> => {
  try {
    localStorage.removeItem(STORAGE_KEYS.LAYOUT)
    localStorage.removeItem(STORAGE_KEYS.WIDGETS)
    localStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES)
  } catch (error) {
    console.error('Failed to clear dashboard data:', error)
    throw error
  }
}

// Get storage usage information
export const getStorageInfo = (): {
  used: number
  available: number
  layout: number
  widgets: number
  preferences: number
} => {
  const getSize = (key: string): number => {
    const item = localStorage.getItem(key)
    return item ? new Blob([item]).size : 0
  }

  const layoutSize = getSize(STORAGE_KEYS.LAYOUT)
  const widgetsSize = getSize(STORAGE_KEYS.WIDGETS)
  const preferencesSize = getSize(STORAGE_KEYS.USER_PREFERENCES)
  const totalUsed = layoutSize + widgetsSize + preferencesSize

  // Rough estimate of available space (5MB is typical limit)
  const available = 5 * 1024 * 1024 - totalUsed

  return {
    used: totalUsed,
    available,
    layout: layoutSize,
    widgets: widgetsSize,
    preferences: preferencesSize,
  }
}

// Check if storage is available
export const isStorageAvailable = (): boolean => {
  try {
    const testKey = 'test'
    localStorage.setItem(testKey, 'test')
    localStorage.removeItem(testKey)
    return true
  } catch {
    return false
  }
}

// Auto-save utility
export class AutoSaver {
  private timer: NodeJS.Timeout | null = null
  private delay: number
  private saveFunction: () => Promise<void>

  constructor(saveFunction: () => Promise<void>, delay = 1000) {
    this.saveFunction = saveFunction
    this.delay = delay
  }

  scheduleSave(): void {
    if (this.timer) {
      clearTimeout(this.timer)
    }

    this.timer = setTimeout(() => {
      this.saveFunction().catch(console.error)
      this.timer = null
    }, this.delay)
  }

  cancelSave(): void {
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
  }

  saveNow(): void {
    this.cancelSave()
    this.saveFunction().catch(console.error)
  }

  destroy(): void {
    this.cancelSave()
  }
}

// Create auto-saver instance
export const createAutoSaver = (
  saveFunction: () => Promise<void>,
  delay = 1000
): AutoSaver => {
  return new AutoSaver(saveFunction, delay)
}