@echo off
REM shadcn/ui 安裝腳本 (Windows 版本)
REM 用於快速設置 shadcn/ui 組件庫環境

echo 🚀 開始安裝 shadcn/ui 組件庫...

REM 檢查是否在正確的目錄
if not exist "package.json" (
    echo ❌ 錯誤：請在項目根目錄運行此腳本
    pause
    exit /b 1
)

REM 進入 frontend 目錄
cd unified-dashboard

REM 安裝核心依賴
echo 📦 安裝核心依賴...
call npm install -D tailwindcss-animate
if errorlevel 1 (
    echo ❌ tailwindcss-animate 安裝失敗
    pause
    exit /b 1
)

call npm install @radix-ui/react-icons ^
                 class-variance-authority ^
                 clsx ^
                 tailwind-merge ^
                 lucide-react

if errorlevel 1 (
    echo ❌ 依賴安裝失敗
    pause
    exit /b 1
)

echo ✅ 依賴安裝成功

REM 創建必要的目錄結構
echo 📁 創建目錄結構...
if not exist "src\lib" mkdir src\lib
if not exist "src\components\ui" mkdir src\components\ui

REM 檢查配置文件
if not exist "components.json" (
    echo ⚠️  警告：components.json 不存在
    echo 請確保已經創建了 components.json 配置文件
)

REM 檢查 utils 文件
if not exist "src\lib\utils.ts" (
    echo ⚠️  警告：src\lib\utils.ts 不存在
    echo 請確保已經創建了 utils.ts 工具函數文件
)

REM 檢查 Tailwind 配置
findstr /C:"tailwindcss-animate" tailwind.config.js >nul
if errorlevel 1 (
    echo ⚠️  警告：請確保 tailwind.config.js 包含 tailwindcss-animate
) else (
    echo ✅ Tailwind 配置已更新
)

REM 檢查 CSS 文件
findstr /C:"hsl(var(--background))" src\index.css >nul
if errorlevel 1 (
    echo ⚠️  警告：請確保 src\index.css 包含 shadcn/ui 的 CSS 變量
) else (
    echo ✅ CSS 變量已配置
)

echo.
echo 🎉 shadcn/ui 安裝完成！
echo.
echo 📚 下一步：
echo 1. 查看文檔：docs\shadcn-ui-integration-guide.md
echo 2. 運行組件展示：npm run dev 並訪問 /components-showcase
echo 3. 開始使用組件：import { Button } from '@/components/ui'
echo.
echo 💡 提示：使用 npx shadcn-ui@latest add [component-name] 添加更多組件
echo.
pause