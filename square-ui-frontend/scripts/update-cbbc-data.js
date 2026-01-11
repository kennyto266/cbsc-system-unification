// 更新 CBBC 數據腳本
// 將最新的爬蟲數據複製到系統可讀取的位置

const fs = require('fs');
const path = require('path');

// 源文件路徑
const sourcePath = 'C:\\Users\\Penguin8n\\爬蟲\\hkex爬蟲\\data\\top_stocks\\cbbc_latest_fixed.csv';

// 目標文件路徑（更新日期標記）
const targetPath = 'C:\\Users\\Penguin8n\\爬蟲\\hkex爬蟲\\data\\top_stocks\\cbbc_2025-12-16.csv';

console.log('🔄 更新 CBBC 數據...');
console.log(`來源: ${sourcePath}`);

try {
  // 檢查源文件是否存在
  if (!fs.existsSync(sourcePath)) {
    console.error('❌ 源文件不存在');
    process.exit(1);
  }

  // 讀取源文件
  const data = fs.readFileSync(sourcePath, 'utf-8');

  // 更新日期標記
  const updatedData = data.replace(/"2025-\d{2}-\d{2}"/g, '"2025-12-16"');

  // 寫入新文件
  fs.writeFileSync(targetPath, updatedData);

  console.log(`✅ 數據已更新到: ${targetPath}`);

  // 顯示文件信息
  const stats = fs.statSync(targetPath);
  console.log(`📊 文件大小: ${(stats.size / 1024).toFixed(2)} KB`);
  console.log(`📅 修改時間: ${stats.mtime}`);

} catch (error) {
  console.error('❌ 更新失敗:', error.message);
  process.exit(1);
}