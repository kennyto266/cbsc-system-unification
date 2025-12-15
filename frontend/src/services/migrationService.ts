/**
 * Migration Service - 數據遷移服務
 * 版本: 1.0.0
 * 描述: 處理前端系統數據遷移的核心服務
 */

import { StorageService } from './storageService';

// 數據版本類型
export type DataVersion = '1.0.0' | '1.5.0' | '2.0.0';

// 備份快照接口
export interface BackupSnapshot {
  id: string;
  timestamp: string;
  version: DataVersion;
  data: {
    localStorage: Record<string, any>;
    indexedDB?: Record<string, any>;
    sessionStorage?: Record<string, any>;
  };
}

// 驗證報告接口
export interface ValidationReport {
  dataIntegrity: {
    isValid: boolean;
    issues: string[];
  };
  functionality: {
    isValid: boolean;
    issues: string[];
  };
  performance: {
    loadTime: number;
    memoryUsage: number;
  };
}

// 遷移配置接口
export interface MigrationConfig {
  enableDualWrite: boolean;
  backupBeforeMigration: boolean;
  validateAfterMigration: boolean;
  rollbackOnError: boolean;
}

/**
 * 數據版本管理器
 */
class DataVersionManager {
  private currentVersion: DataVersion = '2.0.0';
  private migrations: Record<string, (data: any) => any> = {
    '1.0.0': this.migrateFromV1.bind(this),
    '1.5.0': this.migrateFromV1_5.bind(this),
  };

  /**
   * 檢測數據版本
   */
  detectVersion(data: any): DataVersion {
    if (data.version) return data.version;

    // 根據數據結構推斷版本
    if (data.strategy_name && data.strategy_type) {
      return '1.0.0';
    } else if (data.name && data.type) {
      return '1.5.0';
    }

    return '1.0.0';
  }

  /**
   * 從 v1.0.0 遷移
   */
  private migrateFromV1(data: any): any {
    return {
      id: data.strategy_id || data.strategy_name,
      name: data.strategy_name,
      type: this.normalizeStrategyType(data.strategy_type),
      parameters: data.params || {},
      enabled: data.is_active !== false,
      lastModified: data.updated_at || new Date().toISOString(),
      version: 1,
    };
  }

  /**
   * 從 v1.5.0 遷移
   */
  private migrateFromV1_5(data: any): any {
    return {
      ...data,
      version: 2,
      metadata: {
        migratedAt: new Date().toISOString(),
        previousVersion: '1.5.0'
      }
    };
  }

  /**
   * 標準化策略類型
   */
  private normalizeStrategyType(type: string): 'price' | 'non-price' {
    const normalized = type?.toLowerCase();
    if (normalized?.includes('price')) return 'price';
    if (normalized?.includes('non-price') || normalized?.includes('nonprice')) return 'non-price';
    return 'price'; // 默認值
  }

  /**
   * 獲取下一版本
   */
  private getNextVersion(current: string): DataVersion {
    const versions: DataVersion[] = ['1.0.0', '1.5.0', '2.0.0'];
    const index = versions.indexOf(current as DataVersion);
    return versions[index + 1] || '2.0.0';
  }
}

/**
 * 遷移適配器
 */
class MigrationAdapter {
  private isMigrationActive: boolean = true;
  private storageService = new StorageService();

  /**
   * 寫入數據（支持雙寫）
   */
  async writeData(key: string, data: any, useDualWrite: boolean = true): Promise<void> {
    // 寫入新系統
    await this.storageService.set(key, data);

    // 遷移期間同時寫入舊系統
    if (useDualWrite && this.isMigrationActive) {
      try {
        await this.writeToLegacySystem(key, data);
      } catch (error) {
        console.warn('Legacy write failed:', error);
      }
    }
  }

  /**
   * 讀取數據
   */
  async readData(key: string, fallbackToLegacy: boolean = true): Promise<any> {
    try {
      // 優先從新系統讀取
      const newData = await this.storageService.get(key);
      if (newData !== null) return newData;
    } catch (error) {
      console.warn('New system read failed:', error);
    }

    // 新系統無數據時從舊系統讀取
    if (fallbackToLegacy) {
      return await this.readFromLegacySystem(key);
    }

    return null;
  }

