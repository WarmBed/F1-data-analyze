# Workspace Manager 功能開發計劃

## 📋 功能概述

**目標**：實現 Workspace 管理系統，允許用戶保存和載入整個工作區的狀態，包括所有分頁和 MDI 視窗的配置。

**核心價值**：
- 💾 保存當前分析進度
- 🔄 快速切換不同賽事分析
- 📊 管理多個分析項目

---

## ✅ 需求確認

### 記錄內容
- [x] 分頁名稱（Tab 1, Tab 2, ...）
- [x] 每個 MDI 視窗的類型（Tire Analysis, Rain Analysis, ...）
- [x] MDI 視窗的參數（年份、賽事、會話、車手）
- [x] MDI 視窗的位置和尺寸
- [x] MDI 視窗的排列方式（Tile/Cascade）
- [x] 當前選中的分頁
- [x] 獨立彈出的視窗狀態
- [ ] HOME 分頁（不記錄）

### 功能選擇
- **管理器方案**：方案 C（快速切換 + 完整管理器）
- **資料載入**：方案 A（參數重建，靈活可更新）
- **儲存格式**：SQLite 資料庫（支援多 Workspace 管理）
- **儲存位置**：`workspaces/` 資料夾
- **UI 入口**：主選單（File → Save/Load Workspace）
- **保存對話框**：詳細對話框（包含描述和統計）
- **載入行為**：完全替換（清空當前所有分頁）
- **載入確認**：Save & Load / Load / Cancel
- **資料不存在**：跳過 + 嘗試參數重建
- **名稱衝突**：覆蓋確認

---

## 🗄️ 資料庫結構

### 主表：workspaces
```sql
CREATE TABLE workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP,
    active_tab_index INTEGER DEFAULT 0,
    config_json TEXT NOT NULL,  -- 完整配置 JSON
    total_tabs INTEGER DEFAULT 0,
    total_windows INTEGER DEFAULT 0,
    tags TEXT,
    version TEXT DEFAULT '1.0'
);
```

### 元數據表：workspace_window_types
```sql
CREATE TABLE workspace_window_types (
    workspace_id INTEGER NOT NULL,
    window_type TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (workspace_id, window_type)
);
```

### 元數據表：workspace_parameters
```sql
CREATE TABLE workspace_parameters (
    workspace_id INTEGER NOT NULL,
    param_key TEXT NOT NULL,
    param_value TEXT NOT NULL,
    PRIMARY KEY (workspace_id, param_key, param_value)
);
```

**詳細結構**：請參考 `core/workspace_db_schema.sql`

---

## 📊 config_json 結構設計

```json
{
  "version": "1.0",
  "active_tab_index": 1,
  "tabs": [
    {
      "tab_index": 1,
      "tab_name": "Tab 1",
      "is_popped_out": false,
      "mdi_windows": [
        {
          "window_type": "tire_strategy",
          "window_title": "Tire Strategy Analysis_2025_United States_R (I)",
          "is_fixed": false,
          "position": {"x": 10, "y": 10},
          "size": {"width": 600, "height": 400},
          "display_order": 0,
          "parameters": {
            "year": 2025,
            "race": "United States",
            "session": "R",
            "driver": null
          },
          "data_file": "json/tire_strategy_2025_United_States_R_20251021.json"
        },
        {
          "window_type": "rain_analysis",
          "window_title": "Rain Analysis_2025_United States_R (I)",
          "is_fixed": false,
          "position": {"x": 620, "y": 10},
          "size": {"width": 600, "height": 400},
          "display_order": 1,
          "parameters": {
            "year": 2025,
            "race": "United States",
            "session": "R"
          }
        }
      ]
    },
    {
      "tab_index": 2,
      "tab_name": "Tab 2",
      "is_popped_out": true,
      "popped_window_geometry": {"x": 1920, "y": 0, "width": 1920, "height": 1080},
      "mdi_windows": [
        {
          "window_type": "track_analysis",
          "window_title": "Track Analysis_2025_United States_R (I)",
          "is_fixed": false,
          "position": {"x": 10, "y": 10},
          "size": {"width": 800, "height": 600},
          "display_order": 0,
          "parameters": {
            "year": 2025,
            "race": "United States",
            "session": "R"
          }
        }
      ]
    }
  ]
}
```

---

## 🎯 開發階段

### 階段 1：核心功能（MVP）🏃 當前階段

#### 1.1 資料庫管理器
- [ ] 創建 `WorkspaceDatabase` 類別 (`core/workspace_database.py`)
  - [ ] 初始化資料庫連接
  - [ ] 執行 schema 創建
  - [ ] CRUD 操作（Create, Read, Update, Delete）
  - [ ] 元數據管理（window_types, parameters）

