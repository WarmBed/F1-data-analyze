# Rain Analysis → Box Plot Analysis - 轉換對照表

## 📋 文件級轉換

| Rain Analysis | Box Plot Analysis | 變更類型 |
|---------------|-------------------|----------|
| `rain_analysis_universal.py` | `lap_box_plot_analysis_mdi.py` | 重命名 + 邏輯重寫 |
| `rain_chart_widget.py` | `lap_box_plot_chart_widget.py` | 全新實現 |
| `__init__.py` | `__init__.py` | 導出更新 |

---

## 🏗️ 類別轉換對照

### 1. API Worker

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| `RainAnalysisApiWorker` | `LapTimeBoxPlotApiWorker` |
| `function_id = "1"` | `function_id = "28"` |
| `timeout = 20.0` | `timeout = 75.0` |
| 註釋: "CLI Function 1" | 註釋: "CLI Function 28: detailed_laptime_analysis" |

---

### 2. Data Manager

| Rain Analysis | Box Plot Analysis | 說明 |
|---------------|-------------------|------|
| `RainAnalysisDataManager` | `LapTimeBoxPlotDataManager` | 基類相同 (UniversalDataLoader) |
| `analysis_type = "rain"` | `analysis_type = "laptime_boxplot"` | 註冊類型 |
| `cli_function = "1"` | `cli_function = "28"` | CLI 功能 ID |
| `api_timeout = 20.0` | `api_timeout = 75.0` | API 超時 |

#### 屬性轉換

| Rain Analysis | Box Plot Analysis | 數據類型 |
|---------------|-------------------|----------|
| `self.weather_data` | `self.driver_laptimes` | `Dict[str, List[float]]` |
| `self.lap_weather_data` | ❌ 刪除 | - |
| `self.statistics` | `self.statistics` | `Dict[str, Dict[str, float]]` |
| ❌ 無 | `self.filter_settings` | `Dict[str, Any]` (新增) |

#### 方法轉換

| Rain Analysis 方法 | Box Plot 方法 | 變更說明 |
|-------------------|---------------|----------|
| `process_loaded_data()` | `process_loaded_data()` | 完全重寫：從 `all_drivers_detailed_laptime` 提取 |
| `_process_lap_weather_data()` | `_extract_lap_times()` | 邏輯改為提取圈速 + 過濾進站圈 |
| `_prepare_chart_data()` | ❌ 刪除 | 不再需要 charts_data |
| ❌ 無 | `_filter_outliers_iqr()` | **新增**: IQR 統計過濾 |
| ❌ 無 | `_calculate_statistics()` | **新增**: 統計指標計算 |
| ❌ 無 | `update_filter_settings()` | **新增**: 動態過濾更新 |
| ❌ 無 | `get_processed_data()` | **新增**: 獲取處理後數據 |
| `get_rain_summary()` | ❌ 刪除 | Rain 特有方法 |

#### 文件模式轉換

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| `rain_data_{year}_{race}_{session}_*.json` | `detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json` |

---

### 3. Control Widget

| Rain Analysis | Box Plot Analysis | 說明 |
|---------------|-------------------|------|
| `RainAnalysisControlWidget` | `LapTimeBoxPlotControlWidget` | UI 完全重新設計 |

#### 信號轉換

| Rain Analysis | Box Plot Analysis | 用途 |
|---------------|-------------------|------|
| `chart_type_changed(str)` | ❌ 刪除 | Rain 有多種圖表類型 |
| `parameter_changed(str, Any)` | ❌ 刪除 | Rain 的通用參數 |
| ❌ 無 | `settings_changed(dict)` | **新增**: 過濾設定變更 |
| ❌ 無 | `reload_requested()` | **新增**: 重新載入數據 |
| ❌ 無 | `export_requested()` | **新增**: 匯出圖表 |

#### UI 組件轉換

| Rain Analysis 組件 | Box Plot 組件 | 說明 |
|-------------------|---------------|------|
| `chart_type_combo` (QComboBox) | ❌ 刪除 | 不需要圖表類型選擇 |
| `parameter_panel` (多個參數) | ❌ 刪除 | 不需要通用參數 |
| ❌ 無 | `filter_pit_checkbox` (QCheckBox) | **新增**: 進站圈過濾 |
| ❌ 無 | `filter_outliers_checkbox` (QCheckBox) | **新增**: 異常值過濾 |
| ❌ 無 | `iqr_spinbox` (QDoubleSpinBox) | **新增**: IQR 閾值 |
| ❌ 無 | `reload_button` (QPushButton) | **新增**: 🔄 重新載入 |
| ❌ 無 | `export_button` (QPushButton) | **新增**: 💾 匯出 |
| `stats_label` (QLabel) | `stats_label` (QLabel) | 保留但內容不同 |

