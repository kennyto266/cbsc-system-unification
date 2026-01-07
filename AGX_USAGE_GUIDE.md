# AGX 使用指南

## 📋 項目概述

**agx** 是一個 AI 驅動的數據分析桌面應用程序，讓您通過現代化界面探索和查詢數據。

- **GitHub**: https://github.com/agnosticeng/agx
- **官方網站**: https://agx.app
- **許可證**: MIT
- **Stars**: 198+
- **Forks**: 10+

---

## 🏗️ 技術棧

### 核心技術
- **Tauri** - 原生桌面應用框架（Rust）
- **SvelteKit** - 前端框架
- **Plot** (D3.js) - 數據可視化
- **ClickHouse** - 數據庫引擎
- **Ollama** - 本地 LLM 集成

### 語言分佈
- **Svelte**: 63.1%
- **TypeScript**: 30.0%
- **Rust**: 2.2%
- **CSS**: 2.1%
- **Shell**: 1.1%
- **JavaScript**: 1.1%

---

## ✨ 核心功能

### 1. 交互式 SQL 查詢編輯器
- 語法高亮
- 自動完成
- 查詢歷史
- 多標籤支持

### 2. LLM 集成
- AI 輔助查詢生成
- 自然語言轉 SQL
- 智能建議

### 3. Schema 瀏覽器
- 探索數據結構
- 表和字段視圖
- 關係可視化

### 4. 結果展示
- 表格格式顯示
- 排序和篩選
- 導出功能

### 5. 文件操作
- 拖放文件導入
- 支持 CSV、JSON 等格式

### 6. 跨平台支持
- macOS
- Linux
- Windows

---

## 🚀 安裝和啟動

### 方式一：原生桌面應用

1. **下載最新版本**
   ```bash
   # 訪問 GitHub Releases
   https://github.com/agnosticeng/agx/releases
   ```

2. **安裝**
   - macOS: 下載 `.dmg` 文件
   - Windows: 下載 `.exe` 安裝程序
   - Linux: 下載 `.AppImage` 或 `.deb` 文件

3. **啟動應用**
   - 雙擊安裝的應用程序
   - 應用會自動啟動本地 ClickHouse 實例

### 方式二：在線使用

直接訪問：https://agx.app

### 方式三：Docker 本地部署

#### 1. 克隆倉庫

```bash
git clone https://github.com/agnosticeng/agx
cd agx
```

#### 2. 使用 Docker Compose 啟動

```bash
docker compose up
```

#### 3. 訪問應用

打開瀏覽器訪問：http://localhost:8080

---

## 🔧 Ollama 本地 LLM 集成

### 配置本地 Ollama 模型

要將本地 Ollama 模型與在線版本（https://agx.app）一起使用：

#### 1. 安裝 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# 或訪問 https://ollama.com 下載 Windows 版本
```

#### 2. 配置 CORS

啟動 Ollama 時允許來自 agx.app 的請求：

```bash
# Linux/macOS
OLLAMA_ORIGINS="https://app.agx" ollama serve

# Windows (PowerShell)
$env:OLLAMA_ORIGINS="https://app.agx"; ollama serve

# Windows (CMD)
set OLLAMA_ORIGINS=https://app.agx && ollama serve
```

#### 3. 下載模型

```bash
# 下載推薦的模型
ollama pull llama2
ollama pull codellama
ollama pull mistral
```

#### 4. 在 AGX 中使用

- 打開 https://agx.app
- 在設置中配置 Ollama 端點
- 開始使用 AI 輔助功能

---

## 📦 安裝 Agnostic UDF

安裝 Agnostic ClickHouse UDF（用戶定義函數）以啟用額外功能：

```bash
curl -fsSL https://raw.githubusercontent.com/agnosticeng/agx/main/scripts/install_agnostic_udfs.sh | sh
```

這將安裝額外的 ClickHouse 函數，增強數據處理能力。

---

## 💻 開發環境設置

### 前置要求

- **Node.js** (v16 或更高版本)
- **Rust toolchain**
- **Tauri 系統依賴

#### 安裝 Node.js
```bash
# 使用 nvm (推薦)
nvm install 18
nvm use 18

# 或從官網下載
# https://nodejs.org/
```

#### 安裝 Rust
```bash
# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Windows
# 下載 rustup-init.exe
# https://rustup.rs/
```

#### 安裝 Tauri 依賴

**macOS**:
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

**Windows**:
```bash
# 安裝 Microsoft C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### 項目結構

