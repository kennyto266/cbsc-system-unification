---
allowed-tools: Read
---

# 📚 Claude Code PM - Project Management System

## 🎯 快速开始工作流
1. `/pm:prd-new <name>`        - 创建新的产品需求文档
2. `/pm:prd-parse <name>`      - 将PRD转换为实施计划
3. `/pm:epic-decompose <name>` - 分解为任务
4. `/pm:epic-show <name>`      - 查看计划和任务

## 📄 PRD 命令 (产品需求)
- `/pm:prd-new <name>`     - 为新产品需求启动头脑风暴
- `/pm:prd-parse <name>`   - 将PRD转换为实施计划
- `/pm:prd-list`           - 列出所有PRD
- `/pm:prd-status`         - 显示PRD实施状态

## 📚 Epic 命令 (实施计划)
- `/pm:epic-decompose <name>` - 将计划分解为任务文件
- `/pm:epic-list`             - 列出所有计划
- `/pm:epic-show <name>`      - 显示计划及其任务
- `/pm:epic-status [name]`    - 显示计划进度

## 🔄 工作流命令
- `/pm:next`               - 显示下一个优先任务
- `/pm:status`             - 整体项目仪表板
- `/pm:blocked`            - 显示被阻塞的任务
- `/pm:in-progress`        - 列出进行中的工作

## 🔧 维护命令
- `/pm:validate`           - 检查系统完整性
- `/pm:search <query>`     - 搜索所有内容

## 💡 提示
• 使用 `/pm:next` 查找可用工作
• 运行 `/pm:status` 快速概览
• 本地模式工作流：prd-new → prd-parse → epic-decompose → epic-show
• 查看 README.md 获取完整文档

## 🏠 本地模式
所有命令都可以在本地模式下工作，无需GitHub集成：
- PRD存储在 `.claude/prds/`
- 计划存储在 `.claude/epics/`
- 任务存储为markdown文件