#### 統計標籤格式

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| `"總圈數: X | 下雨圈數: Y | 下雨比例: Z%"` | `"車手數: X | 總圈數: Y | 平均時間: Z.ZZZ秒"` |

---

### 4. Chart Widget

| Rain Analysis | Box Plot Analysis | 說明 |
|---------------|-------------------|------|
| `RainAnalysisChartWidget` | `LapTimeBoxPlotChartWidget` | **完全重寫** |

#### 圖表類型轉換

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| 雙 Y 軸折線圖 | 箱型圖 (boxplot) |
| 柱狀圖 | ❌ 刪除 |
| 趨勢圖 | ❌ 刪除 |
| `switch_chart_type()` 方法 | ❌ 刪除 |

#### 核心方法

| Rain Analysis | Box Plot Analysis | 變更 |
|---------------|-------------------|------|
| `update_data(charts_data)` | `update_data(driver_laptimes)` | 參數結構改變 |
| `plot_dual_axis_chart()` | ❌ 刪除 | Rain 特有 |
| `plot_bar_chart()` | ❌ 刪除 | Rain 特有 |
| `plot_trend_chart()` | ❌ 刪除 | Rain 特有 |
| ❌ 無 | `_plot_boxplot()` | **新增**: 繪製箱型圖 |
| `export_chart()` | `export_chart()` | 保留，邏輯類似 |
| `clear_chart()` | `clear_chart()` | 保留，邏輯類似 |

#### 數據輸入格式

**Rain Analysis**:
```python
{
    "charts_data": {
        "chart_type": "dual_axis_line",
        "data": {
            "x": [...],
            "y1": [...],
            "y2": [...]
        }
    }
}
```

**Box Plot Analysis**:
```python
{
    "driver_laptimes": {
        "VER": [90.1, 89.5, ...],
        "LEC": [90.3, 89.7, ...]
    },
    "statistics": {
        "VER": {"mean": 89.5, "median": 89.4, ...}
    }
}
```

---

### 5. MDI 主類

| Rain Analysis | Box Plot Analysis | 說明 |
|---------------|-------------------|------|
| `RainAnalysisUniversal` | `LapTimeBoxPlotAnalysis` | 基類相同 (UniversalAnalysisMDI) |
| `module_type = "rain"` | `module_type = "laptime_boxplot"` | 註冊類型 |
| `default_size = (1000, 600)` | `default_size = (1200, 700)` | 視窗大小 |

#### 方法轉換

| Rain Analysis 方法 | Box Plot 方法 | 變更說明 |
|-------------------|---------------|----------|
| `create_data_manager()` | `create_data_manager()` | 返回不同類別 |
| `create_chart_widget()` | `create_chart_widget()` | 返回不同類別 |
| `create_control_widget()` | `create_control_widget()` | 返回不同類別 + 不同信號連接 |
| `update_lap_parameters()` | `update_lap_parameters()` | 簡化邏輯（移除 charts_data） |
| `update_analysis_parameters()` | `update_analysis_parameters()` | 保持相同 |
| `_on_chart_type_changed()` | ❌ 刪除 | Rain 特有 |
| `_on_parameter_changed()` | ❌ 刪除 | Rain 特有 |
| ❌ 無 | `_on_filter_settings_changed()` | **新增**: 處理過濾變更 |
| ❌ 無 | `_on_reload_requested()` | **新增**: 處理重新載入 |
| ❌ 無 | `_on_export_requested()` | **新增**: 處理匯出請求 |
| `resizeEvent()` | `resizeEvent()` | 保持相同（僅日誌改變） |
| `set_responsive_layout()` | `set_responsive_layout()` | 保持相同（僅日誌改變） |
| `get_module_info()` | `get_module_info()` | 完全重寫內容 |
| `validate_parameters()` | `validate_parameters()` | 保持相同 |
| `get_analysis_summary()` | `get_analysis_summary()` | 完全重寫邏輯 |

#### 信號連接變更

**Rain Analysis**:
```python
self.control_widget.chart_type_changed.connect(self._on_chart_type_changed)
self.control_widget.parameter_changed.connect(self._on_parameter_changed)
```

**Box Plot Analysis**:
```python
self.control_widget.settings_changed.connect(self._on_filter_settings_changed)
self.control_widget.reload_requested.connect(self._on_reload_requested)
self.control_widget.export_requested.connect(self._on_export_requested)
```

