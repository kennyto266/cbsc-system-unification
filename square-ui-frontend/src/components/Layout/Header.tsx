import React from 'react'
import {
  Bars3Icon,
  MagnifyingGlassIcon,
  BellIcon,
  UserCircleIcon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
} from '@heroicons/react/24/outline'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/react'
import { cn } from '@/utils/cn'
import type { HeaderProps } from '@/types'
import { useResponsive } from '@/utils/useResponsive'

const Header: React.FC<HeaderProps> = ({
  onSidebarToggle,
  isSidebarCollapsed,
  title = 'Dashboard',
  user,
}) => {
  const deviceType = useResponsive()
  const isMobile = deviceType === 'mobile'

  const navigation = [
    { name: 'Profile', href: '#' },
    { name: 'Settings', href: '#' },
    { name: 'Sign out', href: '#' },
  ]

  return (
    <header className="sticky top-0 z-40 w-full bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Left section */}
          <div className="flex items-center">
            <button
              type="button"
              onClick={onSidebarToggle}
              className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle sidebar"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            <h1 className="ml-4 text-xl font-semibold text-gray-900 dark:text-white">
              {title}
            </h1>
          </div>

          {/* Right section */}
          <div className="flex items-center gap-4">
            {/* Search - Hidden on mobile */}
            {!isMobile && (
              <div className="relative max-w-md flex-1">
                <MagnifyingGlassIcon
                  className="pointer-events-none absolute inset-y-0 left-0 h-full w-5 text-gray-400"
                  aria-hidden="true"
                />
                <input
                  type="search"
                  placeholder="Search..."
                  className="block h-full w-full border-0 py-2 pl-10 pr-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 bg-gray-50 dark:bg-gray-800 focus:ring-2 focus:ring-primary-500 rounded-lg sm:text-sm"
                />
              </div>
            )}

            {/* Theme toggle */}
            <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              <button
                type="button"
                className="p-1.5 rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                aria-label="Light mode"
              >
                <SunIcon className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="p-1.5 rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                aria-label="Dark mode"
              >
                <MoonIcon className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="p-1.5 rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                aria-label="System mode"
              >
                <ComputerDesktopIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Notifications */}
            <button
              type="button"
              className="relative p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="View notifications"
            >
              <BellIcon className="h-6 w-6" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-400 rounded-full" />
            </button>

            {/* User menu */}
            <Popover className="relative">
              <PopoverButton className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500">
                <span className="sr-only">Open user menu</span>
                {user?.avatar ? (
                  <img
                    className="h-8 w-8 rounded-full"
                    src={user.avatar}
                    alt={user.name}
                  />
                ) : (
                  <UserCircleIcon className="h-8 w-8 text-gray-400" />
                )}
              </PopoverButton>
              <PopoverPanel
                transition
                className="absolute right-0 z-10 mt-2.5 w-32 origin-top-right rounded-md bg-white dark:bg-gray-900 py-2 shadow-lg ring-1 ring-gray-900/5 transition focus:outline-none data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[leave]:duration-75 data-[enter]:ease-out data-[leave]:ease-in"
              >
                {navigation.map((item) => (
                  <a
                    key={item.name}
                    href={item.href}
                    className="block px-3 py-2 text-sm leading-6 text-gray-900 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    {item.name}
                  </a>
                ))}
              </PopoverPanel>
            </Popover>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header