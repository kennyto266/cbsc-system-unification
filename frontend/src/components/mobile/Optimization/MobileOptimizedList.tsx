import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRight, Search, Filter, SortAsc, SortDesc,
  MoreVertical, Edit, Trash2, Share, Star, Archive,
  Check, X, AlertCircle, Info
} from 'lucide-react';
import TouchFeedback from '../TouchFeedback';
import SwipeContainer from '../SwipeContainer';
import GestureRecognizer, { GestureCallbacks } from '../Gesture/GestureRecognizer';
import { clsx } from 'clsx';

export interface ListItem {
  id: string | number;
  title: string;
  subtitle?: string;
  description?: string;
  avatar?: string;
  badge?: string | number;
  badgeColor?: string;
  tags?: string[];
  timestamp?: number | string;
  metadata?: Record<string, any>;
  actions?: Array<{
    icon: React.ReactNode;
    label: string;
    onPress: (item: ListItem) => void;
    color?: string;
  }>;
}

export interface MobileOptimizedListProps {
  items: ListItem[];
  loading?: boolean;
  error?: string;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  searchable?: boolean;
  filterable?: boolean;
  sortable?: boolean;
  sortOptions?: Array<{ label: string; value: string; key: keyof ListItem }>;
  onItemClick?: (item: ListItem) => void;
  onItemSwipe?: (item: ListItem, direction: 'left' | 'right') => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  pullToRefresh?: boolean;
  onRefresh?: () => Promise<void>;
  stickyHeader?: boolean;
  largeTouchTargets?: boolean;
  showSkeletons?: boolean;
  skeletonCount?: number;
  enableSwipeActions?: boolean;
  swipeActions?: {
    left?: Array<{
      icon: React.ReactNode;
      label: string;
      color: string;
      onPress: (item: ListItem) => void;
    }>;
    right?: Array<{
      icon: React.ReactNode;
      label: string;
      color: string;
      onPress: (item: ListItem) => void;
    }>;
  };
}

/**
 * MobileOptimizedList - Touch-friendly list component with advanced interactions
 */
