/**
 * Storage Service - 統一存儲服務
 * 版本: 1.0.0
 * 描述: 提供統一的本地存儲接口，支持 localStorage、sessionStorage 和 IndexedDB
 */

// 存儲類型
export type StorageType = 'localStorage' | 'sessionStorage' | 'indexedDB';

// 存儲項接口
export interface StorageItem<T = any> {
  data: T;
  version: string;
  timestamp: number;
  ttl?: number; // Time to live in milliseconds
}

// 存儲配置接口
export interface StorageConfig {
  prefix?: string;
  defaultTTL?: number;
  enableEncryption?: boolean;
  compressionThreshold?: number;
}

/**
 * 統一存儲服務
 */
export class StorageService {
  private config: StorageConfig = {
    prefix: 'cbsc_',
    defaultTTL: 24 * 60 * 60 * 1000, // 24 hours
    enableEncryption: false,
    compressionThreshold: 1024, // 1KB
  };

  private memoryCache: Map<string, StorageItem> = new Map();
  private dbPromise: Promise<IDBDatabase> | null = null;

  constructor(config: Partial<StorageConfig> = {}) {
    this.config = { ...this.config, ...config };
  }

  /**
   * 設置數據
   */
  async set<T>(
    key: string,
    value: T,
    options: {
      type?: StorageType;
      ttl?: number;
      version?: string;
    } = {}
  ): Promise<void> {
    const {
      type = 'localStorage',
      ttl = this.config.defaultTTL,
      version = '2.0.0'
    } = options;

    const storageKey = this.getStorageKey(key);
    const now = Date.now();

    const item: StorageItem<T> = {
      data: value,
      version,
      timestamp: now,
      ttl: ttl > 0 ? now + ttl : undefined,
    };

    switch (type) {
      case 'localStorage':
        this.setLocalStorage(storageKey, item);
        break;
      case 'sessionStorage':
        this.setSessionStorage(storageKey, item);
        break;
      case 'indexedDB':
        await this.setIndexedDB(storageKey, item);
        break;
    }

    // 同時更新內存緩存
    if (ttl === undefined || Date.now() < (item.ttl || Infinity)) {
      this.memoryCache.set(key, item);
    }
  }

  /**
   * 獲取數據
   */
  async get<T>(
    key: string,
    options: {
      type?: StorageType;
      fallbackTypes?: StorageType[];
    } = {}
  ): Promise<T | null> {
    const {
      type = 'localStorage',
      fallbackTypes = ['sessionStorage', 'indexedDB']
    } = options;

    // 首先檢查內存緩存
    const cached = this.memoryCache.get(key);
    if (cached && this.isValidItem(cached)) {
      return cached.data as T;
    }

    // 從指定存儲獲取
    const storageKey = this.getStorageKey(key);
    let item: StorageItem<T> | null = null;

    switch (type) {
      case 'localStorage':
        item = this.getLocalStorage<T>(storageKey);
        break;
      case 'sessionStorage':
        item = this.getSessionStorage<T>(storageKey);
        break;
      case 'indexedDB':
        item = await this.getIndexedDB<T>(storageKey);
        break;
    }

    // 如果沒找到，嘗試從備用存儲獲取
    if (!item && fallbackTypes.length > 0) {
      for (const fallbackType of fallbackTypes) {
        item = await this.get<T>(key, { type: fallbackType, fallbackTypes: [] });
        if (item) break;
      }
    }

    if (item && this.isValidItem(item)) {
      // 更新內存緩存
      this.memoryCache.set(key, item);
      return item.data;
    }

    return null;
  }

