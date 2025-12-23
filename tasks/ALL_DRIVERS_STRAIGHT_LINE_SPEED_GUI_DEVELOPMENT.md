# 全車手直線速度分析 GUI 模組開發任務
**功能編號**: F48 Enhancement  
**開發日期**: 2025-10-14  
**開發人員**: AI Programming Assistant  
**參考模組**: ideal_lap_sector_comparison

---

## 📋 反幻覺編碼四原則檢查

### ✅ 原則 0：宣告四原則
- [x] 不懂就問
- [x] 確認需求才實作
- [x] 先驗證後編碼
- [x] 複用現有功能

### ✅ 原則 1：禁止幻覺編碼
- [x] 已用 `semantic_search` 搜索 ideal_lap_sector_comparison
- [x] 已用 `file_search` 檢查 modules/gui/ideal_lap_analysis/
- [x] 已用 `grep_search` 驗證 UniversalDataLoader 存在
- [x] 已閱讀參考模組的完整實現

### ✅ 原則 2：模組資料夾優先
- [x] 已檢查 modules/gui/lap_analysis/speed_analysis/
- [x] 發現 `straight_line_speed_loader.py` 已存在
- [x] 確認可以複用 StraightLineSpeedDataLoader
- [x] 不需要重複開發資料載入器

### ✅ 原則 3：通用模組優先
- [x] 確認使用 `UniversalDataLoader` 作為基礎類別
- [x] 確認使用 `UniversalAnalysisMDI` 管理 MDI 視窗
- [x] 參考 `ideal_lap_sector_comparison` 作為架構範本
- [x] 遵循 API-ONLY 模式政策

---

## 🎯 開發目標

### 主要目標
創建一個專業的 GUI 模組，用於顯示全車手的：
1. **最高速度排名**（垂直長條圖）
2. **100-300km/h 加速性能**（水平長條圖）

### 參考賽事數據
- **2024 Japan Q** (已生成 JSON)
- **2024 Monza Q** (需生成)
- **2024 Monaco Q** (需生成)
- 額外測試：正賽 (R) 數據

### 設計規格
- **架構模式**: UniversalAnalysisMDI + UniversalDataLoader
- **參考模組**: ideal_lap_sector_comparison
- **圖表類型**: 
  - 水平長條圖（加速性能，Y 軸車手，X 軸時間）
  - 垂直長條圖（最高速度，X 軸車手，Y 軸速度）
- **資料來源**: Function 48 JSON 輸出 + API

---

## 📂 模組結構

```
modules/gui/all_drivers_straight_line_speed_analysis/
├── __init__.py                                          # 模組導出
├── all_drivers_straight_line_speed_module.py            # IAnalysisModule 實現
├── all_drivers_straight_line_speed_mdi.py               # UniversalAnalysisMDI 實現
├── all_drivers_straight_line_speed_data_loader.py       # UniversalDataLoader 實現
├── all_drivers_straight_line_speed_widget.py            # 圖表 Widget 實現
├── register_module.py                                   # 模組註冊
├── demo_japan_q.py                                      # Demo 1: 日本站排位賽
├── demo_monza_q.py                                      # Demo 2: 蒙札站排位賽
├── demo_monaco_q.py                                     # Demo 3: 摩納哥站排位賽
├── demo_japan_r.py                                      # Demo 4: 日本站正賽
└── demo_integration_test.py                             # Demo 5: 整合測試
```

---

## 📊 JSON 數據結構 (Function 48)

### 輸入 JSON 結構
```json
{
  "success": true,
  "function_id": "48",
  "message": "全部車手直線速度與加速性能分析完成",
  "data": {
    "metadata": {
      "year": 2024,
      "race": "Japan",
      "session": "Q",
      "analysis_type": "enhanced_straight_line_speed_with_acceleration",
      "drivers_total": 20
    },
    "driver_speeds": [
      {
        "driver": "HUL",
        "team": "Haas F1 Team",
        "max_speed_kmh": 328.0,
        "acceleration_100_300": {
          "time_seconds": 1.2,
          "distance_meters": 97.99,
          "avg_acceleration_ms2": 46.3
        }
      }
    ],
    "summary": {
      "fastest_driver": "HUL",
      "fastest_speed_kmh": 328.0,
      "acceleration_performance": {
        "fastest_acceleration_driver": "HUL",
        "fastest_acceleration_time": 1.2,
        "average_acceleration_time": 1.746
      }
    },
    "chart_data": {
      "speed_chart": {
        "type": "bar",
        "x": ["HUL", "MAG", ...],
        "values": [328.0, 328.0, ...],
        "unit": "km/h"
      },
      "acceleration_chart": {
        "type": "horizontal_bar",
        "y": ["HUL", "PIA", ...],
        "values": [1.2, 1.441, ...],
        "unit": "秒",
        "max_speeds": [328.0, 319.0, ...]
      }
    }
  }
}
```

---

## 🛠️ 實作步驟

### Phase 1: 資料載入器實作 ✅
**檔案**: `all_drivers_straight_line_speed_data_loader.py`