```
agx/
├── src/                 # 前端源代碼 (SvelteKit)
│   ├── lib/             # 共享組件
│   └── routes/          # 應用路由
├── src-tauri/           # 後端源代碼 (Rust)
│   ├── src/             # Rust 源文件
│   └── Cargo.toml       # Rust 依賴
├── package.json         # Node.js 依賴
├── svelte.config.js     # Svelte 配置
├── vite.config.js       # Vite 配置
└── tsconfig.json        # TypeScript 配置
```

### 開發流程

#### 1. 克隆並安裝依賴

```bash
git clone https://github.com/agnosticeng/agx
cd agx
npm install
```

#### 2. 開發模式運行

```bash
# 啟動開發服務器
npm run dev

# 或使用 Tauri 開發模式
npm run tauri dev
```

#### 3. 構建生產版本

```bash
# 使用構建腳本
./build.sh

# 或手動構建
npm run build
npm run tauri build
```

---

## 🎯 使用場景

### 1. 數據探索
```sql
-- 查看所有表
SHOW TABLES;

-- 查看表結構
DESCRIBE table_name;

-- 查詢數據
SELECT * FROM table_name LIMIT 100;
```

### 2. AI 輔助查詢
```
用戶: "顯示上個月的銷售額"
AGX: SELECT SUM(amount) FROM sales WHERE date >= now() - INTERVAL 1 MONTH
```

### 3. 數據可視化
- 創建圖表
- 生成報告
- 導出為 PDF/CSV

### 4. 文件分析
- 拖放 CSV 文件
- 自動檢測模式
- 即時查詢

---

## 🔍 常見問題

### Q: ClickHouse 連接失敗？
A: 確保 ClickHouse 服務正在運行：
```bash
# macOS/Linux
brew services start clickhouse  # macOS
sudo systemctl start clickhouse  # Linux

# Windows
# 使用 ClickHouse 安裝程序啟動服務
```

### Q: Ollama 模型無法連接？
A: 檢查 CORS 設置：
```bash
# 確認 OLLAMA_ORIGINS 已設置
echo $OLLAMA_ORIGINS

# 重啟 Ollama
OLLAMA_ORIGINS="https://app.agx" ollama serve
```

### Q: Docker 容器無法啟動？
A: 檢查端口占用：
```bash
# Windows
netstat -ano | findstr :8080

# macOS/Linux
lsof -i :8080

# 如果端口被占用，更改 docker-compose.yaml 中的端口映射
```

### Q: 性能問題？
A:
- 使用索引
- 優化 SQL 查詢
- 增加內存限制
- 使用數據分區

---

## 📚 進階功能

### 自定義 UDF
```sql
-- 創建自定義函數
CREATE FUNCTION my_function AS (x) -> x * 2;

-- 使用函數
SELECT my_function(column) FROM table;
```

### 數據導入
```sql
-- 從文件導入
INSERT INTO table FROM 'file.csv';

-- 從 URL 導入
INSERT INTO table FROM 'https://example.com/data.csv';
```

### 查詢優化
```sql
-- 使用 EXPLAIN 查看執行計劃
EXPLAIN SELECT * FROM table WHERE condition;

-- 使用 LIMIT 限制結果
SELECT * FROM table LIMIT 1000;
```

---

## 🤝 貢獻指南

### 提交流程

1. Fork 項目
2. 創建功能分支
   ```bash
   git checkout -b feature/my-feature
   ```
3. 提交更改
   ```bash
   git commit -m 'Add my feature'
   ```
4. 推送到分支
   ```bash
   git push origin feature/my-feature
   ```
5. 創建 Pull Request

### 代碼規範
- 遵循現有代碼風格
- 添加測試
- 更新文檔
- 確保構建通過

---

## 📖 相關資源

### 官方文檔
- **主頁**: https://agx.app
- **GitHub**: https://github.com/agnosticeng/agx
- **文檔**: 查看項目 README

### 技術文檔
- **Tauri**: https://tauri.app/
- **SvelteKit**: https://kit.svelte.dev/
- **ClickHouse**: https://clickhouse.com/docs/
- **Ollama**: https://ollama.com/

### 社區
- **GitHub Issues**: 報告問題和請求功能
- **Discussions**: 參與討論

---

## 📄 許可證

MIT License - 商業使用、修改、分發和私人使用均被允許。

---

*最後更新: 2026-01-07*
*版本: AGX 使用指南 v1.0*
