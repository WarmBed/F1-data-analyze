# F1T 工作區彈出邏輯說明

> **版本**: 1.0  
> **更新日期**: 2025-12-12  
> **相關檔案**: `f1t_gui_main.py`, `core/workspace_serializer.py`, `core/workspace_database.py`, `windows/save_workspace_dialog.py`, `windows/load_workspace_dialog.py`

---

## 1. 概述

F1T 工作區系統採用 **多文檔介面 (MDI)** 架構，支援：

1. **分頁彈出** - 將分頁彈出為獨立視窗
2. **工作區儲存** - 將當前 GUI 狀態序列化到資料庫
3. **工作區載入** - 從資料庫還原 GUI 狀態

---

## 2. 分頁彈出機制

### 2.1 核心類別

| 類別 | 檔案 | 說明 |
|-----|------|------|
| `PopoutSubWindow` | `f1t_gui_main.py:3434` | MDI 子視窗容器，支援彈出、調整大小 |
| `TabStandaloneWindow` | `f1t_gui_main.py:6396` | 分頁彈出的獨立視窗 |
| `ResizableStandaloneWindow` | `f1t_gui_main.py` | 可調整大小的獨立視窗基類 |

### 2.2 彈出流程 (`pop_out_tab`)

**位置**: `f1t_gui_main.py:12458`

```
用戶右鍵點擊分頁 → 選擇「彈出為獨立視窗」
         ↓
    pop_out_tab(tab_index)
         ↓
    ┌─────────────────────────────────┐
    │ 1. 檢查是否為 HOME 分頁 (禁止)   │
    │ 2. 檢查是否已經彈出 (禁止重複)   │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 3. 獲取分頁內容 (CustomMdiArea)  │
    │ 4. 創建佔位符 QWidget            │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 5. 創建 TabStandaloneWindow     │
    │    - 設置工具列（6 個按鈕）      │
    │    - 連接參數同步信號            │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 6. 關鍵操作：                    │
    │    - removeTab(tab_index)       │
    │    - insertTab(佔位符)           │
    │    - setCentralWidget(MDI區域)   │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 7. 更新分頁標籤                  │
    │    - 添加 🔗 圖標                │
    │    - 設置灰色文字                │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 8. 記錄到追蹤字典                │
    │    popped_out_tabs[tab_index]   │
    └─────────────────────────────────┘
```

### 2.3 返回流程 (`pop_back_in_tab`)

**位置**: `f1t_gui_main.py:12560`

```
用戶點擊工具列「⌂ 返回主畫面」
         ↓
    pop_back_in_tab(tab_index)
         ↓
    ┌─────────────────────────────────┐
    │ 1. 從追蹤字典獲取彈出資訊        │
    │ 2. 從字典移除 (防重複調用)       │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 3. takeCentralWidget()          │
    │    (避免關閉時刪除 MDI 區域)     │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 4. 移除佔位符                    │
    │ 5. 恢復 MDI 區域到分頁           │
    │ 6. 恢復標籤正常樣式              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 7. 關閉獨立視窗                  │
    │    (MDI 區域不會被刪除)          │
    └─────────────────────────────────┘
```

### 2.4 追蹤字典結構

```python
self.popped_out_tabs = {
    tab_index: {
        'standalone_window': TabStandaloneWindow,  # 獨立視窗實例
        'original_widget': CustomMdiArea,          # MDI 區域
        'placeholder': QWidget,                    # 佔位符
        'tab_name': str                            # 分頁名稱
    }
}
```

### 2.5 TabStandaloneWindow 工具列

| 按鈕 | 功能 | 說明 |
|-----|------|------|
| ⌂ 返回主畫面 | `_on_return_to_main()` | 返回分頁到主視窗 |
| 🔗 同步: ON/OFF | `toggle_sync()` | 切換參數同步狀態 |
| Show All Data | `show_all_data()` | 重置所有 XY 軸視圖 |
| Close All Windows | `close_all_windows()` | 關閉所有 MDI 子視窗 |
| Tile Windows | `tile_windows()` | 平鋪子視窗 |
| Cascade Windows | `cascade_windows()` | 層疊子視窗 |

---

## 3. 工作區序列化系統

### 3.1 核心類別

