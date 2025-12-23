# All Drivers Speed & Brake Performance Race 更換機制深度調查報告

**調查時間**: 2025-10-19  
**調查目標**: 深度分析 All Drivers Straight Line Speed 和 All Drivers Brake Performance 模組在使用者更換 race 後的數據載入機制

---

## 📋 執行摘要

### 🔍 關鍵發現

**兩個模組的架構完全一致**，採用相同的三層架構：
1. **Module 層** (`all_drivers_*_module.py`) - 實作 `IAnalysisModule` 介面
2. **MDI 層** (`all_drivers_*_mdi.py`) - 繼承 `UniversalAnalysisMDI` 基類
3. **Loader 層** (`*_loader.py`) - 繼承 `UniversalDataLoader` 基類

**Race 更換流程**：
```
使用者操作 → Module.update_parameters() 
           ↓
           同步更新 MDI 屬性 (year/race/session)
           ↓
           調用 MDI.load_initial_data()
           ↓
           調用 Loader.load_data()
           ↓
           1. 檢查本地 JSON 檔案
           2. 找不到 → 調用 API 獲取數據
           3. API 成功 → 寫入緩存
           4. 發送 data_loaded 信號
           ↓
           MDI._on_data_loaded() → 更新表格視圖
```

---

## 🏗️ 架構分析

### 1️⃣ Module 層 - 參數更新入口

#### **Brake Performance Module**
**檔案**: `modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_module.py`

```python
def update_parameters(self, year=None, race=None, session=None, **kwargs) -> bool:
    """更新分析參數並重新載入數據"""
    try:
        print("[BRAKE_MODULE] 更新參數...")
        
        # ✅ 步驟 1: 更新 Module 層參數
        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session
        
        # ✅ 步驟 2: 同步更新 MDI 核心參數
        if self._brake_core:
            self._brake_core.year = self.current_year
            self._brake_core.race = self.current_race
            self._brake_core.session = self.current_session
            
            # ✅ 步驟 3: 觸發數據重新載入
            if hasattr(self._brake_core, 'load_initial_data'):
                self._brake_core.load_initial_data()
        
        print(f"[BRAKE_MODULE] 參數已更新: {self.current_year} {self.current_race} {self.current_session}")
        return True
        
    except Exception as e:
        print(f"[BRAKE_MODULE] 更新參數失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
```

#### **Speed Module**
**檔案**: `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_module.py`

```python
def update_parameters(self, year=None, race=None, session=None, **kwargs) -> bool:
    """更新分析參數並重新載入數據"""
    try:
        print("[SPEED_MODULE] 更新參數...")
        
        # ✅ 步驟 1: 更新 Module 層參數
        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session
        
        # ✅ 步驟 2: 同步更新 MDI 核心參數
        if self._speed_core:
            self._speed_core.year = self.current_year
            self._speed_core.race = self.current_race
            self._speed_core.session = self.current_session
            
            # ✅ 步驟 3: 觸發數據重新載入
            if hasattr(self._speed_core, 'load_initial_data'):
                self._speed_core.load_initial_data()
        
        print(f"✅ [SPEED_MODULE] 參數已更新: {self.current_year} {self.current_race} {self.current_session}")
        return True
        
    except Exception as e:
        print(f"❌ [SPEED_MODULE] 更新參數失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
```

**架構評估**:
- ✅ **完全一致**: 兩個模組使用相同的更新邏輯
- ✅ **清晰流程**: Module → MDI → Loader 三層級聯更新
- ✅ **自動觸發**: 參數更新後自動調用 `load_initial_data()`

---

### 2️⃣ MDI 層 - 數據載入協調

#### **Brake Performance MDI**
**檔案**: `modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_mdi.py`

