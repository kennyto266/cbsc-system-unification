import React from 'react'
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/20/solid'
import { cn } from '@/utils/cn'
import type { BreadcrumbProps } from '@/types'

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items }) => {
  return (
    <nav className="flex" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {/* Home icon as first item */}
        <li>
          <div>
            <a
              href="/"
              className="text-gray-400 hover:text-gray-500 transition-colors"
              aria-label="Home"
            >
              <HomeIcon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
            </a>
          </div>
        </li>

        {/* Breadcrumb items */}
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          const hasLink = item.href && !isLast

          return (
            <li key={index}>
              <div className="flex items-center">
                <ChevronRightIcon
                  className="h-5 w-5 flex-shrink-0 text-gray-400"
                  aria-hidden="true"
                />
                {hasLink ? (
                  <a
                    href={item.href}
                    className="ml-2 text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {item.label}
                  </a>
                ) : (
                  <span
                    className={cn(
                      'ml-2 text-sm font-medium',
                      isLast
                        ? 'text-gray-900 dark:text-white'
                        : 'text-gray-500 dark:text-gray-400'
                    )}
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {item.label}
                  </span>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export default Breadcrumb