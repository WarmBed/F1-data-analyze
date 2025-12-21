# Distance Diff 時間軸功能修復計劃

## 🔍 問題診斷

### 根本原因
**時間軸參數 `use_time_axis` 沒有從 MDI 傳遞到 Data Loader**

### 詳細分析

#### 問題 1: Data Loader 缺少參數
```python
# ❌ 當前簽名 (Line 48-51)
def load_distancediff_data(self, year: int, race: str, session: str, 
                          driver1: str, driver2: str = None, 
                          lap1: int = 1, lap2: int = None, 
                          is_fastest_lap: bool = False) -> bool:
```

**缺少**: `use_time_axis: bool = False` 參數

#### 問題 2: MDI 調用未傳遞參數
```python
# ❌ 當前調用 (Line 194-202)
success = self.distancediff_loader.load_distancediff_data(
    year=int(year),
    race=race,
    session=session,
    driver1=driver1,
    driver2=driver2,
    lap1=lap1,
    lap2=lap2,
    is_fastest_lap=is_fastest  # 缺少 use_time_axis
)
```

#### 問題 3: 為什麼 Cross-Event 模式能工作？
Cross-Event 模式**繞過了 data loader**，直接由 MDI 處理 API 響應：
```python
# ✅ Cross-Event 模式 (Line 1645-1740 _on_cross_event_data_loaded)
chart_data = {
    "distancediff_data": {
        "distance": telemetry.get("distance", []),
        "cumulative_distance_difference": telemetry.get("distance_difference", []),
        "driver1_time_seconds": telemetry.get("driver1_time_seconds", []),
        "driver2_time_seconds": telemetry.get("driver2_time_seconds", []),
    },
    "use_time_axis": getattr(self, 'use_time_axis', False),  # ✅ 直接設置
}
self.distancediff_chart_widget.set_time_axis_mode(self.use_time_axis)  # ✅ 直接設置
self._update_chart(chart_data)
```

#### 問題 4: 為什麼 Standard Lap Comparison 不能工作？
Standard 模式**必須通過 data loader**，但 data loader 沒有接收或傳遞 `use_time_axis`：
```python
# ❌ Standard 模式流程
update_lap_parameters(use_time_axis=True)
  → 設置 self.use_time_axis = True  ✅
  → 調用 chart_widget.set_time_axis_mode(True)  ✅
  → 調用 data_manager.load_distancediff_data(...)  ❌ 沒有傳遞 use_time_axis
    → Data Loader 不知道需要時間軸數據
    → API 請求中沒有 use_time_axis 參數
    → 返回的數據缺少 driver1_time_seconds/driver2_time_seconds
    → Chart Widget 無法繪製時間軸
```

---

## 🛠️ 修復方案

### 階段 1: 修復 Data Loader 簽名

#### 1.1 修改 `distancediff_analysis_data_loader.py`
**檔案**: `distancediff_analysis_data_loader.py`  
**位置**: Line 48-51

```python
# ✅ 新簽名
def load_distancediff_data(self, year: int, race: str, session: str, 
                          driver1: str, driver2: str = None, 
                          lap1: int = 1, lap2: int = None, 
                          is_fastest_lap: bool = False,
                          use_time_axis: bool = False) -> bool:  # ✅ 新增參數
    """
    載入距離差分析數據 - 向後兼容接口
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 會話類型 (R/Q/S)
        driver1: 車手1代碼
        driver2: 車手2代碼
        lap1: 車手1圈數
        lap2: 車手2圈數
        is_fastest_lap: 是否為最快圈
        use_time_axis: 是否使用時間軸模式  # ✅ 新增文檔
        
    Returns:
        bool: 載入是否成功啟動
    """
```

#### 1.2 Data Loader 內部傳遞參數
**位置**: 需要找到 data loader 內部調用 UniversalDataLoader 的地方

```python
# 需要將 use_time_axis 傳遞到底層 API 請求
return self.load_data(
    year=year,
    race=race,
    session=session,
    driver1=driver1,
    driver2=driver2,
    lap1=lap1,
    lap2=lap2,
    is_fastest_lap=is_fastest_lap,
    use_time_axis=use_time_axis  # ✅ 新增傳遞
)
```

### 階段 2: 修復 MDI 調用

#### 2.1 修改 `distancediff_analysis_mdi.py` - load_distancediff_data 調用
**位置**: Line 194-202

```python
# ✅ 新調用
success = self.distancediff_loader.load_distancediff_data(
    year=int(year),
    race=race,
    session=session,
    driver1=driver1,
    driver2=driver2,
    lap1=lap1,
    lap2=lap2,
    is_fastest_lap=is_fastest,
    use_time_axis=getattr(self, 'use_time_axis', False)  # ✅ 新增傳遞
)
```

#### 2.2 修改 `update_lap_parameters` 方法
**位置**: Line 748-880