**狀態**: 可複用現有的 `StraightLineSpeedDataLoader`

**發現**: modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py 已存在完整實現
- ✅ 支援 Function 48
- ✅ API-ONLY 模式
- ✅ JSON 檔案搜尋
- ✅ 資料驗證和轉換

**決策**: 直接使用現有的 `StraightLineSpeedDataLoader`，不需要重新實現

---

### Phase 2: Widget 圖表實作 🔄
**檔案**: `all_drivers_straight_line_speed_widget.py`

**功能需求**:
1. 繪製水平長條圖（加速性能）
2. 繪製垂直長條圖（最高速度）
3. 支援圖表切換
4. 支援資料高亮顯示
5. 支援匯出功能

**參考實現**: `ideal_lap_sector_comparison_widget.py`

**關鍵方法**:
- `__init__()`: 初始化 matplotlib 畫布
- `draw_acceleration_chart()`: 繪製加速圖表
- `draw_speed_chart()`: 繪製速度圖表
- `switch_chart()`: 切換圖表類型
- `export_chart()`: 匯出圖表

---

### Phase 3: MDI 視窗實作 🔄
**檔案**: `all_drivers_straight_line_speed_mdi.py`

**繼承**: `UniversalAnalysisMDI`

**關鍵方法**:
```python
class AllDriversStraightLineSpeedMDI(UniversalAnalysisMDI):
    def __init__(self, year, race, session, parent=None):
        config = {
            "window_title": f"全車手直線速度分析 - {year} {race} {session}",
            "analysis_type": "straight_line_speed",
            "default_size": (1200, 800),
            "module_type": "all_drivers_speed"
        }
        super().__init__(year, race, session, parent, **config)
        self._init_ui()
        self.load_initial_data()
    
    def _create_data_loader(self):
        # 使用現有的 StraightLineSpeedDataLoader
        from modules.gui.lap_analysis.speed_analysis.straight_line_speed_loader import (
            StraightLineSpeedDataLoader
        )
        return StraightLineSpeedDataLoader(parent=self)
    
    def _create_chart_widget(self):
        return AllDriversStraightLineSpeedWidget(parent=self)
    
    def _on_data_loaded(self, data):
        # 更新統計面板
        self._update_stats_panel(data)
        # 更新圖表
        self.chart_widget.draw_acceleration_chart(data["chart_data"]["acceleration_chart"])
```

**UI 組件**:
- 統計面板（最快車手、平均速度、加速性能）
- 圖表切換按鈕
- 圖表匯出按鈕
- 控制面板（排序、高亮、篩選）

---

### Phase 4: 模組介面實作 🔄
**檔案**: `all_drivers_straight_line_speed_module.py`

**實現 IAnalysisModule 介面**:
```python
class AllDriversStraightLineSpeedModule(IAnalysisModule):
    @property
    def module_name(self) -> str:
        return "AllDriversStraightLineSpeed"
    
    @property
    def display_name(self) -> str:
        return "全車手直線速度與加速性能分析"
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        # 初始化 MDI 視窗
        pass
    
    def get_widget(self) -> Optional[QWidget]:
        # 返回主要 Widget
        pass
```

---

### Phase 5: Demo 測試實作 🔄
**檔案**: `demo_*.py`

#### Demo 1: `demo_japan_q.py`
```python
# 測試 2024 日本站排位賽（已有 JSON）
year = 2024
race = "Japan"
session = "Q"
```

#### Demo 2: `demo_monza_q.py`
```python
# 測試 2024 蒙札站排位賽（需生成 JSON）
year = 2024
race = "Italy"  # Monza
session = "Q"
```

#### Demo 3: `demo_monaco_q.py`
```python
# 測試 2024 摩納哥站排位賽（需生成 JSON）
year = 2024
race = "Monaco"
session = "Q"
```

#### Demo 4: `demo_japan_r.py`
```python
# 測試 2024 日本站正賽
year = 2024
race = "Japan"
session = "R"
```

#### Demo 5: `demo_integration_test.py`
```python
# 整合測試：測試所有 Demo
# 驗證：Import、MDI、資料載入、圖表繪製
```

---

## ✅ 測試計畫

### 階段 1: Import 測試
```python
# 測試所有模組是否可以正常 import
from modules.gui.all_drivers_straight_line_speed_analysis import (
    AllDriversStraightLineSpeedModule,
    AllDriversStraightLineSpeedMDI,
    AllDriversStraightLineSpeedWidget
)
```

### 階段 2: 資料載入測試
```python
# 測試資料載入器
loader = StraightLineSpeedDataLoader()
success = loader.load_data(year=2024, race="Japan", session="Q")
assert success, "資料載入失敗"
```

### 階段 3: Widget 測試
```python
# 測試圖表繪製
widget = AllDriversStraightLineSpeedWidget()
widget.draw_acceleration_chart(chart_data)
widget.draw_speed_chart(chart_data)
```

