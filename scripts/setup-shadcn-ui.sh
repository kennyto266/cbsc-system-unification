#!/bin/bash

# shadcn/ui 安裝腳本
# 用於快速設置 shadcn/ui 組件庫環境

echo "🚀 開始安裝 shadcn/ui 組件庫..."

# 檢查是否在正確的目錄
if [ ! -f "package.json" ]; then
    echo "❌ 錯誤：請在項目根目錄運行此腳本"
    exit 1
fi

# 進入 frontend 目錄
cd unified-dashboard

# 安裝核心依賴
echo "📦 安裝核心依賴..."
npm install -D tailwindcss-animate
npm install @radix-ui/react-icons \
            class-variance-authority \
            clsx \
            tailwind-merge \
            lucide-react

# 檢查安裝是否成功
if [ $? -ne 0 ]; then
    echo "❌ 依賴安裝失敗"
    exit 1
fi

echo "✅ 依賴安裝成功"

# 創建必要的目錄結構
echo "📁 創建目錄結構..."
mkdir -p src/lib
mkdir -p src/components/ui

# 檢查配置文件
if [ ! -f "components.json" ]; then
    echo "⚠️  警告：components.json 不存在"
    echo "請確保已經創建了 components.json 配置文件"
fi

# 檢查 utils 文件
if [ ! -f "src/lib/utils.ts" ]; then
    echo "⚠️  警告：src/lib/utils.ts 不存在"
    echo "請確保已經創建了 utils.ts 工具函數文件"
fi

# 檢查 Tailwind 配置
if grep -q "tailwindcss-animate" tailwind.config.js; then
    echo "✅ Tailwind 配置已更新"
else
    echo "⚠️  警告：請確保 tailwind.config.js 包含 tailwindcss-animate"
fi

# 檢查 CSS 文件
if grep -q "hsl(var(--background))" src/index.css; then
    echo "✅ CSS 變量已配置"
else
    echo "⚠️  警告：請確保 src/index.css 包含 shadcn/ui 的 CSS 變量"
fi

echo ""
echo "🎉 shadcn/ui 安裝完成！"
echo ""
echo "📚 下一步："
echo "1. 查看文檔：docs/shadcn-ui-integration-guide.md"
echo "2. 運行組件展示：npm run dev 並訪問 /components-showcase"
echo "3. 開始使用組件：import { Button } from '@/components/ui'"
echo ""
echo "💡 提示：使用 npx shadcn-ui@latest add [component-name] 添加更多組件"