---

## 🎨 視覺元素轉換

### 圖表視覺化

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| 折線圖：圈數 vs 降雨量 | 箱型圖：車手 vs 圈速分布 |
| 雙 Y 軸（降雨 + 溫度） | 單 Y 軸（圈速時間） |
| 藍色/綠色系（天氣主題） | 車隊配色（20 種顏色） |
| 圖例：降雨、溫度 | 圖例：箱子、中位數、平均值、異常值 |

### 配色方案

**Rain Analysis**: 固定顏色
```python
rain_color = 'blue'
temp_color = 'red'
```

**Box Plot Analysis**: 車隊配色
```python
TEAM_COLORS = {
    'VER': '#3671C6',  # Red Bull
    'LEC': '#E8002D',  # Ferrari
    'HAM': '#27F4D2',  # Mercedes
    ...  # 20 位車手
}
```

---

## 📊 數據處理邏輯轉換

### JSON 數據提取

**Rain Analysis**:
```python
# 從 weather_data 提取
weather_info = raw_data.get("weather_data", {})
self.weather_data = weather_info.get("weather", [])
```

**Box Plot Analysis**:
```python
# 從 all_drivers_detailed_laptime 提取
all_drivers_data = raw_data.get("all_drivers_detailed_laptime", {})
for driver, laps in all_drivers_data.items():
    self.driver_laptimes[driver] = self._extract_lap_times(laps)
```

### 過濾邏輯

**Rain Analysis**: 無過濾（顯示所有天氣數據）

**Box Plot Analysis**: 雙重過濾
```python
# 1. 進站圈過濾
if lap.get('PitOutTime') or lap.get('PitInTime'):
    continue  # 跳過進站圈

# 2. IQR 異常值過濾
q1 = np.percentile(lap_times, 25)
q3 = np.percentile(lap_times, 75)
iqr = q3 - q1
filtered = [t for t in lap_times 
            if q1 - 1.5*iqr <= t <= q3 + 1.5*iqr]
```

### 統計計算

**Rain Analysis**:
```python
{
    "total_laps": 44,
    "rain_laps": 12,
    "rain_percentage": 27.3,
    "has_rain_data": True
}
```

**Box Plot Analysis**:
```python
{
    "VER": {
        "mean": 89.567,
        "median": 89.500,
        "q1": 89.200,
        "q3": 89.800,
        "iqr": 0.600,
        "count": 52
    },
    ...
}
```

---

## 🔄 工作流程比較

### Rain Analysis 流程

```
載入數據
  ↓
提取 weather_data
  ↓
_process_lap_weather_data()
  ↓
_prepare_chart_data()
  ↓
創建 charts_data payload
  ↓
chart_widget.update_data(charts_data)
  ↓
根據 chart_type 繪製不同圖表
```

### Box Plot Analysis 流程

```
載入數據
  ↓
提取 all_drivers_detailed_laptime
  ↓
_extract_lap_times() (含進站圈過濾)
  ↓
_filter_outliers_iqr()
  ↓
_calculate_statistics()
  ↓
組合 {driver_laptimes, statistics}
  ↓
chart_widget.update_data(processed_data)
  ↓
_plot_boxplot() (固定圖表類型)
```

---

## 📁 文件命名轉換

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| `rain_data_2025_Belgium_R.json` | `detailed_laptime_analysis_2025_Belgium_R_all_drivers.json` |
| `rain_analysis_summary.json` | ❌ 無獨立摘要文件 |

---

## 🔧 配置參數轉換

### AnalysisConfig

**Rain Analysis**:
```python
AnalysisConfig.register_analysis_type(
    type_name="rain",
    cli_function="1",
    search_dirs=["json", "json_exports", "cache"],
    file_patterns=["rain_data_{year}_{race}_{session}_*.json"]
)
```

**Box Plot Analysis**:
```python
AnalysisConfig.register_analysis_type(
    type_name="laptime_boxplot",
    cli_function="28",
    search_dirs=["json", "json_exports", "cache"],
    file_patterns=["detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json"]
)
```

### AnalysisMDIConfig

**Rain Analysis**:
```python
AnalysisMDIConfig.register_module_type(
    module_type="rain",
    default_size=(1000, 600),
    requires_driver_params=False
)
```

**Box Plot Analysis**:
```python
AnalysisMDIConfig.register_module_type(
    module_type="laptime_boxplot",
    default_size=(1200, 700),
    requires_driver_params=False
)
```

---

## 📝 日誌前綴轉換

所有 `print()` 語句：

