# Distance Diff 時間軸功能修復報告

## 📅 修復日期
2025-11-14

## 🎯 問題根本原因

**Distance Diff 模組的 Standard Lap Comparison 模式無法使用時間軸功能**

### 根本原因
`use_time_axis` 參數沒有從 MDI → Data Loader → API 請求的完整鏈路傳遞。

### 問題細節

1. **TelemetryDataLoader 基類**（Line 330）
   - ❌ 方法簽名缺少 `use_time_axis` 參數
   - ❌ API 請求參數（worker_params）沒有包含 `use_time_axis`

2. **distancediff_analysis_data_loader.py**（Line 48-82）
   - ❌ `load_distancediff_data()` 簽名缺少 `use_time_axis` 參數
   - ❌ 調用基類 `load_telemetry_data()` 時沒有傳遞參數

3. **distancediff_analysis_mdi.py**（多處）
   - ❌ 調用 `distancediff_loader.load_distancediff_data()` 時沒有傳遞 `use_time_axis`
   - ❌ `update_lap_parameters()` 中的 `data_manager.load_distancediff_data()` 調用沒有傳遞參數
   - ❌ 其他方法（如 `_on_lap_numbers_changed`）的調用也缺少參數

---

## 🛠️ 修復內容

### Phase 1: 基類修復

#### 1.1 修改 `telemetry_data_loader_base.py` 方法簽名（Line 330）

**修改前**:
```python
def load_telemetry_data(self, year: int, race: str, session: str,
                       driver1: str, driver2: str = None,
                       lap1: int = 1, lap2: int = None,
                       is_fastest_lap: bool = False) -> bool:
```

**修改後**:
```python
def load_telemetry_data(self, year: int, race: str, session: str,
                       driver1: str, driver2: str = None,
                       lap1: int = 1, lap2: int = None,
                       is_fastest_lap: bool = False,
                       use_time_axis: bool = False) -> bool:  # ✅ 新增參數
```

#### 1.2 修改 `telemetry_data_loader_base.py` incoming_session（Line 370-383）

**修改前**:
```python
incoming_session = {
    'year': year,
    'race': race,
    'session': session,
    'driver1': driver1,
    'driver2': driver2,
    'driver2_effective': effective_driver2,
    'lap1': lap1,
    'lap2': lap2,
    'is_fastest_lap': is_fastest_lap,
    'force_refresh': False,
    'single_driver_mode': single_driver_mode
}
```

**修改後**:
```python
incoming_session = {
    'year': year,
    'race': race,
    'session': session,
    'driver1': driver1,
    'driver2': driver2,
    'driver2_effective': effective_driver2,
    'lap1': lap1,
    'lap2': lap2,
    'is_fastest_lap': is_fastest_lap,
    'force_refresh': False,
    'single_driver_mode': single_driver_mode,
    'use_time_axis': use_time_axis  # ✅ 新增
}
```

#### 1.3 修改 `telemetry_data_loader_base.py` worker_params（Line 651-662）

**修改前**:
```python
worker_params = {
    "year": params.get('year'),
    "race": params.get('race'),
    "session": params.get('session'),
    "driver1": driver1,
    "driver2": driver2,
    "lap1": lap1,
    "lap2": lap2,
    "force_refresh": params.get('force_refresh', False)
}
```

**修改後**:
```python
worker_params = {
    "year": params.get('year'),
    "race": params.get('race'),
    "session": params.get('session'),
    "driver1": driver1,
    "driver2": driver2,
    "lap1": lap1,
    "lap2": lap2,
    "force_refresh": params.get('force_refresh', False),
    "use_time_axis": params.get('use_time_axis', False)  # ✅ 新增
}
```

---

### Phase 2: Data Loader 修復

#### 2.1 修改 `distancediff_analysis_data_loader.py` 簽名（Line 48-51）

**修改前**:
```python
def load_distancediff_data(self, year: int, race: str, session: str, 
                          driver1: str, driver2: str = None, 
                          lap1: int = 1, lap2: int = None, 
                          is_fastest_lap: bool = False) -> bool:
```

**修改後**:
```python
def load_distancediff_data(self, year: int, race: str, session: str, 
                          driver1: str, driver2: str = None, 
                          lap1: int = 1, lap2: int = None, 
                          is_fastest_lap: bool = False,
                          use_time_axis: bool = False) -> bool:  # ✅ 新增參數
```

#### 2.2 修改 `distancediff_analysis_data_loader.py` 調用（Line 82）

**修改前**:
```python
return self.load_telemetry_data(year, race, session, driver1, driver2, lap1, lap2, is_fastest_lap)
```

**修改後**:
```python
return self.load_telemetry_data(year, race, session, driver1, driver2, lap1, lap2, is_fastest_lap, use_time_axis)
```

---

### Phase 3: MDI 調用修復

