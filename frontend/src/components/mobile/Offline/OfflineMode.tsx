import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff, RefreshCw, AlertCircle, Check, Clock, Download, Trash2 } from 'lucide-react';
import { clsx } from 'clsx';

interface OfflineData {
  id: string;
  type: 'strategy' | 'chart' | 'report' | 'user';
  title: string;
  data: any;
  timestamp: number;
  expiresAt: number;
  size: number;
}

interface OfflineModeProps {
  className?: string;
  onCacheUpdate?: (stats: CacheStats) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
  maxCacheSize?: number; // in MB
  retentionPeriod?: number; // in hours
}

interface CacheStats {
  totalSize: number;
  itemCount: number;
  oldestItem: number;
  newestItem: number;
  types: Record<string, number>;
}

/**
 * OfflineMode - Manages offline data caching and synchronization
 */
const OfflineMode: React.FC<OfflineModeProps> = ({
  className,
  onCacheUpdate,
  autoRefresh = true,
  refreshInterval = 5 * 60 * 1000, // 5 minutes
  maxCacheSize = 50, // 50MB
  retentionPeriod = 24 * 7, // 7 days
}) => {
  const [isOnline, setIsOnline] = useState(true);
  const [showOfflineBanner, setShowOfflineBanner] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [cacheStats, setCacheStats] = useState<CacheStats>({
    totalSize: 0,
    itemCount: 0,
    oldestItem: 0,
    newestItem: 0,
    types: {},
  });
  const [cachedData, setCachedData] = useState<OfflineData[]>([]);
  const [lastSyncTime, setLastSyncTime] = useState<number | null>(null);

  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const syncTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Storage keys
  const CACHE_KEY = 'cbsc_offline_cache';
  const STATS_KEY = 'cbsc_cache_stats';
  const SYNC_KEY = 'cbsc_last_sync';

  // Initialize offline mode
  useEffect(() => {
    // Check initial online status
    setIsOnline(navigator.onLine);

    // Load cached data and stats
    loadCachedData();
    loadCacheStats();
    loadLastSyncTime();

    // Setup event listeners
    const handleOnline = () => {
      setIsOnline(true);
      setShowOfflineBanner(false);
      syncWhenOnline();
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOfflineBanner(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Setup auto refresh
    if (autoRefresh && isOnline) {
      refreshTimerRef.current = setInterval(() => {
        refreshCache();
      }, refreshInterval);
    }

    // Setup periodic cleanup
    syncTimerRef.current = setInterval(() => {
      cleanupExpiredCache();
    }, 60 * 60 * 1000); // Every hour

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);

      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
      if (syncTimerRef.current) {
        clearInterval(syncTimerRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, isOnline]);

  // Load cached data from storage
  const loadCachedData = useCallback(() => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const data: OfflineData[] = JSON.parse(cached);
        setCachedData(data);
      }
    } catch (error) {
      console.error('Failed to load cached data:', error);
    }
  }, []);

  // Load cache statistics
  const loadCacheStats = useCallback(() => {
    try {
      const stats = localStorage.getItem(STATS_KEY);
      if (stats) {
        setCacheStats(JSON.parse(stats));
      }
    } catch (error) {
      console.error('Failed to load cache stats:', error);
    }
  }, []);

  // Load last sync time
  const loadLastSyncTime = useCallback(() => {
    try {
      const syncTime = localStorage.getItem(SYNC_KEY);
      if (syncTime) {
        setLastSyncTime(parseInt(syncTime));
      }
    } catch (error) {
      console.error('Failed to load last sync time:', error);
    }
  }, []);

  // Save cached data to storage
  const saveCachedData = useCallback((data: OfflineData[]) => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(data));
      setCachedData(data);
      updateCacheStats(data);
    } catch (error) {
      console.error('Failed to save cached data:', error);
    }
  }, []);

  // Update cache statistics
  const updateCacheStats = useCallback((data: OfflineData[]) => {
    const stats: CacheStats = {
      totalSize: data.reduce((sum, item) => sum + item.size, 0),
      itemCount: data.length,
      oldestItem: data.length > 0 ? Math.min(...data.map(item => item.timestamp)) : 0,
      newestItem: data.length > 0 ? Math.max(...data.map(item => item.timestamp)) : 0,
      types: data.reduce((acc, item) => {
        acc[item.type] = (acc[item.type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
    };

    setCacheStats(stats);
    localStorage.setItem(STATS_KEY, JSON.stringify(stats));
    onCacheUpdate?.(stats);
  }, [onCacheUpdate]);

  // Cache new data
  const cacheData = useCallback((
    type: OfflineData['type'],
    title: string,
    data: any,
    ttlHours: number = retentionPeriod
  ) => {
    const now = Date.now();
    const item: OfflineData = {
      id: `${type}_${now}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      title,
      data,
      timestamp: now,
      expiresAt: now + (ttlHours * 60 * 60 * 1000),
      size: new Blob([JSON.stringify(data)]).size,
    };

    const updatedData = [...cachedData, item];

    // Check cache size limit
    const totalSize = updatedData.reduce((sum, i) => sum + i.size, 0);
    if (totalSize > maxCacheSize * 1024 * 1024) {
      // Remove oldest items until within limit
      const sorted = updatedData.sort((a, b) => a.timestamp - b.timestamp);
      const filtered: OfflineData[] = [];
      let currentSize = 0;

      for (const item of sorted.reverse()) {
        if (currentSize + item.size <= maxCacheSize * 1024 * 1024) {
          filtered.unshift(item);
          currentSize += item.size;
        }
      }

      saveCachedData(filtered);
    } else {
      saveCachedData(updatedData);
    }
  }, [cachedData, maxCacheSize, retentionPeriod, saveCachedData]);

  // Get cached data
  const getCachedData = useCallback((type?: OfflineData['type'], id?: string) => {
    let data = cachedData;

    if (type) {
      data = data.filter(item => item.type === type);
    }

    if (id) {
      data = data.filter(item => item.id === id);
    }

    return data;
  }, [cachedData]);

  // Clear cache
  const clearCache = useCallback((type?: OfflineData['type']) => {
    let updatedData = cachedData;

    if (type) {
      updatedData = cachedData.filter(item => item.type !== type);
    } else {
      updatedData = [];
    }

    saveCachedData(updatedData);
  }, [cachedData, saveCachedData]);

  // Cleanup expired cache items
  const cleanupExpiredCache = useCallback(() => {
    const now = Date.now();
    const validData = cachedData.filter(item => item.expiresAt > now);

    if (validData.length !== cachedData.length) {
      saveCachedData(validData);
    }
  }, [cachedData, saveCachedData]);

  // Refresh cache
  const refreshCache = useCallback(async () => {
    if (!isOnline || isRefreshing) return;

    setIsRefreshing(true);

    try {
      // Here you would fetch fresh data from your API
      // For demonstration, we'll just update the sync time
      const now = Date.now();
      setLastSyncTime(now);
      localStorage.setItem(SYNC_KEY, now.toString());

      // You could also pre-cache important data here
      // await cacheEssentialData();

    } catch (error) {
      console.error('Failed to refresh cache:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [isOnline, isRefreshing]);

  // Sync when coming back online
  const syncWhenOnline = useCallback(async () => {
    if (!isOnline) return;

    // Sync any pending changes
    // This would depend on your specific implementation
    await refreshCache();
  }, [isOnline, refreshCache]);

  // Format size
  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format time
  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60 * 1000) return '剛剛';
    if (diff < 60 * 60 * 1000) return `${Math.floor(diff / (60 * 1000))} 分鐘前`;
    if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / (60 * 60 * 1000))} 小時前`;
    return date.toLocaleDateString('zh-TW');
  };

  return (
    <>
      {/* Offline banner */}
      <AnimatePresence>
        {!isOnline && (
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            className={clsx(
              'fixed top-0 left-0 right-0 z-50 bg-amber-500 text-white px-4 py-3',
              className
            )}
          >
            <div className="flex items-center justify-between max-w-4xl mx-auto">
              <div className="flex items-center gap-3">
                <WifiOff className="w-5 h-5" />
                <span className="font-medium">離線模式</span>
                <span className="text-sm opacity-90">
                  顯示緩存數據，最後同步: {lastSyncTime ? formatTime(lastSyncTime) : '未知'}
                </span>
              </div>
              <button
                onClick={refreshCache}
                disabled={isRefreshing}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 text-sm',
                  'hover:bg-white/30 transition-colors',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <RefreshCw className={clsx('w-4 h-4', isRefreshing && 'animate-spin')} />
                重試
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Cache management panel (dev mode only) */}
      {import.meta.env.DEV && (
        <div className="fixed bottom-20 right-4 bg-white rounded-lg shadow-lg p-4 max-w-xs z-40">
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <Download className="w-4 h-4" />
            離線緩存
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>項目數量:</span>
              <span>{cacheStats.itemCount}</span>
            </div>
            <div className="flex justify-between">
              <span>總大小:</span>
              <span>{formatSize(cacheStats.totalSize)}</span>
            </div>
            <div className="flex justify-between">
              <span>類型:</span>
              <span>{Object.keys(cacheStats.types).join(', ')}</span>
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <button
              onClick={refreshCache}
              disabled={isRefreshing}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1 bg-blue-500 text-white rounded text-xs"
            >
              <RefreshCw className={clsx('w-3 h-3', isRefreshing && 'animate-spin')} />
              刷新
            </button>
            <button
              onClick={() => clearCache()}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1 bg-red-500 text-white rounded text-xs"
            >
              <Trash2 className="w-3 h-3" />
              清除
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default OfflineMode;

// Export utilities for other components
export const useOfflineMode = () => {
  const cacheData = (type: OfflineData['type'], title: string, data: any, ttlHours?: number) => {
    // This would be implemented using the OfflineMode component context
    console.log('Caching data:', { type, title, data });
  };

  const getCachedData = (type?: OfflineData['type'], id?: string) => {
    // This would fetch from the OfflineMode component context
    console.log('Getting cached data:', { type, id });
    return null;
  };

  const clearCache = (type?: OfflineData['type']) => {
    // This would clear cache in the OfflineMode component context
    console.log('Clearing cache:', { type });
  };

  return {
    cacheData,
    getCachedData,
    clearCache,
  };
};