```python
def load_initial_data(self):
    """載入初始數據"""
    try:
        print("[BRAKE_MDI] 開始載入初始數據...")
        
        if not self.data_manager:
            print("[BRAKE_MDI] data_manager 不存在")
            return
        
        # ✅ 調用資料載入器的 load_data 方法
        success = self.data_manager.load_data(
            year=self.year,
            race=self.race,
            session=self.session
        )
        
        if not success:
            print("[BRAKE_MDI] 資料載入失敗")
            
    except Exception as e:
        print(f"[BRAKE_MDI] 載入初始數據失敗: {e}")
        import traceback
        traceback.print_exc()


@pyqtSlot(dict)
def _on_data_loaded(self, data: Dict[str, Any]):
    """數據載入完成回調"""
    try:
        print("[BRAKE_MDI] 收到資料載入完成信號")
        
        if not data:
            self._on_load_error(tr("data_empty", "資料為空"))
            return
        
        self._current_data = data
        self._is_data_loaded = True
        
        # ✅ 更新表格元件
        if self.chart_widget:
            self.chart_widget.update_data(data)
        
        print("[BRAKE_MDI] 資料處理完成")
        
    except Exception as e:
        print(f"[BRAKE_MDI] 資料處理失敗: {e}")
        import traceback
        traceback.print_exc()
        self._on_load_error(f"{tr('data_processing_error', '資料處理錯誤')}: {str(e)}")
```

#### **Speed MDI**
**檔案**: `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_mdi.py`

```python
# ✅ 完全相同的實作邏輯
# load_initial_data() - 調用 data_manager.load_data()
# _on_data_loaded() - 更新 chart_widget
```

**架構評估**:
- ✅ **信號驅動**: 使用 PyQt5 信號槽機制異步更新
- ✅ **錯誤處理**: 完整的錯誤回調機制
- ✅ **狀態管理**: `_current_data` 和 `_is_data_loaded` 狀態追蹤

---

### 3️⃣ Loader 層 - 數據獲取邏輯

#### **Brake Performance Loader**
**檔案**: `modules/gui/all_drivers_brake_performance_analysis/brake_performance_loader.py`

```python
def load_data(self, **kwargs) -> bool:
    """Load brake performance data, fetching from API when needed."""
    
    # ✅ 步驟 1: 驗證參數
    if not self._validate_load_parameters(kwargs):
        self._error(tr("brake_perf_load_param_validation_failed", "載入參數驗證失敗"))
        self.load_error.emit(tr("brake_perf_load_param_invalid", "載入參數不正確"))
        return False
    
    # ✅ 步驟 2: 檢查本地 JSON 檔案
    existing = self._find_data_file(**kwargs)
    if not existing:
        # ✅ 步驟 3: 找不到 → 調用 API 獲取
        self._debug(tr("brake_perf_no_local_file", "找不到本地煞車性能檔案，準備透過 API 取得最新資料"))
        if not self._fetch_via_api_and_cache(**kwargs):
            return False
    
    # ✅ 步驟 4: 調用基類載入邏輯（讀取檔案 + 處理數據）
    return super().load_data(**kwargs)


def _fetch_via_api_and_cache(self, **kwargs) -> Optional[str]:
    """透過 API 獲取數據並緩存"""
    try:
        year = int(kwargs["year"])
        race = str(kwargs["race"])
        session = str(kwargs["session"])
    except (KeyError, TypeError, ValueError) as exc:
        self._error(tr("brake_perf_api_missing_params", "缺少必要參數，無法呼叫 API: {error}").format(error=str(exc)))
        self.load_error.emit(tr("brake_perf_load_missing_params", "缺少必要參數，無法載入煞車性能分析"))
        return None
    
    params = {
        "function_id": 34,  # ✅ Brake Performance 功能 ID
        "year": year,
        "race": race,
        "session": session,
    }
    
    endpoint = f"{self._api_base_url}/api/v2/analysis/execute"
    self.status_changed.emit(tr("brake_perf_loading_via_api", "透過 API 載入全部車手煞車性能資料..."))
    self.load_progress.emit(25)
    
    try:
        # ✅ 發送 API 請求
        response = requests.post(
            endpoint,
            params=params,
            timeout=self._api_timeout,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        self._error(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
        # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
        self._debug("💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接")
        return None
    
    if not isinstance(payload, dict) or not payload.get("success", False):
        message = payload.get("message") if isinstance(payload, dict) else tr("brake_perf_unknown_error", "未知錯誤")
        self._error(tr("brake_perf_api_return_failed", "API 返回失敗: {message}").format(message=message))
        # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
        self._debug("💡 提示: API 響應異常，請檢查後端服務狀態")
        return None
    
    self._last_api_payload = payload
    
    # ✅ 寫入緩存
    output_path = self._write_payload_to_cache(payload, year, race, session)
    if output_path:
        self.load_progress.emit(60)
        return output_path
    
    # ⚠️ [API-ONLY 模式修正] 儲存失敗不影響數據使用，不發送 load_error
    self._error(tr("brake_perf_save_error", "儲存 API 結果時發生錯誤"))
    self._debug("💡 數據已成功獲取但未能寫入本地緩存，不影響使用")
    return None
```

