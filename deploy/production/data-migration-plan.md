# CBSC系統生產環境數據遷移方案

## 方案概述

本文檔描述了CBSC量化交易系統從測試環境到生產環境的數據遷移方案，包括遷移策略、實施步驟、風險控制應急預案。

### 遷移目標
- 確保數據完整性：100%數據遷移，零數據丟失
- 最小化停機時間：核心業務停機 < 4小時
- 數據一致性：保證業務數據的一致性和準確性
- 平滑過渡：無縫切換，用戶無感知

### 遷移範圍

#### 核心業務數據
1. **用戶數據**
   - 用戶基本信息（100萬條）
   - 用戶權限配置
   - 用戶偏好設置
   - 登錄日誌

2. **策略數據**
   - 策略定義（50萬個）
   - 策略參數配置
   - 策略版本歷史
   - 策略執行記錄

3. **交易數據**
   - 訂單記錄（1000萬條）
   - 成交記錄（800萬條）
   - 持倉記錄（500萬條）
   - 資金流水

4. **市場數據**
   - 實時行情數據
   - 歷史K線數據（5年）
   - 技術指標數據
   - 經濟指標數據

5. **系統數據**
   - 系統配置
   - 審計日誌
   - 監控指標
   - 報表數據

### 遷移統計

| 數據類型 | 數據量 | 預計時間 | 遷移方式 |
|----------|--------|----------|----------|
| 用戶數據 | 10GB | 1小時 | 全量 |
| 策略數據 | 50GB | 2小時 | 全量 |
| 交易數據 | 100GB | 4小時 | 增量 |
| 市場數據 | 500GB | 6小時 | 離同步 |
| 系統數據 | 20GB | 30分鐘 | 全量 |
| **總計** | **680GB** | **13.5小時** | - |

## 遷移策略

### 遷移方法選擇

#### 1. 全量遷移
- **適用場景**：用戶數據、策略數據、系統數據
- **優點**：簡單可靠，數據一致性保證
- **缺點**：遷移時間長，業務中斷
- **實施**：在維護窗口期間進行

#### 2. 增量遷移
- **適用場景**：交易數據、實時數據
- **優點**：業務中斷短，可實時同步
- **缺點**：實現複雜，需要數據校驗
- **實施**：雙寫機制，實時同步

#### 3. 混合遷移
- **適用場景**：結合全量和增量的優勢
- **優點**：平衡效率和業務影響
- **缺點**：管理複雜度增加
- **實施**：靜態數據全量，動態數據增量

### 遷移模式

#### 1. 雙寫模式（Dual-write）
```python
# 雙寫實現示例
class DualWriteHandler:
    def __init__(self, old_db, new_db):
        self.old_db = old_db
        self.new_db = new_db
        self.write_queue = Queue()
        
    def write_data(self, table, data):
        # 先寫新庫
        success = self.new_db.write(table, data)
        if success:
            # 後寫舊庫（異步）
            self.write_queue.put(('old', table, data))
            return True
        return False
        
    async def process_queue(self):
        while True:
            try:
                db_type, table, data = await self.write_queue.get()
                if db_type == 'old':
                    self.old_db.write(table, data)
            except Exception as e:
                logger.error(f"Queue write error: {e}")
```

#### 2. CDC模式（Change Data Capture）
```yaml
# Debezium配置示例
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: postgres-connector
spec:
  class: DebeziumPostgreSqlConnector
  tasksMax: 3
  config:
    database.hostname: postgres-source
    database.port: 5432
    database.user: debezium
    database.password: debezium
    database.dbname: cbsc
    database.server.name: cbsc-source
    plugin.name: pgoutput
    transforms: route
    transforms.route.type: org.apache.kafka.connect.transforms.RegexRouter
    transforms.route.regex: ([^.]+)\\.([^.]+).([^.]+)
    transforms.route.replacement: $2
```

## 實施計劃

### Phase 1：準備階段（1天）

#### 1.1 環境準備
- [ ] 生產環境部署完成
- [ ] 網絡連通測試
- [ ] 遷移工具準備就緒
- [ ] 監控告警配置完成

#### 1.2 數據準備
- [ ] 源庫數據完整備份
- [ ] 數據質量檢查
- [ ] 數據清洗和格式化
- [ ] 遷移腳本驗證

