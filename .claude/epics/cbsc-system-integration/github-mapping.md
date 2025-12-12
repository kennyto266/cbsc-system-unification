# GitHub Mapping for CBSC System Integration Epic

## Epic Mapping
- **Local Epic**: `.claude/epics/cbsc-system-integration/epic.md`
- **GitHub Issue**: #28 - "CBSC系統統一整合 Epic" (未找到對應issue，需要創建)
- **Status**: Local epic存在，GitHub上沒有對應issue
- **Last Sync**: 2025-12-12T10:00:00Z

## Task Mapping

### Found GitHub Tasks (需要映射到本地)
- #18: "Task 004: 數據架構重構 - PostgreSQL + Redis 統一架構" → `.claude/epics/cbsc-system-integration/004.md`
- #17: "Task 003: 後端服務整合 - API網關與服務治理" → `.claude/epics/cbsc-system-integration/003.md`
- #23: "CacheManager核心实现" → `.claude/epics/cbsc-system-integration/004.md` (子任務)
- #24: "缓存集成与监控" → `.claude/epics/cbsc-system-integration/004.md` (子任務)
- #25: "数据库分区与归档系统" → `.claude/epics/cbsc-system-integration/004.md` (子任務)
- #26: "WebSocket连接池实现" → `.claude/epics/cbsc-system-integration/003.md` (子任務)
- #27: "WebSocket压力测试与监控" → `.claude/epics/cbsc-system-integration/003.md` (子任務)

### Local Tasks (需要映射到GitHub)
- `.claude/epics/cbsc-system-integration/001.md` → GitHub上未找到
- `.claude/epics/cbsc-system-integration/002.md` → GitHub上未找到

## Sync Actions Required

1. **Create GitHub Issue for Epic**: #28 "CBSC系統統一整合 Epic"
2. **Create GitHub Issues**:
   - Task 001: 前端系統統一 - React整合與UI組件庫
   - Task 002: 策略管理系統重構 - 模組化重構與API統一
3. **Link existing subtasks**: #23-27 作為Task 003/004的子任務
4. **Update local frontmatter**: 添加GitHub URL和同步狀態

## Notes
- GitHub上的task編號與本地不匹配
- 需要建立清晰的父子任務關係
- 部分GitHub task是其他task的子任務