#### **Speed Loader**
**檔案**: `modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py`

```python
def load_data(self, **kwargs) -> bool:
    """Load straight-line speed data, fetching from API when needed."""
    
    # ✅ 完全相同的流程
    if not self._validate_load_parameters(kwargs):
        self._error(tr("straight_speed_load_param_validation_failed", "載入參數驗證失敗"))
        self.load_error.emit(tr("straight_speed_load_param_invalid", "載入參數不正確"))
        return False
    
    existing = self._find_data_file(**kwargs)
    if not existing:
        self._debug(tr("straight_speed_no_local_file", "找不到本地直線速度檔案，準備透過 API 取得最新資料"))
        if not self._fetch_via_api_and_cache(**kwargs):
            return False
    
    return super().load_data(**kwargs)


def _fetch_via_api_and_cache(self, **kwargs) -> Optional[str]:
    """透過 API 獲取數據並緩存"""
    # ✅ 唯一差異: function_id 不同
    params = {
        "function_id": 48,  # ✅ Speed Analysis 功能 ID
        "year": year,
        "race": race,
        "session": session,
    }
    
    # ✅ 其他邏輯完全相同
    # - API 請求
    # - 錯誤處理（不發送 load_error 彈窗）
    # - 緩存寫入
```

**架構評估**:
- ✅ **API 優先**: 本地檔案不存在時自動調用 API
- ✅ **緩存機制**: API 成功後寫入 `json/` 目錄緩存
- ✅ **錯誤處理**: API 失敗不彈窗，僅記錄日誌（API-ONLY 模式修正）
- ✅ **功能 ID**: Brake=34, Speed=48

---

## 🔄 Race 更換完整流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│  使用者操作: 在 GUI 中選擇新的 Race                                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  Module.update_parameters(year, race, session)                  │
│  - 更新 self.current_year/race/session                          │
│  - 同步更新 self._brake_core.year/race/session                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  MDI.load_initial_data()                                        │
│  - 調用 self.data_manager.load_data(year, race, session)        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  Loader.load_data(**kwargs)                                     │
│  1. _validate_load_parameters() - 驗證參數                       │
│  2. _find_data_file() - 檢查本地 JSON                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                ┌───────┴───────┐
                │               │
            找到檔案          找不到檔案
                │               │
                │               ▼
                │   ┌─────────────────────────────────────────┐
                │   │  _fetch_via_api_and_cache()             │
                │   │  - 構建 API 請求參數                     │
                │   │  - POST /api/v2/analysis/execute        │
                │   │  - function_id: 34 (Brake) / 48 (Speed) │
                │   └─────────────┬───────────────────────────┘
                │                 │
                │         ┌───────┴───────┐
                │         │               │
                │     API 成功         API 失敗
                │         │               │
                │         ▼               ▼
                │   ┌─────────┐     ┌─────────────┐
                │   │ 寫入緩存  │     │ 記錄錯誤日誌  │
                │   │ json/   │     │ (不彈窗)    │
                │   └─────┬───┘     └─────────────┘
                │         │
                └─────────┴─────────┐
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────┐
        │  UniversalDataLoader.load_data() (基類)                 │
        │  - _read_json_file() - 讀取 JSON 檔案                    │
        │  - _validate_data_format() - 驗證數據格式                │
        │  - _process_data() - 處理嵌套的 data.data 結構           │
        └───────────────────────┬─────────────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │  發送信號: data_loaded.emit(processed_data)              │
        └───────────────────────┬─────────────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │  MDI._on_data_loaded(data)                              │
        │  - 更新 self._current_data                              │
        │  - 調用 self.chart_widget.update_data(data)             │
        └───────────────────────┬─────────────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │  TableWidget.update_data(data)                          │
        │  - 清空舊數據                                            │
        │  - 填充新數據                                            │
        │  - 更新表格視圖                                          │
        └─────────────────────────────────────────────────────────┘