| Rain Analysis | Box Plot Analysis |
|---------------|-------------------|
| `[RAIN_MDI]` | `[BOXPLOT_MDI]` |
| `[RAIN_DATA]` | `[BOXPLOT_DATA]` (如使用) |
| `[RAIN_CHART]` | `[BOXPLOT_CHART]` |
| `[ERROR] [RAIN_MDI]` | `[ERROR] [BOXPLOT_MDI]` |

---

## 🎯 核心差異總結

### 架構保留項目 ✅

1. **UniversalDataLoader** 基類
2. **UniversalAnalysisMDI** 基類
3. **AnalysisConfig** 註冊系統
4. **AnalysisMDIConfig** 註冊系統
5. **API Worker** 模式（QThread）
6. **信號槽機制**
7. **MDI 視窗架構**
8. **響應式佈局**

### 完全重寫項目 ✏️

1. **數據處理邏輯** (weather → lap times)
2. **圖表類型** (折線圖 → 箱型圖)
3. **控制面板 UI** (圖表類型選擇 → 過濾控制)
4. **統計計算** (降雨統計 → 圈速統計)
5. **過濾功能** (無 → IQR + 進站圈過濾)

### 新增功能 🆕

1. **IQR 異常值檢測**
2. **進站圈過濾**
3. **車隊配色方案**
4. **動態過濾更新**
5. **統計面板顯示**
6. **匯出文件對話框**

### 移除功能 ❌

1. **多圖表類型切換**
2. **通用參數控制**
3. **charts_data payload**
4. **天氣數據處理**

---

## 🔍 關鍵轉換點

### 1. 數據來源變更

```python
# Rain Analysis
raw_data.get("weather_data", {})

# Box Plot Analysis
raw_data.get("all_drivers_detailed_laptime", {})
```

### 2. 核心數據結構變更

```python
# Rain Analysis
self.weather_data: List[Dict]  # [{lap: 1, rainfall: 0.5}, ...]

# Box Plot Analysis
self.driver_laptimes: Dict[str, List[float]]  # {"VER": [90.1, ...]}
```

### 3. 圖表參數變更

```python
# Rain Analysis
chart_widget.update_data({"charts_data": {...}})

# Box Plot Analysis
chart_widget.update_data({"driver_laptimes": {...}, "statistics": {...}})
```

### 4. 控制信號變更

```python
# Rain Analysis
chart_type_changed(str) + parameter_changed(str, Any)

# Box Plot Analysis
settings_changed(dict) + reload_requested() + export_requested()
```

---

## 📊 代碼行數對比

| 組件 | Rain Analysis | Box Plot Analysis | 差異 |
|------|---------------|-------------------|------|
| MDI 主文件 | 943 行 | 1056 行 | +113 行 |
| Chart Widget | ~400 行 | 280 行 | -120 行 |
| 總計 | ~1343 行 | ~1336 行 | -7 行 |

**結論**: 代碼量相近，但功能更專注（移除多圖表類型，增強過濾功能）

---

## ✅ 轉換完整性檢查清單

- [x] 所有類別名稱已轉換
- [x] 所有方法名稱已轉換或移除
- [x] 所有屬性名稱已轉換
- [x] 所有信號已重新定義
- [x] 所有 UI 組件已重新設計
- [x] 所有數據處理邏輯已重寫
- [x] 所有日誌前綴已更新
- [x] 所有註冊配置已更新
- [x] 所有文件模式已更新
- [x] 所有圖表邏輯已重寫
- [x] 所有統計計算已實現
- [x] 所有過濾功能已實現
- [x] 所有導入語句已更新
- [x] 所有 docstring 已更新
- [x] 主 GUI 整合已完成

**轉換完成度**: ✅ **100%**

---

## 🎓 學習要點

### 為什麼選擇 Rain Analysis 作為模板？

1. **架構完整**: 完整實現 UniversalAnalysisMDI 模式
2. **功能豐富**: 包含數據管理、圖表、控制面板
3. **經過驗證**: 已在生產環境中穩定運行
4. **代碼品質**: 結構清晰、註釋完整
5. **943 行範本**: 適合大規模功能開發

### 轉換策略

1. **保留架構**: UniversalDataLoader + UniversalAnalysisMDI
2. **替換邏輯**: 天氣數據 → 圈速數據
3. **簡化圖表**: 多類型 → 單一箱型圖
4. **增強控制**: 圖表選擇 → 過濾控制
5. **系統驗證**: 每個方法轉換後檢查編譯

---

*轉換對照表 v1.0*  
*生成日期: 2025-10-02*  
*用途: 未來模組開發參考*
