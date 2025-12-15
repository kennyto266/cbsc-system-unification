// Layout component types
export interface SidebarItem {
  id: string
  label: string
  icon: React.ComponentType<any>
  href: string
  badge?: number
  children?: SidebarItem[]
}

export interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
  items: SidebarItem[]
  activeItem: string
  onItemClick: (id: string) => void
}

export interface HeaderProps {
  onSidebarToggle: () => void
  isSidebarCollapsed: boolean
  title?: string
  user?: User
}

export interface BreadcrumbItem {
  label: string
  href?: string
  isActive?: boolean
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

// User types
export interface User {
  id: string
  name: string
  email: string
  avatar?: string
  role: string
}

// Navigation types
export interface NavigationState {
  activeItemId: string
  breadcrumbs: BreadcrumbItem[]
  isSidebarCollapsed: boolean
}

// Layout context type
export interface LayoutContextType {
  isSidebarCollapsed: boolean
  toggleSidebar: () => void
  activeItemId: string
  setActiveItem: (id: string) => void
  breadcrumbs: BreadcrumbItem[]
  setBreadcrumbs: (items: BreadcrumbItem[]) => void
}

// Responsive breakpoints
export type Breakpoint = 'sm' | 'md' | 'lg' | 'xl' | '2xl'

// Theme types
export type Theme = 'light' | 'dark' | 'system'

// Device type for responsive behavior
export type DeviceType = 'mobile' | 'tablet' | 'desktop'