#### 1.3 人員準備
- [ ] DBA團隊到位
- [ ] 運維團隊培訓
- [ ] 業務方確認時間窗口
- [ ] 應急聯繫方式確認

### Phase 2：靜態數據遷移（2天）

#### 2.1 遷移順序
1. 系統配置數據（30分鐘）
2. 用戶數據（2小時）
3. 策略數據（3.5小時）
4. 基礎市場數據（3小時）

#### 2.2 遷移腳本
```bash
#!/bin/bash
# 數據遷移主腳本

set -e

# 配置參數
SOURCE_DB="source.cbsc.com"
TARGET_DB="target.cbsc.com"
BACKUP_DIR="/backup/$(date +%Y%m%d)"
LOG_FILE="/var/log/migration/$(date +%Y%m%d).log"

# 創建日誌
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "=== Starting Data Migration ==="
echo "Source: $SOURCE_DB"
echo "Target: $TARGET_DB"
echo "Time: $(date)"

# 1. 系統配置遷移
echo "Migrating system configurations..."
pg_dump -h $SOURCE_DB -U postgres cbsc_config > $BACKUP_DIR/config.sql
psql -h $TARGET_DB -U postgres -d cbsc_new < $BACKUP_DIR/config.sql

# 2. 用戶數據遷移
echo "Migrating user data..."
pg_dump -h $SOURCE_DB -U postgres cbsc_users -t users -t user_permissions -t user_preferences > $BACKUP_DIR/users.sql
psql -h $TARGET_DB -U postgres -d cbsc_new < $BACKUP_DIR/users.sql

# 3. 策略數據遷移
echo "Migrating strategy data..."
pg_dump -h $SOURCE_DB -U postgres cbsc_strategies -t strategies -t strategy_parameters -t strategy_versions > $BACKUP_DIR/strategies.sql
psql -h $TARGET_DB -U postgres -d cbsc_new < $BACKUP_DIR/strategies.sql

# 4. 數據驗證
echo "Verifying migrated data..."
psql -h $TARGET_DB -U postgres -d cbsc_new -c "SELECT COUNT(*) FROM users;" > user_count_new.txt
psql -h $SOURCE_DB -U postgres -d cbsc -c "SELECT COUNT(*) FROM users;" > user_count_old.txt

# 比較記錄數
if diff user_count_new.txt user_count_old.txt; then
    echo "ERROR: User count mismatch!"
    exit 1
else
    echo "User data migration verified"
fi

echo "=== Data Migration Completed Successfully ==="
```

#### 2.3 數據驗證
```python
#!/usr/bin/env python3
"""
數據遷移驗證腳本
"""

import psycopg2
import hashlib
from datetime import datetime

def verify_migration():
    """驗證遷移數據的完整性"""
    
    # 連接源庫和目標庫
    source_conn = psycopg2.connect(
        host="source.cbsc.com",
        database="cbsc",
        user="postgres"
    )
    
    target_conn = psycopg2.connect(
        host="target.cbsc.com", 
        database="cbsc_new",
        user="postgres"
    )
    
    verification_results = {}
    
    # 驗證用戶數據
    verification_results['users'] = verify_table_data(
        source_conn, target_conn, 'users'
    )
    
    # 驗證策略數據
    verification_results['strategies'] = verify_table_data(
        source_conn, target_conn, 'strategies'
    )
    
    # 生成驗證報告
    generate_verification_report(verification_results)
    
    return verification_results

def verify_table_data(source_conn, target_conn, table_name):
    """驗證單個表的數據"""
    
    # 獲取記錄數
    source_count = get_table_count(source_conn, table_name)
    target_count = get_table_count(target_conn, table_name)
    
    # 比較記錄數
    if source_count != target_count:
        return {
            'status': 'FAIL',
            'source_count': source_count,
            'target_count': target_count,
            'difference': abs(source_count - target_count)
        }
    
    # MD5校驗
    source_md5 = calculate_md5(source_conn, table_name)
    target_md5 = calculate_md5(target_conn, table_name)
    
    if source_md5 != target_md5:
        return {
            'status': 'FAIL',
            'source_count': source_count,
            'target_count': target_count,
            'md5_mismatch': True,
            'source_md5': source_md5,
            'target_md5': target_md5
        }
    
    return {
        'status': 'PASS',
        'count': source_count,
        'md5': source_md5
    }

if __name__ == "__main__":
    results = verify_migration()
    
    if all(result['status'] == 'PASS' for result in results.values()):
        print("✅ All data migration verification passed!")
    else:
        print("❌ Data migration verification failed!")
        for table, result in results.items():
            if result['status'] == 'FAIL':
                print(f"Table {table}: {result}")
```