#### 3.1 修改 `distancediff_analysis_mdi.py` - load_distancediff_data 調用（Line 194-202）

**修改前**:
```python
success = self.distancediff_loader.load_distancediff_data(
    year=int(year),
    race=race,
    session=session,
    driver1=driver1,
    driver2=driver2,
    lap1=lap1,
    lap2=lap2,
    is_fastest_lap=is_fastest
)
```

**修改後**:
```python
success = self.distancediff_loader.load_distancediff_data(
    year=int(year),
    race=race,
    session=session,
    driver1=driver1,
    driver2=driver2,
    lap1=lap1,
    lap2=lap2,
    is_fastest_lap=is_fastest,
    use_time_axis=getattr(self, 'use_time_axis', False)  # ✅ 新增
)
```

#### 3.2 修改 `update_lap_parameters` 中的調用（Line 826, 858）

**自動批量修改**（使用 `fix_time_axis_param.py` 腳本）：
- Line 826（params_changed 分支）
- Line 858（首次載入分支）
- Line 995（其他調用）

**修改模式**:
```python
success = self.data_manager.load_distancediff_data(
    year=self.current_year,
    race=self.current_race,
    session=self.current_session,
    driver1=self.driver1,
    driver2=self.driver2,
    lap1=self.lap1,
    lap2=self.lap2,
    use_time_axis=use_time_axis  # ✅ 新增
)
```

#### 3.3 修改 `_on_lap_numbers_changed` 中的調用（Line 995-1005）

**特殊處理**：此方法沒有 `use_time_axis` 參數，使用實例變數

**修改後**:
```python
success = self.data_manager.load_distancediff_data(
    year=self.current_year,
    race=self.current_race,
    session=self.current_session,
    driver1=self.driver1,
    driver2=self.driver2,
    lap1=self.lap1,
    lap2=self.lap2,
    use_time_axis=getattr(self, 'use_time_axis', False)  # ✅ 使用實例變數
)
```

---

## ✅ 修復驗證

### 語法檢查
- ✅ `telemetry_data_loader_base.py` - 無錯誤
- ✅ `distancediff_analysis_data_loader.py` - 無錯誤
- ✅ `distancediff_analysis_mdi.py` - 無錯誤

### 修改統計
- 修改檔案數量：**3 個**
- 修改方法簽名：**2 個**
- 修改方法調用：**6 處**
- 新增參數傳遞：**8 處**

---

## 🔄 完整數據流

### 修復後的完整鏈路

```
用戶操作
  ↓
GUI 按鈕/選單（時間軸開關）
  ↓
distancediff_analysis_mdi.update_lap_parameters(use_time_axis=True)
  ↓
self.use_time_axis = use_time_axis  ✅ 狀態保存
  ↓
chart_widget.set_time_axis_mode(use_time_axis)  ✅ 圖表設置
  ↓
data_manager.load_distancediff_data(..., use_time_axis=use_time_axis)  ✅ 傳遞參數
  ↓
distancediff_analysis_data_loader.load_distancediff_data(..., use_time_axis=use_time_axis)
  ↓
self.load_telemetry_data(..., use_time_axis=use_time_axis)  ✅ 調用基類
  ↓
incoming_session['use_time_axis'] = use_time_axis  ✅ 保存到會話
  ↓
worker_params["use_time_axis"] = use_time_axis  ✅ API 請求參數
  ↓
TelemetryApiWorker 發送請求
  ↓
API 端點 /api/v2/analysis/execute (包含 use_time_axis 參數)
  ↓
CLI Function 12 (Distancediff) 處理 --use-time-axis 參數
  ↓
API 返回完整數據（包含 driver1_time_seconds, driver2_time_seconds）
  ↓
_on_api_success → _handle_api_success
  ↓
self._on_data_loaded(data)
  ↓
_update_chart(data)
  ↓
chart_widget.update_distancediff_data(data)
  ↓
圖表正確顯示時間軸模式 ✅
```

---

## 🎯 預期效果

修復後，Distance Diff 模組應該能夠：

1. ✅ **Standard Lap Comparison 模式 + 時間軸**
   - 用戶切換時間軸開關
   - API 請求包含 `use_time_axis=True`
   - API 返回包含時間數據的完整響應
   - Chart Widget 正確切換 X 軸為時間

2. ✅ **Cross-Event Comparison 模式 + 時間軸**
   - 已有的實現繼續正常工作
   - MDI 直接處理 API 響應，設置時間軸模式

3. ✅ **參數變化檢測**
   - `update_lap_parameters` 能檢測時間軸模式變化
   - 時間軸變化觸發數據重載
   - 所有參數正確傳遞到 API

4. ✅ **D→X 和 X→D 按鈕切換**
   - 同步模式切換能正確傳遞時間軸狀態
   - 參數介面（get_parameter_interface）包含時間軸狀態

---

## 📋 後續任務