  /**
   * 寫入舊系統
   */
  private async writeToLegacySystem(key: string, data: any): Promise<void> {
    const legacyKey = this.mapToLegacyKey(key);
    const legacyData = this.mapToLegacyFormat(data);

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(legacyKey, JSON.stringify(legacyData));
    }
  }

  /**
   * 從舊系統讀取
   */
  private async readFromLegacySystem(key: string): Promise<any> {
    const legacyKey = this.mapToLegacyKey(key);

    if (typeof localStorage !== 'undefined') {
      const item = localStorage.getItem(legacyKey);
      if (item) {
        try {
          const data = JSON.parse(item);
          return this.mapFromLegacyFormat(data);
        } catch (error) {
          console.error('Failed to parse legacy data:', error);
        }
      }
    }

    return null;
  }

  /**
   * 映射到舊系統key
   */
  private mapToLegacyKey(key: string): string {
    const keyMap: Record<string, string> = {
      'userPreferences': 'cbsc_user_prefs',
      'dashboardConfig': 'dashboard_config',
      'strategyFilters': 'strategy_filters',
      'chartSettings': 'chart_settings',
    };

    return keyMap[key] || key;
  }

  /**
   * 映射到舊系統格式
   */
  private mapToLegacyFormat(data: any): any {
    // 實現具體的格式轉換邏輯
    return data;
  }

  /**
   * 從舊系統格式轉換
   */
  private mapFromLegacyFormat(data: any): any {
    // 實現具體的格式轉換邏輯
    return data;
  }

  /**
   * 禁用雙寫模式
   */
  disableDualWrite(): void {
    this.isMigrationActive = false;
  }
}

/**
 * 數據備份工具
 */
class DataBackupTool {
  /**
   * 創建備份
   */
  async createBackup(): Promise<BackupSnapshot> {
    const snapshot: BackupSnapshot = {
      id: this.generateBackupId(),
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      data: {
        localStorage: this.getAllLocalStorage(),
        indexedDB: await this.getAllIndexedDB(),
        sessionStorage: this.getAllSessionStorage(),
      }
    };

    // 保存備份到本地或雲端
    await this.saveBackup(snapshot);

    return snapshot;
  }

  /**
   * 恢復備份
   */
  async restoreBackup(backupId: string): Promise<void> {
    const backup = await this.loadBackup(backupId);
    if (!backup) {
      throw new Error(`Backup ${backupId} not found`);
    }

    // 恢復 localStorage
    this.restoreLocalStorage(backup.data.localStorage);

    // 恢復 IndexedDB
    if (backup.data.indexedDB) {
      await this.restoreIndexedDB(backup.data.indexedDB);
    }

    // 恢復 sessionStorage
    if (backup.data.sessionStorage) {
      this.restoreSessionStorage(backup.data.sessionStorage);
    }
  }

