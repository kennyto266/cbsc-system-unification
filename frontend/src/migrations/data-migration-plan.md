# 前端數據遷移方案設計

**版本**: 1.0.0
**創建日期**: 2025-12-15
**適用範圍**: CBSC系統前端統一項目

---

## 1. 遷移目標

將現有的多個前端系統（Vanilla JS、React舊版本、混合架構）統一遷移到 React 18 + TypeScript 技術棧，確保：
- 數據完整性
- 功能對等性
- 性能提升
- 開發體驗改善

---

## 2. 數據類型分析

### 2.1 用戶配置數據
```typescript
// 本地存儲的用戶偏好設置
interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-CN' | 'zh-TW' | 'en-US';
  timezone: string;
  dashboardLayout: DashboardLayoutConfig;
  notifications: NotificationSettings;
}

// 舊版本 localStorage key 映射
const LEGACY_STORAGE_KEYS = {
  USER_PREFERENCES: 'cbsc_user_prefs',
  DASHBOARD_CONFIG: 'dashboard_config',
  STRATEGY_FILTERS: 'strategy_filters',
  CHART_SETTINGS: 'chart_settings'
};
```

### 2.2 策略配置數據
```typescript
// 策略相關配置
interface StrategyConfig {
  id: string;
  name: string;
  type: 'price' | 'non-price';
  parameters: Record<string, any>;
  enabled: boolean;
  lastModified: string;
  version: number;
}

// 舊版本數據格式
interface LegacyStrategyConfig {
  strategy_name: string;
  strategy_type: string;
  is_active: boolean;
  params: object;
  updated_at: string;
}
```

### 2.3 儀表板狀態數據
```typescript
// 儀表板狀態
interface DashboardState {
  widgets: WidgetConfig[];
  layout: LayoutConfig;
  filters: FilterConfig;
  selectedStrategies: string[];
  timeRange: TimeRangeConfig;
}
```

---

## 3. 遷移策略

### 3.1 雙寫機制 (Dual-Writing)
在遷移期間，新舊系統並行運行，採用雙寫策略確保數據同步：

```typescript
// 遷移適配器
class MigrationAdapter {
  private isMigrationActive: boolean = true;

  // 寫入操作時同時更新新舊系統
  async writeData(key: string, data: any): Promise<void> {
    // 寫入新系統
    await this.writeToNewSystem(key, data);

    // 遷移期間同時寫入舊系統
    if (this.isMigrationActive) {
      try {
        await this.writeToLegacySystem(key, data);
      } catch (error) {
        console.warn('Legacy write failed:', error);
      }
    }
  }

  // 讀取優先從新系統獲取
  async readData(key: string): Promise<any> {
    try {
      // 優先從新系統讀取
      const newData = await this.readFromNewSystem(key);
      if (newData !== null) return newData;
    } catch (error) {
      console.warn('New system read failed:', error);
    }

    // 新系統無數據時從舊系統讀取
    return await this.readFromLegacySystem(key);
  }
}
```

### 3.2 數據版本控制
實現數據版本管理，處理格式變更：

```typescript
// 數據版本管理器
class DataVersionManager {
  private currentVersion = '2.0.0';

  // 數據遷移映射
  private migrations: Record<string, (data: any) => any> = {
    '1.0.0': this.migrateFromV1.bind(this),
    '1.5.0': this.migrateFromV1_5.bind(this),
  };

  // 版本升級
  async upgradeData(data: any, fromVersion: string): Promise<any> {
    let currentData = data;
    let currentVer = fromVersion;

    while (currentVer !== this.currentVersion) {
      const migration = this.migrations[currentVer];
      if (!migration) {
        throw new Error(`No migration path from ${currentVer}`);
      }

      currentData = await migration(currentData);
      currentVer = this.getNextVersion(currentVer);
    }

    return {
      ...currentData,
      version: this.currentVersion,
      migratedAt: new Date().toISOString()
    };
  }
}
```

---

## 4. 遷移執行計劃

### 4.1 Phase 1: 數據備份與驗證
```typescript
// 數據備份工具
class DataBackupTool {
  async createBackup(): Promise<BackupSnapshot> {
    const snapshot = {
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      data: {
        localStorage: this.getAllLocalStorage(),
        indexedDB: await this.getAllIndexedDB(),
        sessionStorage: this.getAllSessionStorage(),
      }
    };

    // 保存到本地文件或雲端
    await this.saveBackup(snapshot);
    return snapshot;
  }

  async validateDataIntegrity(snapshot: BackupSnapshot): Promise<boolean> {
    // 驗證數據完整性
    const results = await Promise.all([
      this.validateLocalStorage(snapshot.data.localStorage),
      this.validateIndexedDB(snapshot.data.indexedDB),
    ]);

    return results.every(r => r.isValid);
  }
}
```

