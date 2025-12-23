# Throttle Line Chart 多車手模式改造任務

**創建日期**: 2025-10-08  
**目標**: 將 Throttle Line Chart 改造成類似 Detailed Lap Analysis 的多車手選擇模式  
**參考模組**: Detailed Lap Analysis (`modules/gui/driver_race/detailed_lap_analysis/`)

---

## 📋 需求概述

### 用戶需求
> "我期望他的折線圖將與 detailed lap analysis 一樣的 UI 一樣的邏輯（選擇 5 個車手）等..."

### 核心功能
1. ✅ **多車手選擇**: 支援同時選擇最多 5 個車手
2. ✅ **折線圖顯示**: 每個車手顯示為一條獨立的折線
3. ✅ **顏色區分**: 使用 5 種不同顏色區分車手
4. ✅ **圖例系統**: 顯示車手名稱和對應顏色
5. ✅ **數據對比**: 同時顯示多個車手的油門數據

---

## 🔍 架構分析

### Detailed Lap Analysis 架構 (參考模板)

```
driverLapAnalysisDataManager (UniversalDataLoader)
├─ 支援 API Function 28
├─ 車手選擇邏輯
└─ 多車手數據載入

LaptimeChartWidget (QWidget)
├─ paintEvent() 繪製圖表
├─ ChartSeries 數據系列
├─ ChartTheme 顏色主題
│  ├─ DRIVER1_COLOR = 紅色 (220, 53, 69)
│  ├─ DRIVER2_COLOR = 藍色 (0, 123, 255)
│  ├─ DRIVER3_COLOR = 綠色 (40, 167, 69)
│  ├─ DRIVER4_COLOR = 黃色 (255, 193, 7)
│  └─ DRIVER5_COLOR = 灰色 (108, 117, 125)
└─ 圖例、Tooltip、固定點功能

控制面板
├─ 5 個車手選擇 QComboBox
├─ 顯示選項 (圖例、網格等)
└─ 載入按鈕
```

### Throttle Line Chart 當前架構

```
ThrottleLineChartMDI (UniversalAnalysisMDI)
├─ create_data_manager() → ThrottleLineChartDataLoader
├─ create_chart_widget() → ThrottleDurationChartWidget (單車手)
└─ create_control_widget() → 單車手控制面板

ThrottleLineChartDataLoader (UniversalDataLoader)
├─ 使用 CLI Function 54
└─ 單車手數據載入
```

---

## 🎯 改造計劃

### Phase 1: 數據層改造 ⏳

**檔案**: `throttle_line_chart_data_loader.py`

**任務清單**:
- [ ] 1.1 添加多車手支援
  - [ ] 添加 `selected_drivers: List[str]` 屬性（最多 5 個）
  - [ ] 修改 `load_data()` 支援批次載入多個車手
  - [ ] 每個車手獨立調用 CLI Function 54

- [ ] 1.2 數據結構調整
  - [ ] 原: `driver_data = {...}` (單車手)
  - [ ] 新: `multi_driver_data = {driver_code: {...}, ...}` (多車手)
  - [ ] 添加 `get_driver_throttle_data(driver_code)` 方法

- [ ] 1.3 API 整合
  - [ ] 支援 API 批次請求（如果有 API 支援）
  - [ ] 或者循環調用單車手 API

**預計時間**: 2-3 小時

---

### Phase 2: 圖表組件創建 ⏳

**新檔案**: `throttle_multi_driver_chart_widget.py`

**任務清單**:
- [ ] 2.1 創建基礎圖表組件
  ```python
  class ThrottleChartTheme:
      DRIVER1_COLOR = QColor(220, 53, 69)    # 紅色
      DRIVER2_COLOR = QColor(0, 123, 255)    # 藍色
      DRIVER3_COLOR = QColor(40, 167, 69)    # 綠色
      DRIVER4_COLOR = QColor(255, 193, 7)    # 黃色
      DRIVER5_COLOR = QColor(108, 117, 125)  # 灰色
  
  class ThrottleChartWidget(QWidget):
      def __init__(self, parent=None):
          # 圖表系列列表
          self.series_list = []  # List[ChartSeries]
      
      def update_series_data(self, series_list):
          # 更新多車手數據
          pass
      
      def paintEvent(self, event):
          # 繪製多條折線
          pass
  ```

