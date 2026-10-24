/**
 * Layout system type definitions for CBSC Dashboard
 */

export interface NavigationItem {
  key: string
  label: string
  icon?: React.ReactNode
  path?: string
  children?: NavigationItem[]
  badge?: {
    count: number
    color?: 'primary' | 'success' | 'warning' | 'error'
  }
  disabled?: boolean
  hidden?: boolean
  permission?: string[]
  target?: '_blank' | '_self'
  external?: boolean
}

export interface BreadcrumbItem {
  title: string
  path?: string
  icon?: React.ReactNode
}

export interface UserMenuProps {
  username: string
  email: string
  avatar?: string
  role: string
  notifications: number
}

export interface NotificationItem {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

export interface SearchSuggestion {
  type: 'page' | 'strategy' | 'indicator' | 'setting'
  title: string
  description: string
  path: string
  icon?: React.ReactNode
  keywords?: string[]
}

export interface LayoutState {
  sidebarCollapsed: boolean
  mobileMenuOpen: boolean
  theme: 'light' | 'dark' | 'auto'
  language: string
  breadcrumbs: BreadcrumbItem[]
  quickActions: QuickAction[]
}

export interface QuickAction {
  id: string
  label: string
  icon: React.ReactNode
  onClick: () => void
  shortcut?: string
  description?: string
  disabled?: boolean
}

export interface LayoutConfig {
  sidebar: {
    width: number
    collapsedWidth: number
    breakPoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl'
    defaultCollapsed: boolean
    showTrigger: boolean
    triggerRender?: (collapsed: boolean) => React.ReactNode
  }
  header: {
    height: number
    fixed: boolean
    showBreadcrumb: boolean
    showSearch: boolean
    showNotifications: boolean
    showUserMenu: boolean
  }
  content: {
    padding: number | { top?: number; right?: number; bottom?: number; left?: number }
    margin: number | { top?: number; right?: number; bottom?: number; left?: number }
  }
  footer: {
    height: number
    show: boolean
    fixed: boolean
  }
}

export interface ResponsiveBreakpoint {
  xs: boolean
  sm: boolean
  md: boolean
  lg: boolean
  xl: boolean
  xxl: boolean
}

export interface ViewportSize {
  width: number
  height: number
}

export interface ScrollPosition {
  x: number
  y: number
}

export interface LayoutContextValue {
  state: LayoutState
  config: LayoutConfig
  viewport: ViewportSize
  breakpoint: ResponsiveBreakpoint
  scroll: ScrollPosition
  updateState: (updates: Partial<LayoutState>) => void
  toggleSidebar: () => void
  toggleMobileMenu: () => void
  setTheme: (theme: 'light' | 'dark' | 'auto') => void
  setLanguage: (language: string) => void
  updateBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void
  addQuickAction: (action: QuickAction) => void
  removeQuickAction: (id: string) => void
}

export interface MenuItemProps extends NavigationItem {
  level?: number
  selected?: boolean
  expanded?: boolean
  onExpand?: (key: string, expanded: boolean) => void
  onClick?: (item: NavigationItem) => void
}

export interface SubMenuProps {
  item: NavigationItem
  level?: number
  selectedKeys?: string[]
  expandedKeys?: string[]
  onSelect?: (key: string) => void
  onExpand?: (key: string, expanded: boolean) => void
}

export interface UserMenuComponentProps extends UserMenuProps {
  onLogout: () => void
  onProfileClick: () => void
  onSettingsClick: () => void
  onNotificationClick: (notification: NotificationItem) => void
  markAllAsRead: () => void
  clearNotifications: () => void
}

export interface SearchBarProps {
  placeholder?: string
  suggestions?: SearchSuggestion[]
  onSearch: (value: string) => void
  onSelect?: (suggestion: SearchSuggestion) => void
  onClear?: () => void
  loading?: boolean
  allowClear?: boolean
  showRecent?: boolean
  recentSearches?: string[]
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
  separator?: React.ReactNode
  maxItems?: number
  showHome?: boolean
  homePath?: string
}

export interface LayoutTheme {
  name: string
  colors: {
    primary: string
    secondary: string
    background: string
    surface: string
    text: {
      primary: string
      secondary: string
      disabled: string
    }
    border: string
    shadow: string
  }
  typography: {
    fontFamily: string
    fontSize: {
      xs: string
      sm: string
      base: string
      lg: string
      xl: string
    }
    fontWeight: {
      normal: number
      medium: number
      bold: number
    }
  }
  spacing: {
    xs: number
    sm: number
    md: number
    lg: number
    xl: number
  }
  borderRadius: {
    sm: number
    md: number
    lg: number
    full: number
  }
}