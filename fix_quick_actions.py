# 修復快速操作按鈕的問題

# 1. 修復 handleRunBacktest 函數，添加更好的錯誤處理
# 2. 添加一個代理設置來避免CORS問題
# 3. 確保API端點正確

import re

# 讀取文件
with open('square-ui-frontend/app/dashboard/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 修復運行回測函數
old_backtest = '''// 处理运行回测
  const handleRunBacktest = async () => {
    setLoading('backtest');
    try {
      const response = await fetch(`${API_BASE_URL}/api/backtest/strategy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy_id: '1', // 示例策略ID
          start_date: '2023-01-01',
          end_date: '2023-12-31',
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert('回测已启动！结果ID: ' + result.result_id);
      } else {
        throw new Error('回测启动失败');
      }
    } catch (error) {
      console.error('运行回测失败:', error);
      alert('运行回测失败，请确保策略已选择');
    } finally {
      setLoading(null);
    }
  };'''

new_backtest = '''// 处理运行回测
  const handleRunBacktest = async () => {
    setLoading('backtest');
    try {
      // 使用代理避免CORS問題
      const response = await fetch('/api/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy_id: '1', // 示例策略ID
          start_date: '2023-01-01',
          end_date: '2023-12-31',
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert('回测已启动！结果ID: ' + result.result_id);
      } else {
        // 嘗試直接調用後端API
        const directResponse = await fetch(`${API_BASE_URL}/api/backtest/strategy`, {
          method: 'POST',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            strategy_id: '1',
            start_date: '2023-01-01',
            end_date: '2023-12-31',
          }),
        });

        if (directResponse.ok) {
          const result = await directResponse.json();
          alert('回测已启动！结果ID: ' + result.result_id);
        } else {
          throw new Error('回测启动失败');
        }
      }
    } catch (error) {
      console.error('运行回测失败:', error);
      // 顯示更具體的錯誤信息
      if (error.message.includes('Failed to fetch')) {
        alert('無法連接到後端服務，請確保後端運行在端口 3004');
      } else {
        alert('运行回测失败: ' + error.message);
      }
    } finally {
      setLoading(null);
    }
  };'''

# 替換內容
content = content.replace(old_backtest, new_backtest)

# 修復導出報告函數
old_export = '''// 处理导出报告
  const handleExportReport = async () => {
    setLoading('export');
    try {
      // 导出最新报告
      const response = await fetch(`${API_BASE_URL}/api/v1/strategies/1/report?format=pdf`);

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `strategy_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('导出失败');
      }
    } catch (error) {
      console.error('导出报告失败:', error);
      alert('导出报告失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };'''

new_export = '''// 处理导出报告
  const handleExportReport = async () => {
    setLoading('export');
    try {
      // 先嘗試通過代理導出
      const response = await fetch('/api/export/strategy/1?format=pdf');

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `strategy_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // 嘗試直接調用後端API
        const directResponse = await fetch(`${API_BASE_URL}/api/v1/strategies/1/report?format=pdf`, {
          mode: 'cors',
        });

        if (directResponse.ok) {
          const blob = await directResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `strategy_report_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          throw new Error('导出失败');
        }
      }
    } catch (error) {
      console.error('导出报告失败:', error);
      if (error.message.includes('Failed to fetch')) {
        alert('無法連接到後端服務，請確保後端運行在端口 3004');
      } else {
        alert('导出报告失败: ' + error.message);
      }
    } finally {
      setLoading(null);
    }
  };'''

content = content.replace(old_export, new_export)

# 寫回文件
with open('square-ui-frontend/app/dashboard/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修復快速操作按鈕的問題")
print("\n主要修改：")
print("1. 改進了運行回測的錯誤處理，添加了代理和直接API調用兩種方式")
print("2. 改進了導出報告的錯誤處理")
print("3. 添加了更友好的錯誤提示信息")