| 類別 | 檔案 | 說明 |
|-----|------|------|
| `WorkspaceSerializer` | `core/workspace_serializer.py` | GUI 狀態 ↔ JSON 轉換 |
| `WorkspaceDatabase` | `core/workspace_database.py` | SQLite 資料庫操作 |
| `SaveWorkspaceDialog` | `windows/save_workspace_dialog.py` | 儲存對話框 |
| `LoadWorkspaceDialog` | `windows/load_workspace_dialog.py` | 載入對話框 |

### 3.2 視窗類型映射

`WorkspaceSerializer.WINDOW_TYPE_MAPPING` 定義模組類別名稱到類型標識的映射：

```python
WINDOW_TYPE_MAPPING = {
    # 分析模組
    "RainAnalysisModuleAdapter": "rain_analysis",
    "TireAnalysisModuleAdapter": "tire_strategy",
    "TrackAnalysisUniversal": "track_analysis",
    "AccidentAnalysisModule": "accident_analysis",
    "PitstopAnalysisModule": "pitstop_analysis",
    
    # Lap Analysis 遙測模組
    "SpeedAnalysisModule": "speed",
    "BrakeAnalysisModule": "brake",
    "ThrottleAnalysisModule": "throttle",
    "RPMAnalysisModule": "rpm",
    "GearAnalysisModule": "gear",
    
    # Live Timing 模組
    "LiveTimingTrackMap": "live_track_map",
    "LiveTimingRankingTower": "live_ranking_tower",
    "LiveTimingPitWindow": "live_pit_window",
    "LiveTimingSpeedTrace": "live_speed_trace",
    "ChaseStrategyMDI": "live_chase_strategy",
    # ... 更多映射
}
```

### 3.3 序列化流程

```
serialize_workspace()
         ↓
    ┌─────────────────────────────────┐
    │ 1. 遍歷所有分頁（排除 HOME）     │
    └─────────────────────────────────┘
         ↓
    _serialize_tab(tab_index, tab_name)
         ↓
    ┌─────────────────────────────────┐
    │ 2. 檢查是否彈出（佔位符）        │
    │    - 彈出：從 popped_out_tabs 獲取│
    │    - 未彈出：直接獲取 MDI 區域   │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 3. 遍歷 MDI 子視窗               │
    │    - 獲取位置、大小              │
    │    - 提取參數（年份/賽事/賽段）  │
    │    - 識別視窗類型                │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ 4. 返回 JSON 配置                │
    └─────────────────────────────────┘
```

### 3.4 JSON 配置結構

```json
{
    "version": "1.0",
    "active_tab_index": 1,
    "tabs": [
        {
            "tab_index": 1,
            "tab_name": "Analysis",
            "is_popped_out": false,
            "mdi_windows": [
                {
                    "window_type": "rain_analysis",
                    "window_title": "Rain Analysis_2025_Japan_R",
                    "is_fixed": false,
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 800, "height": 600},
                    "display_order": 0,
                    "parameters": {
                        "year": 2025,
                        "race": "Japan",
                        "session": "R"
                    },
                    "data_file": null
                }
            ]
        },
        {
            "tab_index": 2,
            "tab_name": "Live Timing",
            "is_popped_out": true,
            "popped_window_geometry": {
                "x": 100,
                "y": 100,
                "width": 1200,
                "height": 800
            },
            "mdi_windows": [...]
        }
    ]
}
```

### 3.5 視窗類型識別策略

序列化時，按以下順序識別視窗類型：

1. **策略 1**: 檢查 `subwindow.analysis_module.analysis_type`
2. **策略 2**: 從 `widget()` 遞迴搜索 `analysis_type` 屬性
3. **策略 3**: 使用 `WINDOW_TYPE_MAPPING` 類別名稱映射

---

## 4. 資料庫結構

### 4.1 workspaces 表

```sql
CREATE TABLE workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP,
    active_tab_index INTEGER DEFAULT 0,
    config_json TEXT NOT NULL,
    total_tabs INTEGER DEFAULT 0,
    total_windows INTEGER DEFAULT 0,
    tags TEXT,
    version TEXT DEFAULT '1.0'
);
```

### 4.2 資料庫位置

```
workspaces/workspaces.db
```

---

## 5. 彈出視窗的參數同步

### 5.1 同步機制