```

---

## 🔬 關鍵機制深度分析

### 1. **參數同步機制**

**問題**: Module 層和 MDI 層都持有 year/race/session 參數，如何保持一致？

**解決方案**:
```python
# Module 層 (外層)
self.current_year = year
self.current_race = race
self.current_session = session

# MDI 層 (核心)
self._brake_core.year = self.current_year
self._brake_core.race = self.current_race
self._brake_core.session = self.current_session

# ✅ 採用級聯同步: Module → MDI → Loader
# ✅ update_parameters() 時自動同步所有層級
```

**評估**:
- ✅ **清晰**: 外層控制內層，單向數據流
- ⚠️ **重複**: 參數在兩層都存儲，可能不一致
- 💡 **改進建議**: 考慮使用屬性代理，避免重複存儲

---

### 2. **本地緩存 vs API 獲取**

**邏輯**:
```python
existing = self._find_data_file(**kwargs)
if not existing:
    # 找不到本地檔案 → 調用 API
    self._fetch_via_api_and_cache(**kwargs)

# 無論是否調用 API，最終都調用基類載入
return super().load_data(**kwargs)
```

**檔案搜索模式**:
```python
def _build_filename_patterns(self, **kwargs) -> List[str]:
    return [
        f"all_drivers_brake_performance_{year}_{race}_{session}.json",
        f"all_drivers_brake_performance_{year}_{race_slug}_{session_slug}.json",
        f"all_drivers_brake_performance_*_{race}_{session}.json",
        f"brake_performance_{year}_{race}_{session}.json",
        # ✅ 支持多種命名格式
        # ✅ 支持萬用字元 (*)
    ]
```

**API 請求參數**:
```python
params = {
    "function_id": 34,  # Brake Performance
    "year": 2025,
    "race": "China",
    "session": "R",
}

endpoint = "https://api.f1telemetrystationpro.org/api/v2/analysis/execute"
# 或本地開發: "http://localhost:8000/api/v2/analysis/execute"
```

**評估**:
- ✅ **智能緩存**: 優先使用本地檔案，減少 API 調用
- ✅ **自動回退**: 本地不存在時自動調用 API
- ✅ **容錯性**: API 失敗不彈窗，僅記錄日誌

---

### 3. **數據格式處理**

**API 返回的嵌套結構**:
```json
{
  "success": true,
  "message": "分析完成",
  "function_id": "34",
  "data": {                          // 第一層 data
    "data": {                        // 第二層 data (嵌套)
      "metadata": {...},
      "driver_brakes": [...],
      "reference_brake_zone": {...}
    }
  }
}
```

**處理邏輯**:
```python
def _process_data(self, raw_data: Any) -> Dict[str, Any]:
    first_layer = raw_data.get("data", {})
    
    # ✅ 檢查是否有嵌套的第二層 data
    if isinstance(first_layer, dict) and "data" in first_layer:
        payload = first_layer.get("data", {})  # 取第二層
    else:
        payload = first_layer  # 兼容舊格式（沒有嵌套）
    
    # ✅ 提取實際數據
    processed = {
        "metadata": payload.get("metadata") or {},
        "driver_brakes": payload.get("driver_brakes") or [],
        "reference_brake_zone": payload.get("reference_brake_zone") or {},
        "summary": payload.get("summary") or {},
        "chart_data": payload.get("chart_data"),
        "raw_payload": raw_data,
    }
    return processed