### 階段 4: MDI 測試
```python
# 測試 MDI 視窗
mdi = AllDriversStraightLineSpeedMDI(2024, "Japan", "Q")
mdi.show()
```

### 階段 5: 整合測試
```python
# 測試完整流程
app = QApplication(sys.argv)
module = AllDriversStraightLineSpeedModule()
module.initialize_module()
widget = module.get_widget()
widget.show()
app.exec_()
```

---

## 📊 預期輸出

### 水平長條圖（加速性能）
```
最快在頂端：
HUL    ████████████████ 1.20s (328 km/h)
PIA    ████████████████████ 1.44s (319 km/h)
MAG    █████████████████████ 1.48s (328 km/h)
...
ZHO    ████████████████████████████████ 2.28s (321 km/h)
```

### 垂直長條圖（最高速度）
```
330 ┤
320 ┤ █ █
310 ┤ █ █ █ █
300 ┤ █ █ █ █ █ █
    └─────────────────
     H M V P A A ...
     U A E R L L
     L G R   O B
```

---

## 🔧 技術細節

### 使用的技術棧
- **PyQt5**: GUI 框架
- **Matplotlib**: 圖表繪製
- **UniversalDataLoader**: 資料載入基類
- **UniversalAnalysisMDI**: MDI 視窗基類
- **StraightLineSpeedDataLoader**: Function 48 專用載入器

### API 整合
- **API 端點**: `POST /api/v2/analysis/execute?function_id=48`
- **回退模式**: 本地 JSON 檔案 (`json/all_drivers_straight_line_speed_*.json`)
- **API-ONLY 模式**: 禁止 GUI 自動啟動 CLI

### 資料流
```
GUI 請求 → StraightLineSpeedDataLoader → API (優先) / 本地 JSON (備援)
         ↓
    AllDriversStraightLineSpeedMDI → _on_data_loaded()
         ↓
    AllDriversStraightLineSpeedWidget → draw_acceleration_chart() / draw_speed_chart()
```

---

## 🎨 UI/UX 設計

### 視窗佈局
```
┌─────────────────────────────────────────────┐
│ 全車手直線速度與加速性能分析 - 2024 Japan Q  │
├─────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────┐ │
│ │ 統計面板        │ │ 控制面板            │ │
│ │ 最快車手: HUL   │ │ [圖表切換▼]         │ │
│ │ 最高速度: 328   │ │ [匯出圖表]          │ │
│ │ 最快加速: 1.20s │ │ [排序選項]          │ │
│ └─────────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │                                         │ │
│ │       圖表區域 (Matplotlib Canvas)      │ │
│ │                                         │ │
│ │     水平長條圖 / 垂直長條圖切換顯示     │ │
│ │                                         │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 顏色主題
- **最快車手**: 綠色高亮
- **前三名**: 漸層綠色
- **中段**: 藍色
- **後段**: 灰色
- **車隊顏色**: 可選（根據 Team 資料）

---

## 🐛 已知問題和解決方案

### 問題 1: 低速賽道無法達到 300km/h
**解決方案**: 
- 在資料驗證時檢查 `acceleration_100_300` 是否為 None
- 顯示 "N/A" 或空白
- 統計摘要中排除無效數據

### 問題 2: 圖表標籤重疊
**解決方案**:
- 使用 `plt.tight_layout()`
- 調整字體大小
- 旋轉 X 軸標籤

### 問題 3: 中文字體顯示
**解決方案**:
```python
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
```

---

## 📝 開發檢查清單

### 開發前檢查 (反幻覺編碼)
- [x] ✅ 用 semantic_search 搜索相關功能
- [x] ✅ 用 file_search 檢查 modules/gui/
- [x] ✅ 用 grep_search 驗證方法存在
- [x] ✅ 閱讀參考實現的完整代碼
- [x] ✅ 確認使用通用架構

### 實作檢查
- [ ] 創建模組資料夾結構
- [ ] 實現 DataLoader 類別
- [ ] 實現 Widget 圖表類別
- [ ] 實現 MDI 視窗類別
- [ ] 實現 Module 介面類別
- [ ] 創建 Demo 測試檔案

### 測試檢查
- [ ] Import 測試通過
- [ ] 方法驗證通過
- [ ] MDI 初始化測試通過
- [ ] GUI 啟動無錯誤
- [ ] API 調用成功
- [ ] 圖表正常繪製
- [ ] 無 AttributeError
- [ ] 無 TypeError

### 整合檢查
- [ ] 註冊到主 GUI 選單
- [ ] 多個 Demo 測試通過
- [ ] 文檔更新完成

---

## 🚀 下一步

1. **立即執行**: 創建模組資料夾結構
2. **實現順序**: DataLoader → Widget → MDI → Module → Demo
3. **測試策略**: 每個階段完成後立即測試
4. **文檔更新**: 完成後更新主 README

---

**任務創建時間**: 2025-10-14  
**預計完成時間**: 2025-10-14  
**實際完成時間**: [待完成]  
**狀態**: 🔄 進行中