  /**
   * 刪除數據
   */
  async remove(
    key: string,
    options: {
      type?: StorageType;
      allTypes?: boolean;
    } = {}
  ): Promise<void> {
    const { type = 'localStorage', allTypes = false } = options;
    const storageKey = this.getStorageKey(key);

    // 從內存緩存刪除
    this.memoryCache.delete(key);

    const types = allTypes
      ? ['localStorage', 'sessionStorage', 'indexedDB'] as StorageType[]
      : [type];

    for (const storageType of types) {
      switch (storageType) {
        case 'localStorage':
          localStorage.removeItem(storageKey);
          break;
        case 'sessionStorage':
          sessionStorage.removeItem(storageKey);
          break;
        case 'indexedDB':
          await this.removeIndexedDB(storageKey);
          break;
      }
    }
  }

  /**
   * 檢查數據是否存在
   */
  async exists(
    key: string,
    options: {
      type?: StorageType;
    } = {}
  ): Promise<boolean> {
    const value = await this.get(key, options);
    return value !== null;
  }

  /**
   * 獲取存儲的鍵列表
   */
  async keys(type: StorageType = 'localStorage'): Promise<string[]> {
    const prefix = this.config.prefix || '';
    const keys: string[] = [];

    switch (type) {
      case 'localStorage':
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith(prefix)) {
            keys.push(key.substring(prefix.length));
          }
        }
        break;
      case 'sessionStorage':
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i);
          if (key && key.startsWith(prefix)) {
            keys.push(key.substring(prefix.length));
          }
        }
        break;
      case 'indexedDB':
        const db = await this.getIndexedDB();
        const transaction = db.transaction(['storage'], 'readonly');
        const store = transaction.objectStore('storage');

        const request = store.getAllKeys();
        return new Promise((resolve, reject) => {
          request.onsuccess = () => {
            const allKeys = request.result as string[];
            const filteredKeys = allKeys
              .filter(key => key.startsWith(prefix))
              .map(key => key.substring(prefix.length));
            resolve(filteredKeys);
          };
          request.onerror = () => reject(request.error);
        });
    }

    return keys;
  }

  /**
   * 清空存儲
   */
  async clear(type?: StorageType): Promise<void> {
    if (type) {
      const keys = await this.keys(type);
      await Promise.all(keys.map(key => this.remove(key, { type })));
    } else {
      // 清空所有類型
      await Promise.all([
        this.clear('localStorage'),
        this.clear('sessionStorage'),
        this.clear('indexedDB')
      ]);
    }
  }

  /**
   * 獲取存儲大小
   */
  async getStorageSize(type: StorageType = 'localStorage'): Promise<number> {
    let size = 0;

    switch (type) {
      case 'localStorage':
        for (let key in localStorage) {
          if (localStorage.hasOwnProperty(key)) {
            size += localStorage[key].length + key.length;
          }
        }
        break;
      case 'sessionStorage':
        for (let key in sessionStorage) {
          if (sessionStorage.hasOwnProperty(key)) {
            size += sessionStorage[key].length + key.length;
          }
        }
        break;
      case 'indexedDB':
        // IndexedDB 大小估算較複雜，這裡簡化處理
        const db = await this.getIndexedDB();
        const transaction = db.transaction(['storage'], 'readonly');
        const store = transaction.objectStore('storage');

        return new Promise((resolve, reject) => {
          const request = store.getAll();
          request.onsuccess = () => {
            const items = request.result;
            let totalSize = 0;
            items.forEach(item => {
              totalSize += JSON.stringify(item).length;
            });
            resolve(totalSize);
          };
          request.onerror = () => reject(request.error);
        });
    }

    return size;
  }

  /**
   * 獲取完整的存儲鍵
   */
  private getStorageKey(key: string): string {
    return `${this.config.prefix || ''}${key}`;
  }

  /**
   * 檢查存儲項是否有效
   */
  private isValidItem(item: StorageItem): boolean {
    if (!item) return false;

    // 檢查 TTL
    if (item.ttl && Date.now() > item.ttl) {
      return false;
    }

    return true;
  }

  /**
   * 設置 localStorage
   */
  private setLocalStorage<T>(key: string, item: StorageItem<T>): void {
    try {
      const serialized = JSON.stringify(item);
      localStorage.setItem(key, serialized);
    } catch (error) {
      console.error('Failed to set localStorage:', error);
      throw error;
    }
  }

  /**
   * 獲取 localStorage
   */
  private getLocalStorage<T>(key: string): StorageItem<T> | null {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;

      const parsed = JSON.parse(item);
      return this.isValidItem(parsed) ? parsed : null;
    } catch (error) {
      console.error('Failed to get localStorage:', error);
      return null;
    }
  }

  /**
   * 設置 sessionStorage
   */
  private setSessionStorage<T>(key: string, item: StorageItem<T>): void {
    try {
      const serialized = JSON.stringify(item);
      sessionStorage.setItem(key, serialized);
    } catch (error) {
      console.error('Failed to set sessionStorage:', error);
      throw error;
    }
  }

  /**
   * 獲取 sessionStorage
   */
  private getSessionStorage<T>(key: string): StorageItem<T> | null {
    try {
      const item = sessionStorage.getItem(key);
      if (!item) return null;

      const parsed = JSON.parse(item);
      return this.isValidItem(parsed) ? parsed : null;
    } catch (error) {
      console.error('Failed to get sessionStorage:', error);
      return null;
    }
  }

  /**
   * 獲取 IndexedDB 實例
   */
  private async getIndexedDB(): Promise<IDBDatabase> {
    if (!this.dbPromise) {
      this.dbPromise = this.initIndexedDB();
    }
    return this.dbPromise;
  }

  /**
   * 初始化 IndexedDB
   */
  private initIndexedDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('CBSC_Storage', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('storage')) {
          const store = db.createObjectStore('storage', { keyPath: 'key' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  /**
   * 設置 IndexedDB
   */
  private async setIndexedDB<T>(key: string, item: StorageItem<T>): Promise<void> {
    const db = await this.getIndexedDB();
    const transaction = db.transaction(['storage'], 'readwrite');
    const store = transaction.objectStore('storage');

    return new Promise((resolve, reject) => {
      const request = store.put({ key, ...item });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 獲取 IndexedDB
   */
  private async getIndexedDB<T>(key: string): Promise<StorageItem<T> | null> {
    const db = await this.getIndexedDB();
    const transaction = db.transaction(['storage'], 'readonly');
    const store = transaction.objectStore('storage');

    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => {
        const item = request.result;
        if (!item) {
          resolve(null);
          return;
        }

        // 移除 key 屬性
        const { key: _, ...storageItem } = item;
        resolve(this.isValidItem(storageItem) ? storageItem : null);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 從 IndexedDB 刪除
   */
  private async removeIndexedDB(key: string): Promise<void> {
    const db = await this.getIndexedDB();
    const transaction = db.transaction(['storage'], 'readwrite');
    const store = transaction.objectStore('storage');

    return new Promise((resolve, reject) => {
      const request = store.delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 壓縮數據（如果啟用）
   */
  private compress(data: any): any {
    if (!this.config.compressionThreshold) {
      return data;
    }

    const serialized = JSON.stringify(data);
    if (serialized.length < this.config.compressionThreshold) {
      return data;
    }

    // 這裡可以實現壓縮邏輯
    // 例如使用 LZ-string 或其他壓縮庫
    return data;
  }

  /**
   * 解壓縮數據（如果啟用）
   */
  private decompress(data: any): any {
    // 實現解壓縮邏輯
    return data;
  }

  /**
   * 加密數據（如果啟用）
   */
  private encrypt(data: any): any {
    if (!this.config.enableEncryption) {
      return data;
    }

    // 實現加密邏輯
    return data;
  }

  /**
   * 解密數據（如果啟用）
   */
  private decrypt(data: any): any {
    if (!this.config.enableEncryption) {
      return data;
    }

    // 實現解密邏輯
    return data;
  }
}

// 創建全局實例
export const storageService = new StorageService();

// 導出默認實例
export default storageService;