#### 1.2 Workspace 序列化/反序列化
- [ ] 創建 `WorkspaceSerializer` 類別 (`core/workspace_serializer.py`)
  - [ ] `serialize_workspace()` - 從當前 GUI 狀態生成 JSON
  - [ ] `deserialize_workspace()` - 從 JSON 恢復 GUI 狀態
  - [ ] 視窗類型映射
  - [ ] 參數提取和注入

#### 1.3 保存功能
- [ ] 創建 `SaveWorkspaceDialog` (`windows/save_workspace_dialog.py`)
  - [ ] UI 設計（名稱、描述、統計資訊）
  - [ ] 名稱驗證
  - [ ] 衝突處理（覆蓋確認）
- [ ] 整合到主視窗
  - [ ] 主選單 File → Save Workspace (Ctrl+S)
  - [ ] 主選單 File → Save Workspace As... (Ctrl+Shift+S)
  - [ ] 收集當前狀態
  - [ ] 調用序列化器
  - [ ] 保存到資料庫

#### 1.4 載入功能
- [ ] 創建 `LoadWorkspaceDialog` (`windows/load_workspace_dialog.py`)
  - [ ] UI 設計（簡單列表模式）
  - [ ] 顯示基本資訊（名稱、修改時間、分頁數、視窗數）
  - [ ] 載入確認（Save & Load / Load / Cancel）
- [ ] 整合到主視窗
  - [ ] 主選單 File → Load Workspace (Ctrl+O)
  - [ ] 清空當前分頁（排除 HOME）
  - [ ] 調用反序列化器
  - [ ] 重建分頁和 MDI 視窗

#### 1.5 視窗重建邏輯
- [ ] 創建 `WindowFactory` (`core/window_factory.py`)
  - [ ] 視窗類型映射
  - [ ] 參數重建
  - [ ] 處理資料不存在情況
  - [ ] 錯誤處理和警告

---

### 階段 2：完善功能 🚶

#### 2.1 完整管理器
- [ ] 升級 `LoadWorkspaceDialog` 為完整管理器
  - [ ] 搜索功能（按名稱、描述、標籤）
  - [ ] 排序功能（修改時間、訪問時間、名稱）
  - [ ] 詳細資訊預覽
  - [ ] 重命名功能
  - [ ] 刪除功能
  - [ ] 克隆功能

#### 2.2 快速切換
- [ ] 主選單 File → Recent Workspaces
  - [ ] 顯示最近 10 個 Workspace
  - [ ] 點擊快速載入
  - [ ] 自動更新 `last_accessed_at`

#### 2.3 特殊情況處理
- [ ] 資料檔案不存在
  - [ ] 檢查 JSON 檔案
  - [ ] 嘗試參數重建（通過 API）
  - [ ] 顯示警告對話框
- [ ] 版本相容性
  - [ ] 檢查 `version` 欄位
  - [ ] 自動升級舊格式
  - [ ] 警告不相容版本

---

### 階段 3：進階功能 🎁

#### 3.1 自動保存
- [ ] 退出時自動保存
  - [ ] 保存為 `_autosave` Workspace
  - [ ] 啟動時檢查並恢復

#### 3.2 匯出/匯入
- [ ] 匯出 Workspace 為 JSON 檔案
- [ ] 從 JSON 檔案匯入 Workspace
- [ ] 分享給其他用戶

#### 3.3 標籤系統
- [ ] 添加/編輯標籤
- [ ] 按標籤過濾
- [ ] 標籤建議

#### 3.4 歷史版本
- [ ] 保留最近 N 個版本
- [ ] 版本比較
- [ ] 回滾到舊版本

---

## 🎨 UI 設計

### 主選單整合
```
File
  ├─ Save Workspace          (Ctrl+S)
  ├─ Save Workspace As...    (Ctrl+Shift+S)
  ├─ ─────────────────────
  ├─ Load Workspace...       (Ctrl+O)
  ├─ Manage Workspaces...    (Ctrl+Shift+M)
  ├─ ─────────────────────
  ├─ Recent Workspaces  ►
  │   ├─ 2025_USA_GP_Analysis
  │   ├─ 2025_Japan_GP
  │   ├─ Tire_Strategy_Research
  │   └─ [More...]
  ├─ ─────────────────────
  └─ Exit
```

### 保存對話框（詳細模式）
```
╔════════════════════════════════════════════╗
║ 💾 Save Workspace                          ║
╠════════════════════════════════════════════╣
║ Workspace Name: *                          ║
║ [2025_USA_GP_Analysis________________]     ║
║                                            ║
║ Description (Optional):                    ║
║ [完整分析包含輪胎策略、天氣和進站______]  ║
║                                            ║
║ 📊 將保存:                                 ║
║ • 3 個分頁 (Tab 1, Tab 2, Tab 3)          ║
║ • 8 個 MDI 視窗                            ║
║   - Tire Strategy Analysis (3)            ║
║   - Rain Analysis (2)                     ║
║   - Track Analysis (2)                    ║
║   - Accident Analysis (1)                 ║
║ • 當前選中分頁: Tab 1                      ║
║ • 彈出視窗: Tab 2                          ║
║                                            ║
║ 🏷️ 標籤 (Optional):                       ║
║ [2025, USA, 輪胎, 天氣________________]    ║
║                                            ║
║        [💾 Save] [❌ Cancel]               ║
╚════════════════════════════════════════════╝
```

