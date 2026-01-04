import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home, TrendingUp, BarChart3, Settings, User,
  ArrowUp, Menu, X, Search, Bell,
  ChevronLeft, ChevronRight, MoreHorizontal
} from 'lucide-react';
import TouchFeedback from './TouchFeedback';
import SafeArea from './SafeArea';
import { useLocation, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';

export interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number | string;
  disabled?: boolean;
}

export interface MobileNavigationProps {
  items?: NavItem[];
  sticky?: boolean;
  showBackButton?: boolean;
  showSearch?: boolean;
  showNotifications?: boolean;
  showQuickActions?: boolean;
  onBackPress?: () => void;
  onSearchPress?: () => void;
  onNotificationPress?: () => void;
  title?: string;
  subtitle?: string;
  rightActions?: React.ReactNode;
  className?: string;
  largeTouchTargets?: boolean;
  hideOnScroll?: boolean;
  autoHide?: boolean;
  transparent?: boolean;
}

/**
 * MobileNavigation - Enhanced mobile navigation with sticky behavior and quick actions
 */
const MobileNavigation: React.FC<MobileNavigationProps> = ({
  items = [
    { id: 'home', label: '首頁', icon: <Home className="w-5 h-5" />, path: '/' },
    { id: 'strategies', label: '策略', icon: <TrendingUp className="w-5 h-5" />, path: '/strategies' },
    { id: 'analytics', label: '分析', icon: <BarChart3 className="w-5 h-5" />, path: '/analytics', badge: '新' },
    { id: 'settings', label: '設置', icon: <Settings className="w-5 h-5" />, path: '/settings' },
  ],
  sticky = true,
  showBackButton = false,
  showSearch = true,
  showNotifications = true,
  showQuickActions = true,
  onBackPress,
  onSearchPress,
  onNotificationPress,
  title,
  subtitle,
  rightActions,
  className,
  largeTouchTargets = true,
  hideOnScroll = false,
  autoHide = true,
  transparent = false,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [activeTab, setActiveTab] = useState('');
  const [showQuickMenu, setShowQuickMenu] = useState(false);
  const [scrollDirection, setScrollDirection] = useState<'up' | 'down' | null>(null);
  const [lastScrollY, setLastScrollY] = useState(0);

  const location = useLocation();
  const navigate = useNavigate();
  const navRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update active tab based on current route
  useEffect(() => {
    const currentPath = location.pathname;
    const matchingItem = items.find(item =>
      item.path === currentPath ||
      (currentPath.startsWith(item.path) && item.path !== '/')
    );
    setActiveTab(matchingItem?.id || '');
  }, [location.pathname, items]);

  // Handle scroll behavior
  useEffect(() => {
    if (!hideOnScroll) return;

    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      // Determine scroll direction
      if (currentScrollY > lastScrollY) {
        setScrollDirection('down');
      } else if (currentScrollY < lastScrollY) {
        setScrollDirection('up');
      }

      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Auto-hide behavior
      if (autoHide) {
        // Hide when scrolling down, show when scrolling up
        if (currentScrollY > 100) {
          setIsVisible(scrollDirection === 'up' || currentScrollY < 100);
        } else {
          setIsVisible(true);
        }
      }

      // Set timeout to show navigation after scroll stops
      scrollTimeoutRef.current = setTimeout(() => {
        setScrollDirection(null);
      }, 150);

      setLastScrollY(currentScrollY);
    };

    const throttledHandleScroll = throttle(handleScroll, 100);
    window.addEventListener('scroll', throttledHandleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', throttledHandleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [hideOnScroll, autoHide, lastScrollY, scrollDirection]);

  // Throttle utility
  function throttle<T extends (...args: any[]) => void>(
    func: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout | null = null;
    let lastExecTime = 0;

    return (...args: Parameters<T>) => {
      const currentTime = Date.now();

      if (currentTime - lastExecTime > delay) {
        func(...args);
        lastExecTime = currentTime;
      } else {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        timeoutId = setTimeout(() => {
          func(...args);
          lastExecTime = Date.now();
        }, delay - (currentTime - lastExecTime));
      }
    };
  }

  // Handle navigation item click
  const handleNavItemClick = useCallback((item: NavItem) => {
    if (item.disabled) return;
    navigate(item.path);
  }, [navigate]);

  // Scroll to top
  const scrollToTop = useCallback(() => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  }, []);

  // Touch size classes
  const touchSize = largeTouchTargets ? 'p-3' : 'p-2';

  return (
    <>
      {/* Top Navigation Bar */}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            ref={navRef}
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            exit={{ y: -100 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className={clsx(
              'fixed top-0 left-0 right-0 z-50',
              transparent ? 'bg-transparent' : 'bg-white',
              !transparent && 'shadow-sm border-b border-gray-100',
              className
            )}
          >
            <SafeArea top>
              {/* Header content */}
              <div className="flex items-center justify-between h-14 px-4">
                {/* Left section */}
                <div className="flex items-center gap-3">
                  {showBackButton ? (
                    <TouchFeedback
                      className={clsx('rounded-full', touchSize)}
                      onPress={onBackPress || (() => navigate(-1))}
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </TouchFeedback>
                  ) : (
                    <TouchFeedback
                      className={clsx('rounded-full', touchSize)}
                      onPress={() => setShowQuickMenu(true)}
                    >
                      <Menu className="w-5 h-5" />
                    </TouchFeedback>
                  )}

                  <div className="flex-1 min-w-0">
                    {title && (
                      <h1 className="text-lg font-medium text-gray-900 truncate">
                        {title}
                      </h1>
                    )}
                    {subtitle && (
                      <p className="text-sm text-gray-500 truncate">{subtitle}</p>
                    )}
                  </div>
                </div>

                {/* Right section */}
                <div className="flex items-center gap-2">
                  {showSearch && (
                    <TouchFeedback
                      className={clsx('rounded-full', touchSize)}
                      onPress={onSearchPress}
                    >
                      <Search className="w-5 h-5" />
                    </TouchFeedback>
                  )}

                  {showNotifications && (
                    <TouchFeedback
                      className={clsx('rounded-full relative', touchSize)}
                      onPress={onNotificationPress}
                    >
                      <Bell className="w-5 h-5" />
                      <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                    </TouchFeedback>
                  )}

                  {rightActions}
                </div>
              </div>
            </SafeArea>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Menu Overlay */}
      <AnimatePresence>
        {showQuickMenu && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black bg-opacity-50"
            onClick={() => setShowQuickMenu(false)}
          >
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed left-0 top-0 bottom-0 w-72 bg-white shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Quick menu header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <h2 className="text-lg font-semibold">快速導航</h2>
                <TouchFeedback
                  className="p-2 rounded-full hover:bg-gray-100"
                  onPress={() => setShowQuickMenu(false)}
                >
                  <X className="w-5 h-5" />
                </TouchFeedback>
              </div>

              {/* Quick menu items */}
              <div className="flex-1 overflow-y-auto">
                {items.map((item) => (
                  <TouchFeedback
                    key={item.id}
                    className={clsx(
                      'flex items-center gap-3 w-full p-4 hover:bg-gray-50',
                      activeTab === item.id && 'bg-blue-50 text-blue-600'
                    )}
                    onPress={() => {
                      handleNavItemClick(item);
                      setShowQuickMenu(false);
                    }}
                  >
                    <div className="flex-shrink-0">{item.icon}</div>
                    <div className="flex-1">
                      <div className="font-medium">{item.label}</div>
                    </div>
                    {item.badge && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-600 rounded-full">
                        {item.badge}
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </TouchFeedback>
                ))}
              </div>

              {/* User section */}
              <div className="border-t border-gray-100 p-4">
                <TouchFeedback
                  className="flex items-center gap-3 w-full p-3 hover:bg-gray-50 rounded-lg"
                  onPress={() => {
                    navigate('/profile');
                    setShowQuickMenu(false);
                  }}
                >
                  <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-gray-500" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">用戶中心</div>
                    <div className="text-sm text-gray-500">查看個人資料</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </TouchFeedback>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom Navigation */}
      <AnimatePresence>
        {isVisible && items.length > 0 && (
          <motion.div
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className={clsx(
              'fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100',
              sticky && 'shadow-lg'
            )}
          >
            <SafeArea bottom>
              <div className="flex items-center justify-around h-16">
                {items.map((item, index) => (
                  <TouchFeedback
                    key={item.id}
                    className={clsx(
                      'flex flex-col items-center gap-1 flex-1 h-full justify-center',
                      'relative',
                      activeTab === item.id
                        ? 'text-blue-600'
                        : item.disabled
                        ? 'text-gray-300'
                        : 'text-gray-500'
                    )}
                    onPress={() => handleNavItemClick(item)}
                  >
                    <div className="relative">
                      {item.icon}
                      {item.badge && typeof item.badge === 'number' && item.badge > 0 && (
                        <span className="absolute -top-1 -right-1 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full min-w-[18px] text-center">
                          {item.badge > 99 ? '99+' : item.badge}
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-medium">{item.label}</span>
                  </TouchFeedback>
                ))}
              </div>
            </SafeArea>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Scroll to top button */}
      <AnimatePresence>
        {!isVisible && scrollDirection === 'down' && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            onClick={scrollToTop}
            className="fixed bottom-20 right-4 z-40 w-12 h-12 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center"
            aria-label="返回頂部"
          >
            <ArrowUp className="w-5 h-5" />
          </motion.button>
        )}
      </AnimatePresence>
    </>
  );
};

export default MobileNavigation;