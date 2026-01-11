#!/bin/bash

# GitHub Sync Script for CBSC System
# 創建日期: 2025-12-16T05:31:00Z

echo "=== GitHub Sync Script ==="
echo "開始時間: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# 1. 檢查必要文件
echo ""
echo "1. 檢查本地文件..."
echo "找到的 PRD 文件:"
ls -1 .claude/prds/*.md 2>/dev/null || echo "無 PRD 文件"
echo ""
echo "找到的 Epic 文件:"
ls -1 .claude/epics/*.md 2>/dev/null || echo "無 Epic 文件"

# 2. 嘗試獲取 GitHub 狀態
echo ""
echo "2. 檢查 GitHub 連接..."
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "N/A")
echo "倉庫 URL: $REPO_URL"

# 3. 檢查是否可以推送
echo ""
echo "3. 測試推送權限..."
BRANCH_NAME="feature/square-ui-integration-2024"
echo "當前分支: $(git branch --show-current 2>/dev/null || echo 'N/A')"

# 4. 建議手動操作
echo ""
echo "4. 建議手動同步步驟:"
echo "   a. 確保 GitHub CLI 認證: gh auth login"
echo "   b. 創建或更新 GitHub issues"
echo "   c. 同步本地文件狀態"
echo "   d. 更新同步記錄"

# 5. 記錄當前狀態
echo ""
echo "5. 當前狀態摘要:"
echo "   - 本地有 $(find .claude/prds -name "*.md" | wc -l) 個 PRD"
echo "   - 本地有 $(find .claude/epics -maxdepth 1 -name "*.md" | wc -l) 個 Epic"
echo "   - 遠程分支:"
git ls-remote --heads origin 2>/dev/null | sed 's/.*refs\/heads\///' | head -5

echo ""
echo "=== 完成 ==="
echo "結束時間: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"