  /**
   * 生成備份ID
   */
  private generateBackupId(): string {
    return `backup_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 獲取所有 localStorage 數據
   */
  private getAllLocalStorage(): Record<string, any> {
    const data: Record<string, any> = {};

    if (typeof localStorage !== 'undefined') {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cbsc_')) {
          const value = localStorage.getItem(key);
          try {
            data[key] = JSON.parse(value || '{}');
          } catch {
            data[key] = value;
          }
        }
      }
    }

    return data;
  }

  /**
   * 獲取所有 IndexedDB 數據
   */
  private async getAllIndexedDB(): Promise<Record<string, any>> {
    // 實現 IndexedDB 數據獲取邏輯
    return {};
  }

  /**
   * 獲取所有 sessionStorage 數據
   */
  private getAllSessionStorage(): Record<string, any> {
    const data: Record<string, any> = {};

    if (typeof sessionStorage !== 'undefined') {
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key) {
          const value = sessionStorage.getItem(key);
          try {
            data[key] = JSON.parse(value || '{}');
          } catch {
            data[key] = value;
          }
        }
      }
    }

    return data;
  }

  /**
   * 保存備份
   */
  private async saveBackup(snapshot: BackupSnapshot): Promise<void> {
    // 保存到 localStorage
    const backupKey = `cbsc_backup_${snapshot.id}`;
    localStorage.setItem(backupKey, JSON.stringify(snapshot));

    // 可以額外保存到雲端
    // await this.saveToCloud(snapshot);
  }

  /**
   * 加載備份
   */
  private async loadBackup(backupId: string): Promise<BackupSnapshot | null> {
    const backupKey = `cbsc_backup_${backupId}`;
    const item = localStorage.getItem(backupKey);

    if (item) {
      try {
        return JSON.parse(item);
      } catch (error) {
        console.error('Failed to load backup:', error);
      }
    }

    return null;
  }

  /**
   * 恢復 localStorage
   */
  private restoreLocalStorage(data: Record<string, any>): void {
    if (typeof localStorage !== 'undefined') {
      Object.entries(data).forEach(([key, value]) => {
        localStorage.setItem(key, JSON.stringify(value));
      });
    }
  }

  /**
   * 恢復 IndexedDB
   */
  private async restoreIndexedDB(data: Record<string, any>): Promise<void> {
    // 實現 IndexedDB 恢復邏輯
  }

  /**
   * 恢復 sessionStorage
   */
  private restoreSessionStorage(data: Record<string, any>): void {
    if (typeof sessionStorage !== 'undefined') {
      Object.entries(data).forEach(([key, value]) => {
        sessionStorage.setItem(key, JSON.stringify(value));
      });
    }
  }
}

/**
 * 遷移服務主類
 */
export class MigrationService {
  private adapter = new MigrationAdapter();
  private versionManager = new DataVersionManager();
  private backupTool = new DataBackupTool();
  private config: MigrationConfig = {
    enableDualWrite: true,
    backupBeforeMigration: true,
    validateAfterMigration: true,
    rollbackOnError: true,
  };

  /**
   * 配置遷移選項
   */
  configure(config: Partial<MigrationConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * 檢測是否需要遷移
   */
  async needsMigration(): Promise<boolean> {
    // 檢查是否有舊版本數據
    const hasLegacyData = await this.detectLegacyData();

    // 檢查當前版本
    const currentVersion = await this.getCurrentDataVersion();
    const needsUpgrade = currentVersion !== '2.0.0';

    return hasLegacyData || needsUpgrade;
  }

  /**
   * 執行遷移
   */
  async executeMigration(): Promise<void> {
    let backupId: string | null = null;

    try {
      console.log('Starting data migration...');

      // 1. 創建備份
      if (this.config.backupBeforeMigration) {
        const backup = await this.backupTool.createBackup();
        backupId = backup.id;
        console.log(`Created backup: ${backupId}`);
      }

      // 2. 檢測現有數據
      const legacyData = await this.detectLegacyData();
      if (!legacyData || Object.keys(legacyData).length === 0) {
        console.log('No legacy data found, migration complete');
        return;
      }

      // 3. 轉換和遷移數據
      await this.migrateData(legacyData);

      // 4. 驗證遷移
      if (this.config.validateAfterMigration) {
        const validation = await this.validateMigration();
        if (!validation.dataIntegrity.isValid) {
          throw new Error('Migration validation failed');
        }
      }

      console.log('Migration completed successfully');

    } catch (error) {
      console.error('Migration failed:', error);

      // 回滾
      if (this.config.rollbackOnError && backupId) {
        console.log('Rolling back migration...');
        await this.rollbackMigration(backupId);
      }

      throw error;
    }
  }

  /**
   * 檢測舊版數據
   */
  private async detectLegacyData(): Promise<Record<string, any>> {
    const legacyKeys = [
      'cbsc_user_prefs',
      'dashboard_config',
      'strategy_filters',
      'chart_settings',
    ];

    const data: Record<string, any> = {};

    if (typeof localStorage !== 'undefined') {
      for (const key of legacyKeys) {
        const item = localStorage.getItem(key);
        if (item) {
          try {
            data[key] = JSON.parse(item);
          } catch {
            data[key] = item;
          }
        }
      }
    }

    return data;
  }

  /**
   * 獲取當前數據版本
   */
  private async getCurrentDataVersion(): Promise<DataVersion> {
    const versionKey = 'cbsc_data_version';
    const version = localStorage.getItem(versionKey);
    return version as DataVersion || '1.0.0';
  }

  /**
   * 遷移數據
   */
  private async migrateData(legacyData: Record<string, any>): Promise<void> {
    const migrationPromises: Promise<void>[] = [];

    Object.entries(legacyData).forEach(([key, data]) => {
      const version = this.versionManager.detectVersion(data);

      if (version !== '2.0.0') {
        migrationPromises.push(
          this.migrateItem(key, data, version)
        );
      }
    });

    await Promise.all(migrationPromises);

    // 更新版本標記
    localStorage.setItem('cbsc_data_version', '2.0.0');
  }

  /**
   * 遷移單個數據項
   */
  private async migrateItem(key: string, data: any, fromVersion: DataVersion): Promise<void> {
    try {
      // 升級數據格式
      let currentData = data;
      let currentVersion = fromVersion;

      while (currentVersion !== '2.0.0') {
        const migration = this.versionManager['migrations'][currentVersion];
        if (!migration) {
          throw new Error(`No migration path from ${currentVersion}`);
        }

        currentData = await migration(currentData);
        currentVersion = this.getNextVersion(currentVersion);
      }

      // 保存遷移後的數據
      await this.adapter.writeData(key, currentData, this.config.enableDualWrite);

    } catch (error) {
      console.error(`Failed to migrate item ${key}:`, error);
      throw error;
    }
  }

  /**
   * 獲取下一版本
   */
  private getNextVersion(current: string): DataVersion {
    const versions: DataVersion[] = ['1.0.0', '1.5.0', '2.0.0'];
    const index = versions.indexOf(current as DataVersion);
    return versions[index + 1] || '2.0.0';
  }

  /**
   * 驗證遷移
   */
  private async validateMigration(): Promise<ValidationReport> {
    const report: ValidationReport = {
      dataIntegrity: {
        isValid: true,
        issues: []
      },
      functionality: {
        isValid: true,
        issues: []
      },
      performance: {
        loadTime: 0,
        memoryUsage: 0
      }
    };

    // 驗證數據完整性
    try {
      const data = await this.adapter.readData('userPreferences');
      if (!data || typeof data !== 'object') {
        report.dataIntegrity.isValid = false;
        report.dataIntegrity.issues.push('User preferences data is invalid');
      }
    } catch (error) {
      report.dataIntegrity.isValid = false;
      report.dataIntegrity.issues.push(`Failed to validate user preferences: ${error}`);
    }

    // 性能測試
    const startTime = performance.now();
    await this.adapter.readData('dashboardConfig');
    report.performance.loadTime = performance.now() - startTime;

    if (performance.memory) {
      report.performance.memoryUsage = performance.memory.usedJSHeapSize;
    }

    return report;
  }

  /**
   * 回滾遷移
   */
  private async rollbackMigration(backupId: string): Promise<void> {
    try {
      await this.backupTool.restoreBackup(backupId);
      console.log('Rollback completed');
    } catch (error) {
      console.error('Rollback failed:', error);
      throw error;
    }
  }

  /**
   * 完成遷移
   */
  async finalizeMigration(): Promise<void> {
    // 禁用雙寫模式
    this.adapter.disableDualWrite();

    // 清理舊數據（可選）
    // await this.cleanupLegacyData();

    console.log('Migration finalized');
  }

  /**
   * 清理舊數據
   */
  private async cleanupLegacyData(): Promise<void> {
    const legacyKeys = [
      'cbsc_user_prefs',
      'dashboard_config',
      'strategy_filters',
      'chart_settings',
    ];

    if (typeof localStorage !== 'undefined') {
      legacyKeys.forEach(key => {
        localStorage.removeItem(key);
      });
    }
  }
}

// 創建全局實例
export const migrationService = new MigrationService();

// 導出類型
export { DataVersionManager, MigrationAdapter, DataBackupTool };