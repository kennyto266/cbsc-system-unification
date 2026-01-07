# Claude Canvas 使用指南

## 📋 概述

**Claude Canvas** 是一個強大的視覺設計 skill，用於創建博物館級別的設計哲學和藝術作品。

- **設計哲學** (.md) - 創建美學運動宣言
- **視覺作品** (.pdf/.png) - 將哲學表達為藝術

---

## 🚀 快速開始

### 1. 安裝插件（已完成）

```bash
/plugin marketplace add dvdsgl/claude-canvas
/plugin install canvas@claude-canvas
```

### 2. 使用 Skill

在 Claude Code 中：

```
使用 canvas-design skill 創建藝術作品
```

或直接告訴 Claude 您想要什麼類型的設計。

---

## 🎨 工作流程

### 第一步：設計哲學創建

Claude 會自動創建一個 **美學運動** 的哲學宣言，包括：

- **運動名稱**（1-2 個詞）
  - 例如："Brutalist Joy" / "Chromatic Silence" / "Metabolist Dreams"

- **哲學闡述**（4-6 段落）
  - 空間與形式
  - 顏色與材質
  - 比例與節奏
  - 構圖與平衡
  - 視覺層次

### 第二步：視覺表達

根據哲學創建藝術作品：

- **高度視覺化**（90% 設計，10% 文字）
- **極簡文字** - 僅作為視覺元素
- **專業工藝** - 看起來像數小時精心打磨的傑作
- **空間表達** - 通過形式、顏色、構圖傳達思想

---

## 📁 可用字體

Canvas 內置 **60+ 專業字體**，位於 `.claude/skills/canvas-design/canvas-fonts/`

### 無襯線字體
- **GeistMono** (Bold, Regular) - 現代等寬
- **InstrumentSans** (Bold, Italic, Regular) - 優雅無襯線
- **Outfit** (Bold, Regular) - 幾何現代
- **WorkSans** (Bold, Italic, Regular) - 實用無襯線

### 襯線字體
- **CrimsonPro** (Bold, Italic, Regular) - 優雅襯線
- **IBMPlexSerif** (Bold, Italic, Regular) - 專業襯線
- **Lora** (Bold, Italic, Regular) - 經典襯線
- **YoungSerif** (Regular) - 年輕襯線

### 等寬字體
- **JetBrainsMono** (Bold, Regular) - 代碼專用
- **IBMPlexMono** (Bold, Regular) - IBM 風格
- **RedHatMono** (Bold, Regular) - Red Hat 風格
- **DMMono** (Regular) - 設計師專用

### 展示字體
- **EricaOne** - 大膽展示
- **Gloock** - 強力襯線
- **Italiana** - 義式優雅
- **NationalPark** - 國家公園風格

### 特殊字體
- **BigShoulders** - 寬肩設計
- **Boldonse** - 粗體優雅
- **PixelifySans** - 像素風格
- **PoiretOne** - 藝術裝飾
- **Tektur** - 科技感
- **Jura** - 細膩現代
- **SmoochSans** - 柔和無襯線
- **Silkscreen** - 復古像素
- **NothingYouCouldDo** - 手寫風格

---

## 💡 使用技巧

### 1. 明確您的需求

告訴 Claude 您想要：
- 抽象藝術作品
- 特定風格（極簡、粗野主義、有機等）
- 色彩偏好
- 用途（海報、雜誌、藝術品等）

### 2. 信任 AI 的創意

Canvas 的核心是 **創造詮釋空間**：
- 給出概念方向
- 讓 AI 創建獨特的哲學
- AI 會將其視覺化

### 3. 關注工藝細節

最終作品會體現：
- ✅ 精確的對齊和間距
- ✅ 和諧的色彩搭配
- ✅ 大量負空間
- ✅ 極簡的文字使用
- ✅ 博物館級別的品質

---

## 🎯 示例提示

### 抽象極簡
```
創建一個極簡主義的抽象藝術作品，
強調負空間和幾何精度
```

### 有機自然
```
創作一個受自然啟發的有機設計，
使用曲線和自然色彩
```

### 科技數據
```
創建一個數據可視化的抽象作品，
體現算法和數學之美
```

### 粗野主義
```
創作粗野主義風格的海報，
大膽的幾何形式和強烈對比
```

---

## 📦 輸出格式

### 文件類型
- `.pdf` - 適合打印和分享
- `.png` - 適合網絡和數字展示

### 文件結構
```
project/
├── philosophy-name.md          # 設計哲學
└── philosophy-name.pdf         # 視覺作品
```

---

## ⚙️ 進階選項

### 多頁作品

請求創建多個頁面：
```
創建一個 3 頁的作品集，
每頁都是同一哲學的不同詮釋
```

### 特定主題

結合您的項目：
```
為我的量化交易項目創建
一個算法美學的視覺作品
```

---

## 🎓 設計原則回顧

### 核心原則
1. **視覺優先** - 90% 設計，10% 文字
2. **工藝極致** - 數小時精細打磨的品質
3. **空間為王** - 大量負空間創造呼吸感
4. **極簡文字** - 文字作為視覺元素，非說明
5. **創造性詮釋** - 留給 AI 創作空間

### 質量標準
- ✅ 博物館展示級別
- ✅ 專業設計師水準
- ✅ 完美的技術執行
- ✅ 獨特的美學聲音

---

## 📚 參考資源

- **GitHub**: https://github.com/dvdsgl/claude-canvas
- **本地字體目錄**: `.claude/skills/canvas-design/canvas-fonts/`
- **Skill 文件**: `.claude/skills/canvas-design/SKILL.md`

---

*最後更新: 2026-01-07*
*版本: Claude Canvas v1.0*