```python
# ✅ 確保在調用前已設置 use_time_axis
def update_lap_parameters(self, year: str, race: str, session: str, 
                         driver1: str, driver2: str, 
                         lap1: int, lap2: int,
                         use_time_axis: bool = False):
    # 立即保存時間軸狀態（在任何其他操作前）
    self.use_time_axis = use_time_axis  # ✅ 優先設置
    
    # 設置 Chart Widget 時間軸模式
    if self.distancediff_chart_widget:
        self.distancediff_chart_widget.set_time_axis_mode(use_time_axis)
    
    # 檢測參數變化（包括時間軸）
    params_changed = (
        self.current_year != str(year) or 
        self.current_race != race or 
        self.current_session != session or
        self.driver1 != driver1 or
        self.driver2 != driver2 or
        self.lap1 != lap1 or
        self.lap2 != lap2 or
        getattr(self, 'use_time_axis', False) != use_time_axis
    )
    
    # 調用 data manager 時傳遞 use_time_axis
    if params_changed or not hasattr(self, '_data_loaded'):
        success = self.data_manager.load_distancediff_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            driver1=self.driver1,
            driver2=self.driver2,
            lap1=self.lap1,
            lap2=self.lap2,
            is_fastest=is_fastest,
            use_time_axis=use_time_axis  # ✅ 新增傳遞
        )
```

### 階段 3: 確保 API 端支持

#### 3.1 檢查 CLI Function 12 是否支持 time axis
需要確認 CLI `function 12` (Distance Diff) 支持 `--use-time-axis` 參數

#### 3.2 檢查 API 響應格式
API 應該返回以下欄位：
```json
{
  "Distancediff": {
    "distance": [...],
    "distance_difference": [...],
    "driver1_time_seconds": [...],  // ✅ 時間軸必需
    "driver2_time_seconds": [...]   // ✅ 時間軸必需
  }
}
```

### 階段 4: 同步修復 Speed 和 Speed Diff

為了一致性，應該同時修復其他兩個模組：

#### 4.1 Speed Analysis
- 檔案: `speed_analysis_data_loader.py` - 添加 `use_time_axis` 參數
- 檔案: `speed_analysis_mdi.py` - 傳遞 `use_time_axis` 到 data loader

#### 4.2 Speed Diff Analysis
- 檔案: `speeddiff_analysis_data_loader.py` - 添加 `use_time_axis` 參數
- 檔案: `speeddiff_analysis_mdi.py` - 傳遞 `use_time_axis` 到 data loader

---

## 📋 修復檢查清單

### Phase 1: Distance Diff 修復
- [ ] ✅ 添加 `use_time_axis` 參數到 `load_distancediff_data()` 簽名
- [ ] ✅ Data Loader 內部傳遞 `use_time_axis` 到 API/CLI 請求
- [ ] ✅ MDI `load_distancediff_data()` 調用時傳遞 `use_time_axis`
- [ ] ✅ MDI `update_lap_parameters()` 中的 data_manager 調用傳遞 `use_time_axis`
- [ ] ✅ 驗證 CLI Function 12 支持 `--use-time-axis`
- [ ] ✅ 測試 Standard Lap Comparison + Time Axis 功能

### Phase 2: Speed 修復（一致性）
- [ ] ✅ 添加 `use_time_axis` 參數到 `load_speed_data()` 簽名
- [ ] ✅ Data Loader 內部傳遞參數
- [ ] ✅ MDI 調用時傳遞參數
- [ ] ✅ 測試功能

### Phase 3: Speed Diff 修復（一致性）
- [ ] ✅ 添加 `use_time_axis` 參數到 `load_speeddiff_data()` 簽名
- [ ] ✅ Data Loader 內部傳遞參數
- [ ] ✅ MDI 調用時傳遞參數
- [ ] ✅ 測試功能

### Phase 4: 回歸測試
- [ ] ✅ 測試 Distance Diff Standard Mode + Time Axis
- [ ] ✅ 測試 Distance Diff Cross-Event Mode + Time Axis
- [ ] ✅ 測試 Speed Standard Mode + Time Axis
- [ ] ✅ 測試 Speed Diff Standard Mode + Time Axis
- [ ] ✅ 測試所有模組的 D→X 和 X→D 按鈕切換

---

## 🎯 預期結果

修復後，Standard Lap Comparison 模式應該能夠：
1. ✅ 正確傳遞 `use_time_axis` 參數到 data loader
2. ✅ Data Loader 將參數傳遞到 API/CLI 請求
3. ✅ API 返回包含 `driver1_time_seconds` 和 `driver2_time_seconds` 的完整數據
4. ✅ Chart Widget 正確切換時間軸顯示
5. ✅ D→X 和 X→D 按鈕切換正常工作

---

## 📌 優先級

**高優先級**:
- Phase 1: Distance Diff 修復（用戶報告的主要問題）

**中優先級**:
- Phase 2-3: Speed 和 Speed Diff 修復（一致性，避免未來混淆）

**低優先級**:
- Phase 4: 回歸測試（確保所有功能正常）

---

## 🚀 開始執行

建議從 Phase 1 開始，逐步修復 Distance Diff 模組。
