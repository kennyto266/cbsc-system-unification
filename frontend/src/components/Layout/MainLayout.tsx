import React from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Footer } from './Footer'
import { Breadcrumbs } from './Breadcrumbs'
import { useNavigation } from '../../navigation/NavigationProvider'
import { Skeleton } from '../ui/skeleton'

interface MainLayoutProps {
  children?: React.ReactNode
}

/**
 * MainLayout - Desktop layout component with header, sidebar and footer
 */
export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const { loading } = useNavigation()

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main Content Area */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        {/* Header */}
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        {/* Breadcrumbs */}
        <div className="px-6 py-3 bg-card border-b border-border">
          <Breadcrumbs />
        </div>

        {/* Main Content */}
        <main className="min-h-[calc(100vh-8rem)] p-6">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-[200px]" />
              <Skeleton className="h-32 w-full" />
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </div>
            </div>
          ) : (
            children || <Outlet />
          )}
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  )
}

export default MainLayout