- [ ] 2.2 繪製邏輯實現
  - [ ] X 軸: 圈數 (Lap Number)
  - [ ] Y 軸: 油門全開秒數 (Full Throttle Duration)
  - [ ] 多條折線，每條不同顏色
  - [ ] 網格線、刻度標籤

- [ ] 2.3 圖例系統
  - [ ] 繪製圖例（車手名稱 + 顏色方塊）
  - [ ] 支援拖移圖例位置
  - [ ] 點擊圖例切換顯示/隱藏

- [ ] 2.4 交互功能
  - [ ] Hover 顯示 Tooltip（圈數 + 油門秒數）
  - [ ] 左鍵點擊固定 Tooltip（最多 2 個）
  - [ ] 右鍵清除所有固定點

**參考**: `driverlap_analysis_chart_widget.py` 的 `LaptimeChartWidget` 類

**預計時間**: 4-5 小時

---

### Phase 3: 控制面板改造 ⏳

**檔案**: `throttle_line_chart_mdi.py` - `_create_control_widget()` 方法

**任務清單**:
- [ ] 3.1 多車手選擇 UI
  ```python
  # 車手選擇群組
  driver_group = QGroupBox("Select Drivers (Max 5)")
  driver_layout = QVBoxLayout()
  
  self.driver_combos = []  # 5 個 QComboBox
  for i in range(5):
      combo = QComboBox()
      combo.addItem(f"Driver {i+1}: None")
      combo.addItems(available_drivers)
      driver_layout.addWidget(combo)
      self.driver_combos.append(combo)
  ```

- [ ] 3.2 載入按鈕邏輯
  - [ ] 收集選中的車手（最多 5 個）
  - [ ] 調用數據載入器載入多車手數據
  - [ ] 更新圖表顯示

- [ ] 3.3 顯示選項
  - [ ] ☑ 顯示圖例
  - [ ] ☑ 顯示網格
  - [ ] ☑ 顯示數據點

**預計時間**: 1-2 小時

---

### Phase 4: MDI 容器整合 ⏳

**檔案**: `throttle_line_chart_mdi.py`

**任務清單**:
- [ ] 4.1 修改 `create_chart_widget()`
  ```python
  def create_chart_widget(self):
      from .throttle_multi_driver_chart_widget import ThrottleChartWidget
      return ThrottleChartWidget(self)
  ```

- [ ] 4.2 修改 `create_control_widget()`
  - [ ] 返回新的多車手控制面板

- [ ] 4.3 添加車手列表獲取
  ```python
  def get_available_drivers(self):
      # 從 FastF1 或 API 獲取當前賽事的車手列表
      pass
  ```

- [ ] 4.4 數據載入邏輯
  ```python
  def load_multi_driver_data(self):
      selected_drivers = self.get_selected_drivers()
      self.data_manager.load_data(
          year=self.year,
          race=self.race,
          session=self.session,
          drivers=selected_drivers  # 多車手
      )
  ```

**預計時間**: 2 小時

---

### Phase 5: 測試與優化 ⏳

**任務清單**:
- [ ] 5.1 單元測試
  - [ ] 測試多車手數據載入
  - [ ] 測試圖表繪製正確性
  - [ ] 測試顏色分配邏輯

- [ ] 5.2 整合測試
  - [ ] 在 GUI 中打開模組
  - [ ] 選擇 1-5 個車手
  - [ ] 驗證圖表正確顯示
  - [ ] 測試交互功能（Hover, 固定點）

- [ ] 5.3 性能優化
  - [ ] 優化多車手數據載入速度
  - [ ] 優化圖表繪製性能