const MobileOptimizedList: React.FC<MobileOptimizedListProps> = ({
  items,
  loading = false,
  error,
  emptyMessage = '沒有數據',
  emptyIcon,
  searchable = true,
  filterable = true,
  sortable = true,
  sortOptions = [],
  onItemClick,
  onItemSwipe,
  onLoadMore,
  hasMore,
  pullToRefresh = true,
  onRefresh,
  stickyHeader = true,
  largeTouchTargets = true,
  showSkeletons = true,
  skeletonCount = 5,
  enableSwipeActions = true,
  swipeActions = {
    left: [
      { icon: <Archive className="w-5 h-5" />, label: '存檔', color: 'bg-gray-500', onPress: () => {} },
    ],
    right: [
      { icon: <Trash2 className="w-5 h-5" />, label: '刪除', color: 'bg-red-500', onPress: () => {} },
    ],
  },
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState<ListItem[]>(items);
  const [sortBy, setSortBy] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<string | number>>(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeSwipeId, setActiveSwipeId] = useState<string | number | null>(null);

  const listRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Update filtered items when items change
  useEffect(() => {
    let filtered = [...items];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(query) ||
        item.subtitle?.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query) ||
        item.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Apply sorting
    if (sortBy) {
      const sortOption = sortOptions.find(opt => opt.value === sortBy);
      if (sortOption) {
        const { key } = sortOption;
        filtered.sort((a, b) => {
          const aVal = a[key];
          const bVal = b[key];

          if (aVal === undefined) return 1;
          if (bVal === undefined) return -1;

          let comparison = 0;
          if (aVal < bVal) comparison = -1;
          if (aVal > bVal) comparison = 1;

          return sortOrder === 'desc' ? -comparison : comparison;
        });
      }
    }

    setFilteredItems(filtered);
  }, [items, searchQuery, sortBy, sortOrder, sortOptions]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // Handle sort
  const handleSort = useCallback((value: string) => {
    if (sortBy === value) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(value);
      setSortOrder('asc');
    }
  }, [sortBy]);

  // Handle pull to refresh
  const handleRefresh = useCallback(async () => {
    if (!onRefresh || isRefreshing) return;

    setIsRefreshing(true);
    try {
      await onRefresh();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh, isRefreshing]);

  // Handle item swipe
  const handleItemSwipe = useCallback((item: ListItem, direction: 'left' | 'right') => {
    setActiveSwipeId(item.id);
    onItemSwipe?.(item, direction);

    // Auto-hide swipe actions after 2 seconds
    setTimeout(() => {
      setActiveSwipeId(null);
    }, 2000);
  }, [onItemSwipe]);

  // Handle selection
  const handleSelect = useCallback((itemId: string | number) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  }, []);

  // Select all
  const handleSelectAll = useCallback(() => {
    if (selectedItems.size === filteredItems.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(filteredItems.map(item => item.id)));
    }
  }, [selectedItems.size, filteredItems]);

  // Format timestamp
  const formatTimestamp = (timestamp: number | string): string => {
    if (typeof timestamp === 'string') return timestamp;
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60 * 1000) return '剛剛';
    if (diff < 60 * 60 * 1000) return `${Math.floor(diff / (60 * 1000))} 分鐘前`;
    if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / (60 * 60 * 1000))} 小時前`;
    if (diff < 7 * 24 * 60 * 60 * 1000) return `${Math.floor(diff / (24 * 60 * 60 * 1000))} 天前`;
    return date.toLocaleDateString('zh-TW');
  };

  // Render skeleton items
  const renderSkeletons = () => {
    if (!showSkeletons) return null;

    return Array.from({ length: skeletonCount }).map((_, index) => (
      <motion.div
        key={`skeleton-${index}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="p-4 bg-white border-b border-gray-100"
      >
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gray-200 rounded-full animate-pulse" />
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
          </div>
          <div className="w-8 h-8 bg-gray-200 rounded animate-pulse" />
        </div>
      </motion.div>
    ));
  };

  // Render empty state
  const renderEmpty = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 px-4"
    >
      {emptyIcon || (
        <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
          <Info className="w-8 h-8 text-gray-400" />
        </div>
      )}
      <p className="text-gray-500 text-center">{emptyMessage}</p>
      {searchQuery && (
        <button
          onClick={() => setSearchQuery('')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          清除搜索
        </button>
      )}
    </motion.div>
  );

  // Render list item
  const renderListItem = (item: ListItem, index: number) => {
    const isSelected = selectedItems.has(item.id);
    const isSwiped = activeSwipeId === item.id;
    const touchSize = largeTouchTargets ? 'p-4' : 'p-3';

    return (
      <motion.div
        key={item.id}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ delay: index * 0.05 }}
        className="relative overflow-hidden"
      >
        {/* Swipe actions background */}
        <AnimatePresence>
          {isSwiped && enableSwipeActions && (
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              className="absolute inset-0 flex"
            >
              {/* Left actions */}
              {swipeActions.left && (
                <div className="flex">
                  {swipeActions.left.map((action, i) => (
                    <TouchFeedback
                      key={i}
                      className={clsx(
                        'flex items-center justify-center text-white',
                        action.color,
                        largeTouchTargets ? 'w-20' : 'w-16'
                      )}
                      onPress={() => {
                        action.onPress(item);
                        setActiveSwipeId(null);
                      }}
                    >
                      {action.icon}
                    </TouchFeedback>
                  ))}
                </div>
              )}

              {/* Right actions */}
              {swipeActions.right && (
                <div className="flex ml-auto">
                  {swipeActions.right.map((action, i) => (
                    <TouchFeedback
                      key={i}
                      className={clsx(
                        'flex items-center justify-center text-white',
                        action.color,
                        largeTouchTargets ? 'w-20' : 'w-16'
                      )}
                      onPress={() => {
                        action.onPress(item);
                        setActiveSwipeId(null);
                      }}
                    >
                      {action.icon}
                    </TouchFeedback>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main content */}
        <motion.div
          drag={enableSwipeActions ? 'x' : false}
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.2}
          onDrag={(_, info) => {
            if (Math.abs(info.offset.x) > 100) {
              const direction = info.offset.x > 0 ? 'right' : 'left';
              handleItemSwipe(item, direction);
            }
          }}
          className={clsx(
            'bg-white border-b border-gray-100',
            isSwiped && 'shadow-lg'
          )}
        >
          <TouchFeedback
            className={clsx(
              'flex items-center gap-3 w-full',
              touchSize,
              isSelected && 'bg-blue-50'
            )}
            onPress={() => {
              if (selectedItems.size > 0) {
                handleSelect(item.id);
              } else {
                onItemClick?.(item);
              }
            }}
            onLongPress={() => {
              handleSelect(item.id);
            }}
          >
            {/* Checkbox for selection mode */}
            {selectedItems.size > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSelect(item.id);
                }}
                className={clsx(
                  'w-6 h-6 rounded-full border-2 flex items-center justify-center',
                  isSelected
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : 'border-gray-300'
                )}
              >
                {isSelected && <Check className="w-4 h-4" />}
              </button>
            )}

            {/* Avatar */}
            {item.avatar && (
              <img
                src={item.avatar}
                alt={item.title}
                className="w-12 h-12 rounded-full object-cover"
              />
            )}

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-gray-900 truncate">{item.title}</h3>
                {item.badge && (
                  <span
                    className={clsx(
                      'px-2 py-0.5 text-xs rounded-full',
                      item.badgeColor || 'bg-blue-100 text-blue-700'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </div>
              {item.subtitle && (
                <p className="text-sm text-gray-600 truncate mb-1">{item.subtitle}</p>
              )}
              {item.description && (
                <p className="text-xs text-gray-500 line-clamp-2">{item.description}</p>
              )}
              {item.tags && item.tags.length > 0 && (
                <div className="flex gap-1 mt-2 flex-wrap">
                  {item.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              {item.timestamp && (
                <p className="text-xs text-gray-400 mt-1">
                  {formatTimestamp(item.timestamp)}
                </p>
              )}
            </div>

            {/* Chevron */}
            {selectedItems.size === 0 && (
              <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
            )}
          </TouchFeedback>
        </motion.div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      {stickyHeader && (
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200">
          {/* Search bar */}
          {searchable && (
            <div className="p-4 pb-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="搜索..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className={clsx(
                    'w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500',
                    largeTouchTargets && 'py-4 text-lg'
                  )}
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Actions bar */}
          <div className="flex items-center justify-between px-4 pb-2">
            <div className="flex items-center gap-2">
              {filterable && (
                <TouchFeedback
                  className={clsx(
                    'p-2 rounded-lg',
                    showFilters ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
                  )}
                  onPress={() => setShowFilters(!showFilters)}
                >
                  <Filter className="w-5 h-5" />
                </TouchFeedback>
              )}
              {sortable && sortOptions.length > 0 && (
                <TouchFeedback className="p-2 rounded-lg hover:bg-gray-100">
                  {sortOrder === 'asc' ? (
                    <SortAsc className="w-5 h-5" />
                  ) : (
                    <SortDesc className="w-5 h-5" />
                  )}
                </TouchFeedback>
              )}
              {selectedItems.size > 0 && (
                <>
                  <span className="text-sm text-gray-600">
                    已選擇 {selectedItems.size} 項
                  </span>
                  <TouchFeedback
                    className="p-2 rounded-lg hover:bg-gray-100"
                    onPress={handleSelectAll}
                  >
                    <Check className="w-5 h-5" />
                  </TouchFeedback>
                </>
              )}
            </div>
            {selectedItems.size > 0 && (
              <TouchFeedback
                className="p-2 rounded-lg hover:bg-gray-100"
                onPress={() => setSelectedItems(new Set())}
              >
                <X className="w-5 h-5" />
              </TouchFeedback>
            )}
          </div>

          {/* Sort options */}
          {sortOptions.length > 0 && (
            <div className="flex gap-2 px-4 pb-2 overflow-x-auto">
              {sortOptions.map(option => (
                <TouchFeedback
                  key={option.value}
                  className={clsx(
                    'px-3 py-1 rounded-full text-sm whitespace-nowrap',
                    sortBy === option.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700'
                  )}
                  onPress={() => handleSort(option.value)}
                >
                  {option.label}
                </TouchFeedback>
              ))}
            </div>
          )}
        </div>
      )}

      {/* List content */}
      <div
        ref={listRef}
        className={clsx(
          'flex-1 overflow-y-auto',
          !stickyHeader && 'pt-4'
        )}
      >
        {pullToRefresh && onRefresh && (
          <SwipeContainer
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
          >
            {content}
          </SwipeContainer>
        )}

        {!pullToRefresh && content}
      </div>

      {/* Load more button */}
      {hasMore && onLoadMore && (
        <div className="p-4">
          <TouchFeedback
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gray-100 text-gray-700 disabled:opacity-50"
            onPress={onLoadMore}
          >
            {loading ? '載入中...' : '載入更多'}
          </TouchFeedback>
        </div>
      )}

      {/* Selection mode actions */}
      <AnimatePresence>
        {selectedItems.size > 0 && (
          <motion.div
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4"
          >
            <div className="flex items-center justify-around">
              <TouchFeedback className="flex flex-col items-center gap-1">
                <Share className="w-6 h-6" />
                <span className="text-xs">分享</span>
              </TouchFeedback>
              <TouchFeedback className="flex flex-col items-center gap-1">
                <Archive className="w-6 h-6" />
                <span className="text-xs">存檔</span>
              </TouchFeedback>
              <TouchFeedback className="flex flex-col items-center gap-1 text-red-600">
                <Trash2 className="w-6 h-6" />
                <span className="text-xs">刪除</span>
              </TouchFeedback>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  // Extract content for reuse
  function content() {
    if (error) {
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-16 px-4"
        >
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-gray-600 text-center mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg"
          >
            重試
          </button>
        </motion.div>
      );
    }

    if (loading && filteredItems.length === 0) {
      return renderSkeletons();
    }

    if (filteredItems.length === 0) {
      return renderEmpty();
    }

    return (
      <div>
        {filteredItems.map((item, index) => renderListItem(item, index))}
      </div>
    );
  }
};

export default MobileOptimizedList;