### 載入確認對話框
```
╔══════════════════════════════════════════════╗
║ ⚠️ Load Workspace                            ║
╠══════════════════════════════════════════════╣
║ 載入 "2025_USA_GP_Analysis" 將清空當前所有  ║
║ 分頁和視窗。                                 ║
║                                              ║
║ 📊 目前狀態:                                 ║
║ • 4 個分頁                                   ║
║ • 10 個 MDI 視窗                             ║
║                                              ║
║ 📊 將載入:                                   ║
║ • 3 個分頁                                   ║
║ • 8 個 MDI 視窗                              ║
║                                              ║
║ 是否要先保存當前 Workspace？                 ║
║                                              ║
║  [💾 Save & Load] [📂 Load] [❌ Cancel]     ║
╚══════════════════════════════════════════════╝
```

### 管理器對話框（簡單列表 - 階段 1）
```
╔═══════════════════════════════════════════════════╗
║ 📋 Workspace Manager                              ║
╠═══════════════════════════════════════════════════╣
║ Name                   Modified      Tabs Windows ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║ 2025_USA_GP_Analysis   10-21 10:30    3     8    ║
║ 2025_Japan_GP          10-20 15:45    2     5    ║
║ Tire_Research          10-19 09:20    4    12    ║
║                                                   ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║ 📝 描述:                                          ║
║ 2025 USA GP 完整分析，包含輪胎策略、天氣影響     ║
║                                                   ║
║      [📂 Load] [🗑️ Delete] [❌ Close]            ║
╚═══════════════════════════════════════════════════╝
```

---

## 🧪 測試計劃

### 階段 1 測試
- [ ] 資料庫創建和初始化
- [ ] 保存簡單 Workspace（1 個分頁，2 個視窗）
- [ ] 載入 Workspace（驗證參數和位置）
- [ ] 保存複雜 Workspace（3 個分頁，8 個視窗，包含彈出視窗）
- [ ] 名稱衝突處理
- [ ] 載入確認流程

### 階段 2 測試
- [ ] 搜索功能
- [ ] 排序功能
- [ ] 刪除 Workspace
- [ ] Recent Workspaces 列表
- [ ] 資料檔案不存在處理

### 階段 3 測試
- [ ] 自動保存和恢復
- [ ] 匯出/匯入
- [ ] 標籤過濾

---

## 📝 開發檢查清單

### 階段 1（當前）
- [x] 創建資料庫 schema (`core/workspace_db_schema.sql`)
- [x] 創建開發任務文檔 (`tasks/workspace_manager_feature.md`)
- [ ] 實現 `WorkspaceDatabase` 類別
- [ ] 實現 `WorkspaceSerializer` 類別
- [ ] 實現 `SaveWorkspaceDialog`
- [ ] 實現 `LoadWorkspaceDialog`（簡單列表）
- [ ] 實現 `WindowFactory`
- [ ] 整合到主視窗選單
- [ ] 測試基本保存/載入

---

## 🚀 開發優先級

**第一優先**：階段 1 核心功能（預計 2-3 小時）
- 目標：實現基本的保存和載入功能
- 交付：能夠保存和恢復完整的 Workspace

**第二優先**：階段 2 完善功能（預計 1-2 小時）
- 目標：提升用戶體驗和管理能力
- 交付：完整的 Workspace 管理器

**第三優先**：階段 3 進階功能（預計 1-2 小時）
- 目標：自動化和分享功能
- 交付：生產就緒的 Workspace 系統

---

## 📌 注意事項

1. **API-ONLY 模式**：遵守專案的 API-ONLY 政策，不自動啟動 CLI 進程
2. **錯誤處理**：完善的錯誤處理和用戶提示
3. **日誌記錄**：詳細的日誌輸出，使用 `[WORKSPACE]` 前綴
4. **國際化**：所有用戶可見字串使用 `tr()` 函數
5. **測試驅動**：每個功能完成後立即測試

---

## 🎯 下一步行動

1. ✅ 確認需求和設計（已完成）
2. ⏭️ 實現 `WorkspaceDatabase` 類別
3. ⏭️ 實現 `WorkspaceSerializer` 類別
4. ⏭️ 實現保存/載入對話框
5. ⏭️ 整合到主視窗
6. ⏭️ 測試和迭代

---

**準備好開始開發了嗎？** 🚀