- [ ] 5.4 錯誤處理
  - [ ] 處理車手數據缺失
  - [ ] 處理 API 錯誤
  - [ ] 添加用戶友好的錯誤提示

**預計時間**: 2-3 小時

---

## 📁 檔案結構

### 新增檔案
```
modules/gui/Throttle_analysis/throttle_line_chart_analysis/
├─ throttle_multi_driver_chart_widget.py  (新增)
└─ throttle_chart_theme.py                (新增，可選)
```

### 修改檔案
```
modules/gui/Throttle_analysis/throttle_line_chart_analysis/
├─ throttle_line_chart_mdi.py             (修改)
├─ throttle_line_chart_data_loader.py     (修改)
└─ throttle_line_chart_module.py          (可能需要微調)
```

---

## 🎨 UI 設計草圖

```
┌──────────────────────────────────────────────────────────┐
│ 🏎️ 油門分析折線圖 - 2025 Japan R                          │
├──────────────────────────────────────────────────────────┤
│ ┌─ Select Drivers (Max 5) ─────────────────────────┐    │
│ │ Driver 1: [▼ VER - Max Verstappen    ]           │    │
│ │ Driver 2: [▼ LEC - Charles Leclerc   ]           │    │
│ │ Driver 3: [▼ HAM - Lewis Hamilton    ]           │    │
│ │ Driver 4: [▼ None                    ]           │    │
│ │ Driver 5: [▼ None                    ]           │    │
│ └──────────────────────────────────────────────────┘    │
│                                                          │
│ ┌─ Display Options ─────────────────────────────────┐   │
│ │ ☑ Show Legend    ☑ Show Grid    ☑ Show Points   │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ [ 📊 Load Data and Display Chart ]                      │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ Chart Area:                                              │
│   Full Throttle Duration (s) │                          │
│   10 ┼──────────────────────────────────────           │
│      │  ──VER (紅)                                       │
│    8 ┼    ╲╱                                            │
│      │     ╲  ──LEC (藍)                                │
│    6 ┼      ╲╱╲                                         │
│      │       ╲  ──HAM (綠)                              │
│    4 ┼        ╲╱                                        │
│      │                                                  │
│    2 ┼──────────────────────────────────────           │
│      └────────────────────────────────────→            │
│      1    5    10   15   20   25   30  Lap             │
│                                                          │
│   Legend: ■ VER  ■ LEC  ■ HAM                           │
└──────────────────────────────────────────────────────────┘
```

---

## ⚠️ 注意事項

### 向後兼容
- 考慮保留單車手模式作為備選
- 或者創建 `throttle_line_chart_v2` 作為新版本

### API 限制
- CLI Function 54 是單車手的
- 需要循環調用或創建新的批次 API

### 性能考量
- 5 個車手 × 每場比賽 50-70 圈 = 250-350 個數據點
- 需要優化繪製邏輯避免卡頓

---

## 📅 時間估算

| Phase | 任務 | 預計時間 |
|-------|------|---------|
| 1 | 數據層改造 | 2-3 小時 |
| 2 | 圖表組件創建 | 4-5 小時 |
| 3 | 控制面板改造 | 1-2 小時 |
| 4 | MDI 容器整合 | 2 小時 |
| 5 | 測試與優化 | 2-3 小時 |
| **總計** | | **11-15 小時** |

---

## 🚀 下一步行動

1. **確認需求**: 與用戶確認是否完全按照 Detailed Lap Analysis 的 UI 設計
2. **開始 Phase 1**: 先改造數據層，支援多車手數據載入
3. **創建分支**: 在 git 中創建 `feature/throttle-multi-driver` 分支（如果使用版本控制）
4. **逐步推進**: 完成一個 Phase 後測試，再進入下一個 Phase

---

**狀態**: ⏳ 等待用戶確認需求  
**負責人**: AI Assistant  
**優先級**: 高
