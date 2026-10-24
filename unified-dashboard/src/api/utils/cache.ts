/**
 * API Cache Utility
 * Provides caching functionality for API responses
 */

import { API_CONFIG } from '../config'
import { CacheEntry } from '../types/common'

// Simple in-memory cache implementation
class ApiCache {
  private cache = new Map<string, CacheEntry>()
  private cleanupInterval: NodeJS.Timeout | null = null

  constructor() {
    // Start cleanup interval to remove expired entries
    this.startCleanup()
  }

  /**
   * Get value from cache
   */
  get<T = any>(key: string): T | null {
    const entry = this.cache.get(key)

    if (!entry) {
      return null
    }

    // Check if entry has expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key)
      return null
    }

    return entry.data as T
  }

  /**
   * Set value in cache
   */
  set<T = any>(key: string, data: T, ttl?: number): void {
    const entry: CacheEntry<T> = {
      key,
      data,
      expiresAt: Date.now() + (ttl || API_CONFIG.cache.ttl),
      cachedAt: Date.now(),
    }

    this.cache.set(key, entry)

    // Check cache size limit
    if (this.cache.size > API_CONFIG.cache.maxSize) {
      this.evictOldest()
    }
  }

  /**
   * Delete value from cache
   */
  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) {
      return false
    }

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key)
      return false
    }

    return true
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    size: number
    hitRate?: number
    memoryUsage?: number
  } {
    return {
      size: this.cache.size,
    }
  }

  /**
   * Get cache entry information
   */
  getEntryInfo(key: string): CacheEntry | null {
    const entry = this.cache.get(key)
    if (!entry) {
      return null
    }

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key)
      return null
    }

    return entry
  }

  /**
   * Cleanup expired entries
   */
  private cleanup(): void {
    const now = Date.now()
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * Start automatic cleanup
   */
  private startCleanup(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval)
    }

    this.cleanupInterval = setInterval(() => {
      this.cleanup()
    }, 60000) // Cleanup every minute
  }

  /**
   * Evict oldest entries when cache is full
   */
  private evictOldest(): void {
    let oldestKey = ''
    let oldestTime = Date.now()

    for (const [key, entry] of this.cache.entries()) {
      if (entry.cachedAt < oldestTime) {
        oldestTime = entry.cachedAt
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey)
    }
  }

  /**
   * Destroy cache instance
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval)
      this.cleanupInterval = null
    }
    this.cache.clear()
  }
}

// Create singleton instance
export const apiCache = new ApiCache()

// Cache decorator for API methods
export function Cached(ttl?: number) {
  return function (target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value

    descriptor.value = async function (...args: any[]) {
      // Generate cache key from method name and arguments
      const cacheKey = `${propertyName}:${JSON.stringify(args)}`

      // Try to get from cache first
      const cached = apiCache.get(cacheKey)
      if (cached !== null) {
        return cached
      }

      // Execute method and cache result
      const result = await method.apply(this, args)
      apiCache.set(cacheKey, result, ttl)

      return result
    }

    return descriptor
  }
}

// Cache utility functions
export const cacheUtils = {
  /**
   * Generate cache key from URL and parameters
   */
  generateKey(url: string, params?: any): string {
    const paramStr = params ? JSON.stringify(params) : ''
    return `${url}:${paramStr}`
  },

  /**
   * Cache API response
   */
  cacheResponse<T>(url: string, response: T, params?: any, ttl?: number): void {
    const key = this.generateKey(url, params)
    apiCache.set(key, response, ttl)
  },

  /**
   * Get cached API response
   */
  getCachedResponse<T>(url: string, params?: any): T | null {
    const key = this.generateKey(url, params)
    return apiCache.get<T>(key)
  },

  /**
   * Invalidate cache by URL pattern
   */
  invalidateByPattern(pattern: string): void {
    const keys = Array.from((apiCache as any).cache.keys())
    const regex = new RegExp(pattern)

    for (const key of keys) {
      if (regex.test(key)) {
        apiCache.delete(key)
      }
    }
  },

  /**
   * Get cache TTL in milliseconds
   */
  getTTL(ttl?: number): number {
    return ttl || API_CONFIG.cache.ttl
  },
}

// Export cache instance for direct usage
export default apiCache