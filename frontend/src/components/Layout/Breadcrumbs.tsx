import React from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { useNavigation } from '../../navigation/NavigationProvider'
import { cn } from '@/lib/utils'

interface BreadcrumbItem {
  label: string
  href?: string
  active?: boolean
}

interface BreadcrumbsProps {
  className?: string
  items?: BreadcrumbItem[]
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ className, items }) => {
  const { breadcrumbs: navigationBreadcrumbs } = useNavigation()
  const breadcrumbs = items || navigationBreadcrumbs

  if (breadcrumbs.length <= 1) {
    return null
  }

  return (
    <nav className={cn("flex items-center space-x-1 text-sm text-muted-foreground", className)}>
      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1
        const isFirst = index === 0

        return (
          <React.Fragment key={index}>
            {index > 0 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
            )}

            {item.href ? (
              <Link
                to={item.href}
                className={cn(
                  "flex items-center space-x-1 hover:text-foreground transition-colors",
                  isLast && "text-foreground font-medium"
                )}
              >
                {isFirst && <Home className="h-4 w-4" />}
                <span>{item.label}</span>
              </Link>
            ) : (
              <span className={cn(
                "flex items-center space-x-1",
                isLast && "text-foreground font-medium"
              )}>
                {isFirst && <Home className="h-4 w-4" />}
                <span>{item.label}</span>
              </span>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}

export default Breadcrumbs