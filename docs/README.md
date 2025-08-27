# F1T-LOCAL-V13 文檔總覽

## 📁 文檔架構

本文檔系統採用標準化分類管理，所有開發相關文檔統一存放於 `docs/` 目錄：

### 🗂️ 目錄結構
```
docs/
├── module_documentation/           # 模組說明文檔
│   ├── gui_components/            # GUI 元件文檔
│   │   └── UniversalChartWidget_技術文檔.md
│   ├── core_modules/              # 核心模組說明
│   ├── analysis_engines/          # 分析引擎文檔
│   └── utility_functions/         # 工具函數文檔
├── development_tracking/          # 開發追蹤文檔
├── api_documentation/             # API 相關文檔
├── user_guides/                   # 用戶指南
├── technical_specifications/      # 技術規範文檔
└── changelog/                     # 變更日誌
```

## 📚 現有文檔清單

### GUI 組件文檔
- **[UniversalChartWidget 技術文檔](module_documentation/gui_components/UniversalChartWidget_技術文檔.md)**
  - 完整的通用圖表組件技術規範
  - 包含API、信號流程、使用範例
  - 雙Y軸、互動操作、JSON載入等功能說明

### 技術架構文檔
- **[降雨分析架構與數據流程](technical_specifications/architecture_rain_analysis_dataflow.md)**
  - 降雨分析完整技術流程
  - 從用戶點擊到通用視窗顯示的完整數據流
  - 包含緩存機制、異步處理、數據轉換等核心技術

## 🎯 文檔使用指南

### 開發者
- 查看 `module_documentation/` 了解具體模組功能
- 參考 `technical_specifications/` 了解系統架構
- 使用 `development_tracking/` 追蹤開發進度

### 使用者
- 閱讀 `user_guides/` 學習系統使用方法
- 查看 `changelog/` 了解版本更新內容

### API 開發者
- 參考 `api_documentation/` 了解接口規範
- 查看模組文檔了解內部實現細節

## 📝 文檔建立原則

1. **標準化命名**: 使用統一的命名格式 `[模組名稱]_[文檔類型].md`
2. **完整性要求**: 每個文檔必須包含功能、API、範例、注意事項
3. **即時更新**: 代碼變更後同步更新相關文檔
4. **交叉引用**: 建立文檔間的連結關係
5. **版本控制**: 記錄文檔的更新歷史和版本信息

## 🔗 快速導航

- [UniversalChartWidget 技術文檔](module_documentation/gui_components/UniversalChartWidget_技術文檔.md) - 通用圖表組件完整說明
- [系統主要 README](../README.md) - 專案總覽
- [專業工程手冊](../F1T_PROFESSIONAL_ENGINEERING_MANUAL.md) - 開發指導原則

---
*F1T-LOCAL-V13 文檔管理系統 - 版本 1.0.0*
