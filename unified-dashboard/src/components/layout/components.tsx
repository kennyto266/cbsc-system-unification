// Export all layout-related components
export { default as AppLayout } from './index'
export { default as Header } from './Header'
export { default as HeaderEnhanced } from './HeaderEnhanced'
export { default as Sidebar } from './Sidebar'
export { default as Footer } from './Footer'
export { default as Breadcrumb } from './Breadcrumb'
export { default as BreadcrumbEnhanced } from './BreadcrumbEnhanced'
export { default as QuickActions } from './QuickActions'

// Layout hooks
export { useLayout } from '../../hooks/layout/useLayout'
export { useSidebar } from '../../hooks/layout/useSidebar'
export { useNavigation, navigationConfig } from '../../hooks/layout/useNavigation'

// Layout types
export type {
  LayoutState,
  LayoutConfig,
  NavigationItem,
  BreadcrumbItem,
  UserMenuProps,
  NotificationItem,
  SearchSuggestion,
  QuickAction,
  MenuItemProps,
  SubMenuProps,
  UserMenuComponentProps,
  SearchBarProps,
  BreadcrumbProps,
  LayoutTheme
} from '../../types/layout'