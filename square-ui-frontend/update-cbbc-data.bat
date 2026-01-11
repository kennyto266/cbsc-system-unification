@echo off
echo ========================================
echo CBBC 數據更新工具
echo ========================================
echo.

REM 設置日期
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "DATE=%YYYY%-%MM%-%DD%"

echo 1. 運行爬蟲獲取最新數據...
cd /d "C:\Users\Penguin8n\爬蟲\hkex爬蟲"
node daily-updater.js
echo.

echo 2. 複製數據到今日文件...
if exist "data\top_stocks\cbbc_latest_fixed.csv" (
    copy "data\top_stocks\cbbc_latest_fixed.csv" "data\top_stocks\cbbc_%DATE%.csv"
    echo ✅ 數據已更新
) else (
    echo ❌ 未找到爬蟲數據文件
)
echo.

echo 3. 重新啟動 API 服務...
cd /d "C:\Users\Penguin8n\CODEX--\square-ui-frontend"
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start cmd /c "npm run dev"
echo ✅ API 服務已重啟
echo.

echo ========================================
echo 更新完成！
echo 訪問 http://localhost:3001/dashboard 查看
echo ========================================
pause