/**
 * WebSocket Cache Manager
 * Implements LRU cache with TTL support and optional persistence
 */

import { CacheConfig, CacheEntry } from '../../types/websocket';

export class CacheManager {
  private cache: Map<string, CacheEntry> = new Map();
  private accessOrder: string[] = [];
  private config: CacheConfig;
  private cleanupTimer: NodeJS.Timeout | null = null;

  constructor(config: Partial<CacheConfig> = {}) {
    this.config = {
      maxSize: 1000,
      defaultTTL: 300000, // 5 minutes
      enablePersistence: false,
      persistenceKey: 'ws_cache',
      cleanupInterval: 60000, // 1 minute
      ...config
    };

    // Load from persistence if enabled
    if (this.config.enablePersistence && typeof window !== 'undefined') {
      this.loadFromPersistence();
    }

    // Start cleanup timer
    this.startCleanupTimer();
  }

  /**
   * Store data in cache
   */
  set<T>(key: string, data: T, ttl?: number): void {
    // Check if key already exists
    const existingEntry = this.cache.get(key);
    if (existingEntry) {
      // Update access order
      this.updateAccessOrder(key);
    } else {
      // Add new entry
      this.accessOrder.push(key);
    }

    // Create cache entry
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.defaultTTL,
      accessCount: existingEntry ? existingEntry.accessCount + 1 : 1,
      lastAccessed: Date.now()
    };

    this.cache.set(key, entry);

    // Check size limit
    if (this.cache.size > this.config.maxSize) {
      this.evictLRU();
    }

    // Persist if enabled
    if (this.config.enablePersistence) {
      this.saveToPersistence();
    }
  }

  /**
   * Get data from cache
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (this.isExpired(entry)) {
      this.delete(key);
      return null;
    }

    // Update access info
    entry.accessCount++;
    entry.lastAccessed = Date.now();
    this.updateAccessOrder(key);

    return entry.data as T;
  }

  /**
   * Check if key exists in cache
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    return entry !== undefined && !this.isExpired(entry);
  }

  /**
   * Delete entry from cache
   */
  delete(key: string): boolean {
    const deleted = this.cache.delete(key);

    if (deleted) {
      // Remove from access order
      const index = this.accessOrder.indexOf(key);
      if (index !== -1) {
        this.accessOrder.splice(index, 1);
      }

      // Persist if enabled
      if (this.config.enablePersistence) {
        this.saveToPersistence();
      }
    }

    return deleted;
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.accessOrder = [];

    // Persist if enabled
    if (this.config.enablePersistence) {
      this.saveToPersistence();
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now();
    let expiredCount = 0;
    let totalAccessCount = 0;
    let oldestEntry = 0;
    let newestEntry = 0;

    this.cache.forEach(entry => {
      if (this.isExpired(entry)) {
        expiredCount++;
      }
      totalAccessCount += entry.accessCount;
      oldestEntry = Math.min(oldestEntry, entry.timestamp);
      newestEntry = Math.max(newestEntry, entry.timestamp);
    });

    return {
      size: this.cache.size,
      maxSize: this.config.maxSize,
      expiredCount,
      hitRate: this.calculateHitRate(),
      totalAccessCount,
      oldestEntry: oldestEntry || null,
      newestEntry: newestEntry || null,
      memoryUsage: this.estimateMemoryUsage()
    };
  }

  /**
   * Get all keys in cache
   */
  keys(): string[] {
    return Array.from(this.cache.keys()).filter(key => {
      const entry = this.cache.get(key);
      return entry && !this.isExpired(entry);
    });
  }

  /**
   * Get cache entries as array
   */
  entries(): Array<[string, any]> {
    const result: Array<[string, any]> = [];

    this.cache.forEach((entry, key) => {
      if (!this.isExpired(entry)) {
        result.push([key, entry.data]);
      }
    });

    return result;
  }

  /**
   * Warm up cache with provided data
   */
  warmUp<T>(entries: Array<[string, T]>, ttl?: number): void {
    entries.forEach(([key, data]) => {
      this.set(key, data, ttl);
    });
  }

  /**
   * Export cache data
   */
  export(): Record<string, any> {
    const result: Record<string, any> = {};

    this.cache.forEach((entry, key) => {
      if (!this.isExpired(entry)) {
        result[key] = {
          data: entry.data,
          timestamp: entry.timestamp,
          ttl: entry.ttl,
          accessCount: entry.accessCount,
          lastAccessed: entry.lastAccessed
        };
      }
    });

    return result;
  }

  /**
   * Import cache data
   */
  import(data: Record<string, any>): void {
    Object.entries(data).forEach(([key, entryData]) => {
      if (entryData && typeof entryData === 'object') {
        const entry = entryData as CacheEntry;
        this.cache.set(key, entry);
        this.accessOrder.push(key);
      }
    });

    // Clean up expired entries
    this.cleanup();

    // Respect size limit
    while (this.cache.size > this.config.maxSize) {
      this.evictLRU();
    }
  }

  /**
   * Clean up expired entries
   */
  cleanup(): void {
    const keysToDelete: string[] = [];

    this.cache.forEach((entry, key) => {
      if (this.isExpired(entry)) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.delete(key));
  }

  /**
   * Check if cache entry is expired
   */
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  /**
   * Update access order for LRU
   */
  private updateAccessOrder(key: string): void {
    const index = this.accessOrder.indexOf(key);
    if (index !== -1) {
      this.accessOrder.splice(index, 1);
    }
    this.accessOrder.push(key);
  }

  /**
   * Evict least recently used entry
   */
  private evictLRU(): void {
    if (this.accessOrder.length > 0) {
      const lruKey = this.accessOrder.shift();
      if (lruKey) {
        this.cache.delete(lruKey);
      }
    }
  }

  /**
   * Calculate cache hit rate
   */
  private calculateHitRate(): number {
    let totalAccess = 0;

    this.cache.forEach(entry => {
      totalAccess += entry.accessCount;
    });

    return totalAccess > 0 ? (totalAccess - this.accessOrder.length) / totalAccess : 0;
  }

  /**
   * Estimate memory usage
   */
  private estimateMemoryUsage(): number {
    // Rough estimation in bytes
    let size = 0;

    this.cache.forEach((entry, key) => {
      size += key.length * 2; // String characters
      size += JSON.stringify(entry.data).length * 2;
      size += 64; // Metadata overhead
    });

    return size;
  }

  /**
   * Start cleanup timer
   */
  private startCleanupTimer(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);
  }

  /**
   * Save cache to localStorage
   */
  private saveToPersistence(): void {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }

    try {
      const data = this.export();
      window.localStorage.setItem(this.config.persistenceKey!, JSON.stringify(data));
    } catch (error) {
      console.error('[CacheManager] Failed to save to persistence:', error);
    }
  }

  /**
   * Load cache from localStorage
   */
  private loadFromPersistence(): void {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }

    try {
      const dataStr = window.localStorage.getItem(this.config.persistenceKey!);
      if (dataStr) {
        const data = JSON.parse(dataStr);
        this.import(data);
      }
    } catch (error) {
      console.error('[CacheManager] Failed to load from persistence:', error);
    }
  }

  /**
   * Destroy cache manager
   */
  destroy(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }

    this.clear();
  }
}