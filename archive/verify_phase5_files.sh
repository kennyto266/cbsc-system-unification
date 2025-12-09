#!/bin/bash

echo "=========================================="
echo "Phase 5 隱私控制系統 - 文件驗證"
echo "=========================================="
echo ""

# 計數器
total=0
found=0
missing=0

# 檢查文件函數
check_file() {
    local file=$1
    local desc=$2
    total=$((total + 1))
    
    if [ -f "$file" ]; then
        found=$((found + 1))
        size=$(du -h "$file" | cut -f1)
        echo "✅ $desc"
        echo "   路徑: $file"
        echo "   大小: $size"
        echo ""
    else
        missing=$((missing + 1))
        echo "❌ $desc - 文件缺失"
        echo "   預期路徑: $file"
        echo ""
    fi
}

echo "檢查後端核心模塊..."
echo "----------------------------------------"
check_file "/c/Users/Penguin8n/CODEX--/src/privacy/sovereignty_controls.py" "T110: 數據主權控制"
check_file "/c/Users/Penguin8n/CODEX--/src/privacy/transparency_report.py" "T111: 透明度報告生成"
check_file "/c/Users/Penguin8n/CODEX--/src/privacy/audit_tools.py" "T112: 隱私審計工具"

echo "檢查前端組件..."
echo "----------------------------------------"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/components/PrivacySettings.vue" "T109: 隱私設置面板"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/stores/privacy.js" "隱私狀態管理"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/i18n/index.js" "i18n配置"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/i18n/zh-CN.js" "中文翻譯"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/i18n/en-US.js" "英文翻譯"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/router/index.js" "路由配置"
check_file "/c/Users/Penguin8n/CODEX--/frontend/src/main.js" "主應用入口"

echo "檢查文檔文件..."
echo "----------------------------------------"
check_file "/c/Users/Penguin8n/CODEX--/PHASE5_PRIVACY_CONTROL_GUIDE.md" "完整用戶手冊"
check_file "/c/Users/Penguin8n/CODEX--/PHASE5_QUICK_START.md" "快速開始指南"
check_file "/c/Users/Penguin8n/CODEX--/PHASE5_IMPLEMENTATION_SUMMARY.md" "實現總結"
check_file "/c/Users/Penguin8n/CODEX--/PHASE5_FILES_OVERVIEW.md" "文件清單"

echo "=========================================="
echo "驗證結果統計"
echo "=========================================="
echo "總文件數: $total"
echo "已找到: $found"
echo "缺失: $missing"
echo ""

if [ $missing -eq 0 ]; then
    echo "🎉 所有文件已成功創建！"
    echo "✅ Phase 5 隱私控制系統已完成！"
else
    echo "⚠️  發現 $missing 個缺失文件"
fi

echo ""
echo "=========================================="