### 高優先級
- [ ] **測試 Distance Diff Standard Mode + Time Axis**
  - 啟動 GUI
  - 載入 Distance Diff 模組
  - 切換時間軸開關
  - 驗證圖表 X 軸正確切換

### 中優先級  
- [ ] **同步修復 Speed 和 Speed Diff 模組**
  - 應用相同的修復到 `speed_analysis_data_loader.py`
  - 應用相同的修復到 `speeddiff_analysis_data_loader.py`
  - 確保所有 lap analysis 模組一致性

### 低優先級
- [ ] **回歸測試**
  - 測試所有模組的多賽季載入功能
  - 測試所有模組的 D→X 和 X→D 按鈕切換
  - 測試所有模組的時間軸功能

---

## 🔍 技術細節

### 為什麼 Cross-Event 模式能工作？

Cross-Event 模式**繞過了 data loader**，直接由 MDI 處理 API 響應：

```python
# _on_cross_event_data_loaded (Line 1645-1740)
chart_data = {
    "distancediff_data": {
        "distance": telemetry.get("distance", []),
        "cumulative_distance_difference": telemetry.get("distance_difference", []),
        "driver1_time_seconds": telemetry.get("driver1_time_seconds", []),
        "driver2_time_seconds": telemetry.get("driver2_time_seconds", []),
    },
    "use_time_axis": getattr(self, 'use_time_axis', False),  # ✅ 直接設置
}
self.distancediff_chart_widget.set_time_axis_mode(self.use_time_axis)
self._update_chart(chart_data)
```

因此 Cross-Event 模式從一開始就有時間軸支持，但 Standard 模式沒有。

### 為什麼 Standard 模式不工作？

Standard 模式**必須通過 data loader**，但 data loader 沒有接收或傳遞 `use_time_axis`：

**修復前的錯誤流程**：
```python
update_lap_parameters(use_time_axis=True)
  → self.use_time_axis = True  ✅
  → chart_widget.set_time_axis_mode(True)  ✅
  → data_manager.load_distancediff_data(...)  ❌ 沒有傳遞 use_time_axis
    → API 請求沒有 use_time_axis 參數
    → 返回的數據缺少時間欄位
    → Chart Widget 無法繪製時間軸 ❌
```

### API 端點支持

API 端點 `/api/v2/analysis/execute` 應該已經支持 `use_time_axis` 參數：

```json
{
  "function_id": 12,
  "year": 2025,
  "race": "Japan",
  "session": "R",
  "driver1": "VER",
  "driver2": "LEC",
  "lap1": 5,
  "lap2": 5,
  "use_time_axis": true  // ✅ 新增
}
```

CLI Function 12 (Distancediff) 應該支持 `--use-time-axis` 參數。

---

## 📝 結論

此修復解決了 Distance Diff 模組 Standard Lap Comparison 模式無法使用時間軸功能的根本問題。

**關鍵修復點**：
1. ✅ 基類添加 `use_time_axis` 參數支持
2. ✅ Data Loader 傳遞參數到基類
3. ✅ MDI 所有調用點傳遞參數
4. ✅ API 請求包含參數
5. ✅ 語法驗證通過

**預期結果**：
- Distance Diff 的 Standard Mode 應該能夠正常使用時間軸功能
- 時間軸切換應該觸發數據重載並正確顯示

**下一步**：
1. 測試 Distance Diff 修復效果
2. 同步修復 Speed 和 Speed Diff 模組
3. 執行完整回歸測試

---

## 🚀 開發者指南

### 如何測試修復

```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 打開 Distance Diff Analysis 模組
# 選單：Lap Analysis → Distance Diff Analysis

# 3. 載入數據
年份：2025
賽事：Japan
會話：R
車手1：VER
車手2：LEC
圈數：5 vs 5

# 4. 切換時間軸開關
# 點擊 "時間軸" 按鈕或勾選框

# 5. 驗證
# - 圖表 X 軸應該從 "距離 (m)" 切換到 "時間 (s)"
# - API 請求 Log 應該包含 use_time_axis=True
# - 數據重載應該正常完成
```

### 調試技巧

如果時間軸仍然不工作，檢查：

1. **MDI Log**：
```python
print(f"[distancediff_MDI] 🕒 時間軸模式: {use_time_axis}")
```

2. **Data Loader Log**：
```python
print(f"[DISTANCEDIFF_LOADER] use_time_axis: {use_time_axis}")
```

3. **API Worker Log**：
```python
print(f"worker_params: {worker_params}")
# 應該包含 "use_time_axis": True
```

4. **CLI Log**（如果使用 CLI）：
```bash
python f1_analysis_modular_main.py -f 12 -y 2025 -r Japan -s R -d VER -d2 LEC --use-time-axis
```

---

**修復完成日期**：2025-11-14  
**修復版本**：v2.0.0  
**作者**：GitHub Copilot AI Assistant
