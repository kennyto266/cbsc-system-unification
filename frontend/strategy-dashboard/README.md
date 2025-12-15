# CBSC策略管理Dashboard

個人策略管理系統的基礎頁面結構和樣式實現。

## 📁 項目結構

```
strategy-dashboard/
├── index.html              # 主頁面文件
├── css/
│   └── dashboard.css       # 樣式文件
├── js/
│   └── dashboard.js        # 交互腳本
├── test.html               # 測試頁面
├── README.md               # 說明文檔
└── assets/                 # 靜態資源 (待創建)
    ├── favicon.ico
    ├── logo.svg
    └── images/
```

## 🚀 快速開始

### 1. 直接打開

在瀏覽器中打開 `index.html` 文件即可查看Dashboard。

### 2. 本地服務器

推薦使用本地HTTP服務器來避免跨域問題：

```bash
# 使用Python內建服務器
cd strategy-dashboard
python -m http.server 8080

# 或使用Node.js服務器
npx serve . -p 8080

# 或使用PHP服務器
php -S localhost:8080
```

然後訪問 `http://localhost:8080`

## 🎨 設計系統

### 色彩方案

- **主色調**: `#2c3e50` (深藍灰)
- **強調色**: `#3498db` (藍色)
- **成功色**: `#27ae60` (綠色)
- **警告色**: `#f39c12` (橙色)
- **危險色**: `#e74c3c` (紅色)

### 字體系統

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
```

### 間距系統

基於8px網格系統：4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px, 80px

### 響應式斷點

- **桌面**: ≥1200px
- **平板**: 768px-1199px
- **手機**: ≤767px

## 📊 功能特性

### ✅ 已實現功能

- [x] 響應式頁面布局
- [x] 導航菜單系統
- [x] 策略列表展示
- [x] 統計卡片組件
- [x] 圖表容器預留
- [x] 快速操作面板
- [x] 通知系統
- [x] 連接狀態指示
- [x] 鍵盤快捷鍵支持
- [x] 性能優化

### 🔄 集成準備

- [ ] Chart.js圖表集成
- [ ] WebSocket實時數據
- [ ] 後端API連接
- [ ] 用戶認證系統
- [ ] 數據持久化

## 🛠 開發指南

### HTML結構

頁面採用語義化HTML5標籤，支持無障礙訪問：

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <!-- Meta tags and styles -->
  </head>
  <body>
    <header class="app-header">
      <!-- Navigation -->
    </header>
    <main class="app-main">
      <!-- Main content -->
    </main>
    <footer class="app-footer">
      <!-- Footer -->
    </footer>
  </body>
</html>
```

### CSS架構

使用CSS變量和BEM命名規範：

```css
/* CSS Variables */
:root {
  --primary-color: #2c3e50;
  --spacing-4: 1rem;
}

/* Component styles */
.component-name {
  /* Base styles */
}

.component-name__element {
  /* Element styles */
}

.component-name--modifier {
  /* Modifier styles */
}
```

### JavaScript架構

採用ES6類的模塊化設計：

```javascript
class Dashboard {
  constructor() {
    // Initialize
  }

  async init() {
    // Setup dashboard
  }

  // Methods...
}
```

## 📱 響應式設計

### 桌面端 (1920x1080+)

- 雙列布局
- 完整功能展示
- 豐富的交互效果

### 平板端 (768px-1199px)

- 單列布局
- 簡化導航
- 觸摸優化

### 手機端 (≤767px)

- 垂直布局
- 漢堡菜單
- 簡潔界面

## 🔧 自定義配置

### 修改顏色主題

在 `css/dashboard.css` 中修改CSS變量：

```css
:root {
  --primary-color: #your-color;
  --secondary-color: #your-color;
  /* ... */
}
```

### 調整布局

修改 `.main-container` 的最大寬度：

```css
.main-container {
  max-width: 1600px; /* 調整這個值 */
}
```

### 添加新頁面

1. 在 `index.html` 中添加新的頁面容器：

```html
<div id="new-page" class="page-content">
  <!-- Page content -->
</div>
```

2. 在導航中添加鏈接：

```html
<a href="#new" class="nav-link" data-page="new">
  <span class="nav-icon">🔗</span>
  <span class="nav-text">新頁面</span>
</a>
```

3. 在 `js/dashboard.js` 中處理頁面邏輯。

## 🧪 測試

### 功能測試

打開 `test.html` 查看所有功能的完成狀態。

### 響應式測試

在瀏覽器開發者工具中測試不同屏幕尺寸：

1. 打開開發者工具 (F12)
2. 點擊設備模擬按鈕
3. 選擇不同設備或自定義尺寸

### 性能測試

使用瀏覽器開發者工具的Performance和Network面板：

1. 記錄頁面加載性能
2. 檢查資源加載時間
3. 分析渲染瓶頸

## 📈 性能優化

### 已實現優化

- CSS變量減少重複
- 圖片懶加載準備
- JavaScript防抖處理
- 資源預加載

### 建議優化

- [ ] 圖片壓縮和WebP格式
- [ ] CSS和JS文件壓縮
- [ ] CDN加速
- [ ] Service Worker緩存

## 🔌 API集成

### WebSocket連接

```javascript
// 在 dashboard.js 中配置
this.config = {
  wsUrl: 'ws://localhost:3005/ws',
  // ...
}
```

### REST API

```javascript
// 策略數據API
fetch('/api/strategies')
  .then((response) => response.json())
  .then((data) => console.log(data))
```

## 🚀 部署

### 靜態文件部署

直接將 `strategy-dashboard` 文件夾部署到Web服務器。

### Docker部署

```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🐛 常見問題

### Q: 頁面顯示空白？

A: 檢查瀏覽器控制台是否有JavaScript錯誤。

### Q: 樣式顯示異常？

A: 確保CSS文件路徑正確，檢查瀏覽器緩存。

### Q: WebSocket連接失敗？

A: 檢查後端服務是否運行在指定端口。

## 📝 更新日誌

### v1.0.0 (2025-12-11)

- ✅ 完成基礎頁面結構
- ✅ 實現響應式設計
- ✅ 添加基礎交互功能
- ✅ 準備API集成接口

## 🤝 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打開 Pull Request

## 📄 許可證

本項目採用 MIT 許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 📞 聯繫方式

- **項目維護**: CBSC Team
- **技術支持**: dev-team@cbsc.com
- **問題回報**: GitHub Issues

---

_最後更新: 2025-12-11_