```python
class TabStandaloneWindow:
    def __init__(self):
        self.sync_enabled = True  # 預設啟用
        
    def _connect_parameter_signals(self):
        # 連接主視窗的 ComboBox 變更信號
        self.main_window.year_combo.currentIndexChanged.connect(
            self._on_main_parameter_changed
        )
        self.main_window.race_combo.currentIndexChanged.connect(
            self._on_main_parameter_changed
        )
        self.main_window.session_combo.currentIndexChanged.connect(
            self._on_main_parameter_changed
        )
```

### 5.2 同步狀態切換

- **ON**: 主視窗參數變更時，彈出視窗內的模組同步更新
- **OFF**: 彈出視窗使用獨立參數，不受主視窗影響

---

## 6. PopoutSubWindow 詳解

### 6.1 初始化流程

```python
PopoutSubWindow(
    title="Rain Analysis_2025_Japan_R",
    parent_mdi=CustomMdiArea,
    analysis_module=RainAnalysisModuleAdapter,
    sync_enabled=True,
    parameter_provider=MainWindowParameterProvider
)
```

### 6.2 關鍵屬性

| 屬性 | 類型 | 說明 |
|-----|------|------|
| `parent_mdi` | CustomMdiArea | 父層 MDI 區域 |
| `analysis_module` | Module | 分析模組實例 |
| `content_widget` | QWidget | 原始內容 widget |
| `sync_enabled` | bool | 參數同步開關 |
| `_parameter_provider` | Provider | 參數提供者 |
| `local_year/race/session` | str | 本地參數（非同步模式） |

### 6.3 調整大小支援

```python
self.resize_margin = 3            # 視覺邊框寬度
self.resize_detection_margin = 10 # 可操作區域
self.resizing = False
self.resize_direction = None
```

---

## 7. 視覺反饋

### 7.1 分頁標籤狀態

| 狀態 | 標籤文字 | 文字顏色 |
|-----|---------|---------|
| 正常 | `Analysis` | 黑色 `#000000` |
| 已彈出 | `🔗 Analysis` | 灰色 `#666666` |

### 7.2 佔位符

彈出後，原分頁位置顯示佔位符：

```
┌─────────────────────────────────┐
│                                 │
│    「Analysis」分頁已彈出       │
│    為獨立視窗，點擊查看         │
│                                 │
└─────────────────────────────────┘
```

---

## 8. 錯誤處理

### 8.1 防重複彈出

```python
if tab_index in self.popped_out_tabs:
    logger.debug("Tab already popped out")
    return
```

### 8.2 防重複返回

```python
try:
    del self.popped_out_tabs[tab_index]  # 先移除
    # ... 執行返回操作
except KeyError:
    # 已返回，跳過（closeEvent 重複調用）
    pass
```

### 8.3 MDI 區域保護

```python
# 關鍵：先從獨立視窗取出 MDI 區域
standalone_window.takeCentralWidget()

# 然後才關閉視窗（不會刪除 MDI 區域）
standalone_window.close()
```

---

## 9. 相關信號

| 信號 | 來源 | 說明 |
|-----|------|------|
| `resized` | PopoutSubWindow | 視窗尺寸調整 |
| `window_closed` | PopoutSubWindow | 視窗關閉 |
| `workspace_saved` | SaveWorkspaceDialog | 工作區已儲存 |
| `workspace_selected` | LoadWorkspaceDialog | 工作區已選擇 |

---

## 10. 使用範例

### 10.1 程式化彈出分頁

```python
# 彈出第 2 個分頁
main_window.pop_out_tab(2)

# 返回分頁
main_window.pop_back_in_tab(2)
```

### 10.2 儲存工作區

```python
from core.workspace_serializer import WorkspaceSerializer
from core.workspace_database import WorkspaceDatabase

serializer = WorkspaceSerializer(main_window)
database = WorkspaceDatabase()

config = serializer.serialize_workspace()
database.save(name="My Workspace", config=config)
```

### 10.3 載入工作區

```python
config = database.load(workspace_id=1)
serializer.deserialize_workspace(config)
```

---

## 11. 注意事項

1. **HOME 分頁不可彈出** - 固定在主視窗
2. **彈出視窗關閉時自動返回** - closeEvent 觸發 `pop_back_in_tab`
3. **序列化時保留彈出狀態** - 可還原彈出視窗的位置和大小
4. **同步開關影響參數更新** - OFF 時使用本地參數
5. **視窗類型必須有映射** - 否則序列化為 `"unknown"`