### 4.2 Phase 2: 數據轉換與遷移
```typescript
// 數據轉換器
class DataTransformer {
  // 轉換用戶偏好設置
  transformUserPreferences(legacy: any): UserPreferences {
    return {
      theme: legacy.theme || 'light',
      language: legacy.lang || 'zh-CN',
      timezone: legacy.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      dashboardLayout: this.transformDashboardLayout(legacy.dashboard),
      notifications: this.transformNotifications(legacy.notifications),
    };
  }

  // 轉換策略配置
  transformStrategyConfig(legacy: any): StrategyConfig {
    return {
      id: legacy.strategy_id || legacy.strategy_name,
      name: legacy.strategy_name,
      type: this.normalizeStrategyType(legacy.strategy_type),
      parameters: this.normalizeParameters(legacy.params),
      enabled: legacy.is_active,
      lastModified: legacy.updated_at,
      version: 1,
    };
  }
}
```

### 4.3 Phase 3: 驗證與切換
```typescript
// 遷移驗證工具
class MigrationValidator {
  async validateMigration(): Promise<ValidationReport> {
    const report = new ValidationReport();

    // 驗證數據完整性
    report.dataIntegrity = await this.checkDataIntegrity();

    // 驗證功能對等性
    report.functionality = await this.checkFunctionality();

    // 驗證性能基準
    report.performance = await this.benchmarkPerformance();

    return report;
  }
}
```

---

## 5. 具體實施步驟

### 5.1 創建遷移服務
```typescript
// src/services/migrationService.ts
export class MigrationService {
  private adapter: MigrationAdapter;
  private versionManager: DataVersionManager;
  private transformer: DataTransformer;

  constructor() {
    this.adapter = new MigrationAdapter();
    this.versionManager = new DataVersionManager();
    this.transformer = new DataTransformer();
  }

  // 執行完整遷移
  async executeMigration(): Promise<void> {
    try {
      // 1. 創建備份
      const backup = await this.createBackup();

      // 2. 檢測現有數據
      const legacyData = await this.detectLegacyData();

      // 3. 轉換數據
      const transformedData = await this.transformData(legacyData);

      // 4. 遷移數據
      await this.migrateData(transformedData);

      // 5. 驗證遷移
      await this.validateMigration();

      console.log('Migration completed successfully');
    } catch (error) {
      console.error('Migration failed:', error);
      await this.rollbackMigration();
      throw error;
    }
  }
}
```

### 5.2 數據存儲抽象層
```typescript
// src/services/storageService.ts
export class StorageService {
  private storage: Map<string, any> = new Map();

  // 統一的存儲接口
  async set<T>(key: string, value: T): Promise<void> {
    const serialized = JSON.stringify({
      data: value,
      version: '2.0.0',
      timestamp: Date.now()
    });

    localStorage.setItem(key, serialized);
  }

  async get<T>(key: string): Promise<T | null> {
    const item = localStorage.getItem(key);
    if (!item) return null;

    try {
      const parsed = JSON.parse(item);
      return parsed.data as T;
    } catch (error) {
      console.error('Failed to parse storage item:', error);
      return null;
    }
  }
}
```

---

## 6. 風險控制

### 6.1 回滾機制
```typescript
// 回滾管理器
class RollbackManager {
  async rollback(backupId: string): Promise<void> {
    const backup = await this.loadBackup(backupId);

    // 恢復 localStorage
    this.restoreLocalStorage(backup.data.localStorage);

    // 恢復 IndexedDB
    await this.restoreIndexedDB(backup.data.indexedDB);

    // 通知用戶回滾完成
    this.notifyRollbackComplete();
  }
}
```

### 6.2 監控告警
```typescript
// 遷移監控
class MigrationMonitor {
  async monitor(): Promise<void> {
    // 監控數據同步延遲
    this.measureSyncLatency();

    // 監控錯誤率
    this.trackErrorRate();

    // 監控性能指標
    this.trackPerformanceMetrics();
  }
}
```

---

## 7. 時間表

| 階段 | 任務 | 預計時間 | 責任人 |
|------|------|----------|--------|
| 1 | 數據備份工具開發 | 1天 | 前端工程師 |
| 2 | 遷移適配器開發 | 2天 | 前端工程師 |
| 3 | 數據轉換器開發 | 2天 | 前端工程師 |
| 4 | 測試環境驗證 | 1天 | QA團隊 |
| 5 | 生產環境遷移 | 1天 | DevOps團隊 |
| 6 | 監控與優化 | 持續 | 全體團隊 |

---

## 8. 驗收標準

1. **數據完整性**: 所有用戶數據 100% 遷移成功
2. **功能對等**: 所有現有功能在新系統正常運行
3. **性能提升**: 頁面加載速度提升 30%+
4. **錯誤率**: 遷移後錯誤率 < 0.1%

---

## 9. 後續維護

1. **清理舊代碼**: 遷移完成後清理舊系統代碼
2. **文檔更新**: 更新所有相關技術文檔
3. **培訓**: 對開發團隊進行新系統培訓
4. **監控**: 持續監控系統運行狀況