### Phase 3：動態數據同步（1天）

#### 3.1 同步配置

```yaml
# 數據同步服務配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-sync-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-sync
  template:
    metadata:
      labels:
        app: data-sync
    spec:
      containers:
      - name: sync-service
        image: cbsc/data-sync:v1.0
        env:
        - name: SOURCE_DB
          value: "source.cbsc.com"
        - name: TARGET_DB
          value: "target.cbsc.com"
        - name: SYNC_MODE
          value: "realtime"
        volumeMounts:
        - name: sync-config
          mountPath: /etc/sync
      volumes:
      - name: sync-config
        configMap:
          name: sync-config
```

#### 3.2 CDC配置

```yaml
# CDC配置
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: cbsc-cdc-connector
  labels:
    strimzi.io/cluster: my-kafka-cluster
spec:
  class: DebeziumPostgreSqlConnector
  tasksMax: 4
  config:
    database.hostname: postgres-source
    database.port: 5432
    database.user: debezium
    database.password: debezium
    database.dbname: cbsc
    database.server.name: cbsc-source
    plugin.name: pgoutput
    transforms: route
    transforms.route.type: org.apache.kafka.connect.transforms.RegexRouter
    transforms.route.regex: ([^.]+)\\.([^.]+).([^.]+)
    transforms.route.replacement: $2
    schema.history.internal.kafka.bootstrap.servers: kafka:9092
    schema.history.internal.kafka.topic: schema-changes.cbsc
    database.changes.mode: 'filtered'
    table.include.list: 'public.trades,public.orders,public.positions'
    column.exclude.list: 'password,token'
```

### Phase 4：切換階段（2小時）

#### 4.1 切換計劃

```
Time     Operation
-----------------
00:00    - 業務停止，凍結新交易
00:05    - 數據增量同步
00:30    - 業務驗證
00:45    - DNS切換到新系統
01:00    - 業務恢復
01:15    - 監控觀察
02:00    - 切換完成
```

#### 4.2 DNS切換腳本

```bash
#!/bin/bash
# DNS切換腳本

CURRENT_IP="203.0.113.10"
NEW_IP="203.0.113.20"
DOMAIN="api.cbsc.com"

echo "Starting DNS switch for $DOMAIN"
echo "Current IP: $CURRENT_IP"
echo "New IP: $NEW_IP"

# 更新DNS記錄
aws route53 change-resource-record-sets \
    --hosted-zone-id Z3P3QEXAMPLEEXAMPLE \
    --change-batch '{
        "Comment": "Switch to production",
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "api.cbsc.com",
                    "Type": "A",
                    "TTL": 60,
                    "ResourceRecords": [
                        {
                            "Value": "'$NEW_IP'"
                        }
                    ]
                }
            }
        ]
    }'

echo "DNS switch completed"

# 驗證DNS更新
echo "Verifying DNS update..."
nslookup api.cbsc.com

echo "DNS switch verification completed"
```

### Phase 5：後續清理（1天）

#### 5.1 清理任務
- [ ] 舊庫連接釋放
- [ ] 臨時數據刪除
- [ ] 同步服務停止
- [ ] 日誌證歸檔

#### 5.2 總結報告
- 遷移統計匯總
- 問題記錄與總結
- 經驗教訓提煉
- 後續改進建議

## 風險控制

### 風險識別

#### 1. 技術風險
- **數據丟失**：備份不完整或遷移失敗
- **數據不一致**：同步延遲導致不一致
- **性能影響**：遷移過程影響系統性能
- **業務中斷**：切換失敗導致長時間停機

#### 2. 業務風險
- **用戶體驗**：切換過程影響用戶操作
- **交易損失**：停機期間錯過交易機會
- **數據延遲**：遷移後數據不同步

#### 3. 操作風險
- **操作失誤**：人工操作失誤導致故障
- **時間延期**：延遲影響其他計劃
- **溝通不暢**：信息傳遞不及時

### 風險應對措施

