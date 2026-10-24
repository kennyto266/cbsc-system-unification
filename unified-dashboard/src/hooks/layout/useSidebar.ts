import { useState, useCallback, useEffect } from 'react'
import { useAppSelector, useAppDispatch } from '../redux'
import { toggleSidebar, setSidebarCollapsed } from '../../store/slices/uiSlice'

export const useSidebar = () => {
  const dispatch = useAppDispatch()
  const { sidebarCollapsed } = useAppSelector(state => state.ui)
  const [localCollapsed, setLocalCollapsed] = useState(sidebarCollapsed)

  // Sync with Redux state
  useEffect(() => {
    setLocalCollapsed(sidebarCollapsed)
  }, [sidebarCollapsed])

  const toggle = useCallback(() => {
    dispatch(toggleSidebar())
  }, [dispatch])

  const collapse = useCallback(() => {
    dispatch(setSidebarCollapsed(true))
  }, [dispatch])

  const expand = useCallback(() => {
    dispatch(setSidebarCollapsed(false))
  }, [dispatch])

  return {
    collapsed: sidebarCollapsed,
    localCollapsed,
    toggle,
    collapse,
    expand,
    isCollapsed: sidebarCollapsed
  }
}