```

**評估**:
- ✅ **向後兼容**: 支持嵌套和非嵌套兩種格式
- ✅ **健壯性**: 使用 `.get()` 避免 KeyError
- ✅ **完整性**: 保留原始 raw_payload 供調試

---

### 4. **錯誤處理機制**

**API-ONLY 模式錯誤處理**:
```python
try:
    response = requests.post(endpoint, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
except Exception as exc:
    self._error(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
    # ⚠️ [重要] 不發送 load_error.emit() 信號
    # ✅ 只記錄日誌，不彈窗打擾使用者
    self._debug("💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接")
    return None
```

**為什麼不彈窗？**
- ✅ **API-ONLY 模式**: API 失敗是預期的正常情況（例如網絡斷線、後端維護）
- ✅ **使用者體驗**: 避免頻繁彈窗打擾
- ✅ **替代方案**: 使用者可以手動執行 CLI 生成 JSON，或等待 API 恢復

**對比舊版本**:
```python
# ❌ 舊版本 (已移除): 每次 API 失敗都彈窗
self.load_error.emit("API 返回失敗")
# → QMessageBox.critical() 彈窗
# → 使用者體驗差

# ✅ 新版本 (API-ONLY): 只記錄日誌
self._error("API 載入失敗: ...")
self._debug("💡 提示: ...")
# → 不彈窗，僅控制台輸出
# → 使用者體驗改善
```

---

## 📊 兩個模組的差異對比

| 特性 | Brake Performance | Straight Line Speed | 說明 |
|------|-------------------|---------------------|------|
| **Module 類別** | `AllDriversBrakePerformanceModule` | `AllDriversStraightLineSpeedModule` | 實作 `IAnalysisModule` |
| **MDI 類別** | `AllDriversBrakePerformanceMDI` | `AllDriversStraightLineSpeedMDI` | 繼承 `UniversalAnalysisMDI` |
| **Loader 類別** | `BrakePerformanceDataLoader` | `StraightLineSpeedDataLoader` | 繼承 `UniversalDataLoader` |
| **CLI 功能 ID** | `34` | `48` | API 請求參數 |
| **數據欄位** | `driver_brakes` | `driver_speeds` | JSON 主要數據鍵 |
| **參考數據** | `reference_brake_zone` | `reference_segment` | 硬編碼範圍資訊 |
| **視圖組件** | `AllDriversBrakePerformanceTableWidget` | `AllDriversStraightLineSpeedTableWidget` | QTableWidget |
| **統計面板** | ❌ 已取消 | ❌ 已取消 | 兩者都不創建統計面板 |
| **國際化** | ✅ 完整支援 `tr()` | ⚠️ 部分支援 | Brake 更完整 |

**架構一致性**: ✅ **100% 一致**

---

## 🐛 潛在問題與改進建議

### ⚠️ **問題 1: 參數不一致風險**

**現狀**:
```python
# Module 層
self.current_year = "2025"
self.current_race = "China"

# MDI 層
self._brake_core.year = "2025"
self._brake_core.race = "China"
```

**問題**: 兩層都存儲相同的參數，可能不同步

**建議**:
```python
# 選項 A: 使用屬性代理
@property
def current_year(self):
    return self._brake_core.year if self._brake_core else self._year

@current_year.setter
def current_year(self, value):
    if self._brake_core:
        self._brake_core.year = value
    self._year = value

# 選項 B: 完全移除 Module 層參數，直接訪問 MDI
def update_parameters(self, year=None, race=None, session=None, **kwargs):
    if self._brake_core:
        if year: self._brake_core.year = str(year)
        if race: self._brake_core.race = race
        if session: self._brake_core.session = session
        self._brake_core.load_initial_data()
```

---

### ⚠️ **問題 2: Race 更換時舊數據未清空**

**現狀**:
```python
def _on_data_loaded(self, data: Dict[str, Any]):
    self._current_data = data  # 直接覆蓋
    self._is_data_loaded = True
    
    if self.chart_widget:
        self.chart_widget.update_data(data)  # 表格自行處理清空
```

**潛在問題**: 如果表格更新失敗，可能顯示舊數據

**建議**:
```python
def _on_data_loaded(self, data: Dict[str, Any]):
    # ✅ 先清空舊數據
    self._current_data = None
    self._is_data_loaded = False
    
    if self.chart_widget:
        self.chart_widget.clear()  # 確保清空
    
    # ✅ 再載入新數據
    self._current_data = data
    self._is_data_loaded = True
    
    if self.chart_widget:
        self.chart_widget.update_data(data)
```

---

### ⚠️ **問題 3: API 失敗後無法重試**

**現狀**:
```python
if not self._fetch_via_api_and_cache(**kwargs):
    return False  # API 失敗 → load_data 返回 False

# ❌ 使用者需要手動重新選擇 race 才能重試
```

**建議**:
```python
# 選項 A: 添加重試按鈕
def add_retry_button(self):
    btn = QPushButton("重新載入數據")
    btn.clicked.connect(lambda: self.load_initial_data())
    self.layout.addWidget(btn)

# 選項 B: 自動重試機制
def _fetch_via_api_and_cache(self, **kwargs) -> Optional[str]:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(...)
            return output_path
        except Exception as exc:
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待 2 秒後重試
                continue
            else:
                self._error("API 載入失敗（已重試 3 次）")
                return None
```

---

### ✅ **優點評估**

**架構優點**:
1. ✅ **統一架構**: 兩個模組完全一致，易於維護
2. ✅ **清晰分層**: Module → MDI → Loader 職責分明
3. ✅ **信號驅動**: 異步數據載入，不阻塞 UI
4. ✅ **API 優先**: 自動調用 API 獲取最新數據
5. ✅ **智能緩存**: 本地優先，減少 API 調用
6. ✅ **錯誤容錯**: API 失敗不彈窗，使用者體驗佳

**代碼品質**:
1. ✅ **國際化**: Brake 模組完整支援 `tr()` 翻譯
2. ✅ **類型提示**: 使用 `Optional[str]`、`Dict[str, Any]` 等
3. ✅ **日誌完整**: 每個步驟都有 `print` 日誌輸出
4. ✅ **異常處理**: `try-except` 包裹關鍵邏輯

---

## 📝 總結與建議

### 🎯 核心結論

**All Drivers Speed 和 Brake Performance 模組採用完全一致的 Race 更換機制**:

1. **觸發**: `Module.update_parameters(year, race, session)`
2. **同步**: Module → MDI → Loader 三層級聯更新
3. **載入**: 本地 JSON 優先，找不到則調用 API
4. **處理**: API 返回 → 緩存寫入 → 數據處理 → 信號發送
5. **更新**: MDI 接收信號 → 更新表格視圖

**數據流**: 使用者操作 → Module → MDI → Loader → API/JSON → Loader → MDI → TableWidget

---

### 💡 改進建議優先級

**🔴 高優先級**:
1. **添加重試機制**: API 失敗後允許使用者手動或自動重試
2. **清空舊數據**: Race 更換時確保先清空舊數據再載入新數據

**🟡 中優先級**:
3. **參數統一管理**: 使用屬性代理避免 Module/MDI 層參數重複
4. **Speed 國際化**: 補齊 Speed 模組的 `tr()` 翻譯支援

**🟢 低優先級**:
5. **進度提示**: 添加載入進度條或狀態文字
6. **緩存管理**: 提供清除舊緩存的 UI 功能

---

## 📚 相關檔案清單

**Brake Performance 模組**:
- `modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_module.py`
- `modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_mdi.py`
- `modules/gui/all_drivers_brake_performance_analysis/brake_performance_loader.py`
- `modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_table_widget.py`

**Speed 模組**:
- `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_module.py`
- `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_mdi.py`
- `modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py`
- `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`

**基類**:
- `modules/gui/base/universal_analysis_mdi_base.py`
- `modules/gui/base/universal_data_loader_base.py`
- `modules/gui/interfaces/analysis_module.py`

**CLI 後端**:
- `CLI_modules/cli/analyzer/brake_performance_analyzer.py` (Function 34)
- `CLI_modules/cli/analyzer/straight_line_speed_analyzer.py` (Function 48)

---

**報告完成時間**: 2025-10-19  
**調查深度**: ✅ 完整  
**架構一致性**: ✅ 100% 一致  
**關鍵發現**: Race 更換機制採用 Module → MDI → Loader 三層級聯 + API 優先 + 智能緩存