#### 1. 數據保護
```bash
# 全量備份腳本
#!/bin/bash

BACKUP_DIR="/backup/migration/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 數據庫備份
pg_dumpall -h $SOURCE_DB -U postgres > $BACKUP_DIR/all_databases.sql

# 關鍵表備份
pg_dump -h $SOURCE_DB -U postgres -t users > $BACKUP_DIR/users.sql
pg_dump -h $SOURCE_DB -U postgres -t strategies > $BACKUP_DIR/strategies.sql
pg_dump -h $SOURCE_DB -U postgres -t trades > $BACKUP_DIR/trades.sql

# 壓縮備份
tar -czf $BACKUP_DIR/data_backup.tar.gz /var/lib/postgresql/data/

echo "Backup completed: $BACKUP_DIR"
```

#### 2. 回滾方案
```python
#!/usr/bin/env python3
"""
回滾腳本
"""

class RollbackManager:
    def __init__(self):
        self.rollback_steps = [
            self.restore_dns,
            self.stop_new_system,
            self.restore_old_connections,
            self.restore_data
        ]
    
    def execute_rollback(self):
        """執行回滾操作"""
        print("Starting rollback...")
        
        for step in self.rollback_steps:
            try:
                step()
                print(f"✓ {step.__name__} completed")
            except Exception as e:
                print(f"✗ {step.__name__} failed: {e}")
                raise
        
        print("Rollback completed successfully")
    
    def restore_dns(self):
        """恢復DNS設置"""
        # 恢復DNS到舊IP
        pass
    
    def stop_new_system(self):
        """停止新系統服務"""
        # kubectl stop部署
        pass
    
    def restore_old_connections(self):
        """恢復舊的數據庫連接"""
        # 更新應用配置
        pass
    
    def restore_data(self):
        """恢復數據（如必要）"""
        # 從份中恢復
        pass
```

#### 3. 監控告警

```yaml
# 遷移期間監控配置
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: migration-monitoring
spec:
  groups:
  - name: migration
    rules:
    - alert: DataMigrationDelay
      expr: time() - migration_last_success_timestamp > 300
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Data migration delay detected"
    
    - alert: MigrationErrorRate
      expr: migration_error_count / migration_total_count > 0.05
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Migration error rate too high"
```

## 應急預案

### 緊急情況定義

#### P0 - 系統完全不可用
- 數據庫完全損壞
- 網絡完全中斷
- 服務全部宕機

#### P1 - 部分功能不可用
- 核心業務無法訪問
- 數據同步中斷超過10分鐘
- 關鍵API響應超時

#### P2 - 性能嚴重下降
- 響應時間超過5秒
- 錯誤率超過5%
- 用戶投訴增加

### 應急響應流程

#### P0響應流程
```
0分鐘：
- 立即通知應急負責人
- 激活應急響應團隊
- 通知相關領導

5分鐘：
- 評評問題嚴重程度
- 啟動回滾程序
- 通報影響範圍

15分鐘：
- 實施回滾操作
- 監控恢復進度
- 更新狀態通報

30分鐘：
- 完成系統恢復
- 業務驗證
- 問題分析報告
```

#### 聯繫方式
```
緊急聯繫：
- 總指揮：138-0000-0001
- 技術負責人：138-0000-0002
- 運維負責人：138-0000-0003

備用聯繫：
- 應急郵箱：emergency@cbsc.com
- 應急電話：400-888-8888
- 郵件群：@emergency-alerts
```

## 成功標準

### 技術指標
- [ ] 數據完整性：100%
- [ ] 數據一致性：所有表記錄一致
- [ ] 遷移成功率：100%
- [ ] 系統可用性：> 99.9%

### 業務指標
- [ ] 用戶體驗：無投訴
- [ ] 業務影響：零交易損失
- [ ] 系統切換：平滑無感知
- [ ] 恢復時間：< 2小時

### 時間指標
- [ ] 準備時間：按計劃完成
- [ ] 遷移時間：在預定窗口內
- [ ] 驗證時間：4小時內完成
- [ ] 切換時間：小於1小時

## 總結

本數據遷移方案提供了完整的遷移策略、實施步驟和風險控制措施。通過嚴格按照此方案執行，可以確保數據安全、準確、高效地遷移到生產環境。

遷移成功後，系統將具備更好的性能、擴展性和穩定性，為業務快速發展奠定堅實基礎。

---

**文檔版本**：v1.0  
**最後更新**：2024年12月18日  
**下次審核**：遷移完成後1周