# Historical Track Map vs Ideal Lap Ranking Table - 逐行比對報告

**日期**: 2025-11-11  
**目的**: 根據反幻覺編碼五原則，逐行驗證 Historical Track Map 是否完全遵循 Ideal Lap Ranking Table 的參考實現

---

## 🎯 反幻覺編碼五原則宣告

1. ❌ **禁止幻覺編碼** - 必須先驗證再編寫
2. ✅ **模組資料夾優先** - 複用現有功能
3. ✅ **通用模組優先** - 統一架構模式
4. ✅ **模組多國語言化** - 使用 `tr()` 函數
5. ✅ **print 輸出會被 logger 導出**

---

## 📊 逐行比對清單

### 1. **API Worker 類別定義**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| 類別名稱 | `IdealLapRankingApiWorker` | `HistoricalTrackMapApiWorker` | ✅ 一致 |
| 繼承基類 | `QThread` | `QThread` | ✅ 一致 |
| 信號定義 | `progress`, `success`, `failure` | `progress`, `success`, `failure` | ✅ 一致 |
| `__init__` 參數 | `params`, `base_url`, `timeout` | `base_url`, `params`, `timeout`, `parent` | ⚠️ **參數順序不同** |
| 預設 base_url | `"http://localhost:8000"` | `"http://localhost:8000"` | ✅ 一致 |
| 預設 timeout | `60.0` | `60.0` | ✅ 一致 |

**🔴 發現問題 1**: API Worker 的 `__init__` 參數順序不同

**Ideal Lap Ranking**:
```python
def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
```

**Historical Track Map**:
```python
def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 60.0, parent=None):
```

**影響**: 調用時必須使用關鍵字參數，否則會參數錯位。

---

### 2. **API Worker `run()` 方法**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| API 端點 | `/api/v2/analysis/execute` | `/api/v2/analysis/execute` | ✅ 一致 |
| Function ID | `53` | `100` | ✅ 正確（不同功能） |
| 參數構建 | `query_params = {"function_id": 53, "year": ..., "race": ..., "session": ...}` | `query_params = {"function_id": 100, "year": ..., "race": ..., "session": ...}` | ✅ 一致 |
| HTTP 方法 | `requests.post()` | `requests.post()` | ✅ 一致 |
| 進度信號 | `emit(20)`, `emit(70)`, `emit(90)`, `emit(100)` | `emit(20)`, `emit(70)`, `emit(90)`, `emit(100)` | ✅ 一致 |
| 錯誤處理 | `try-except-finally` | `try-except-finally` | ✅ 一致 |
| 回應驗證 | `raise_for_status()` → `payload.get("success")` → `payload.get("data")` | `raise_for_status()` → `payload.get("success")` → `payload.get("data")` | ✅ 一致 |
| 元數據構建 | `meta = {"source": ..., "latency_ms": ..., "request_id": ...}` | `meta = {"source": ..., "latency_ms": ..., "request_id": ...}` | ✅ 一致 |
| 成功信號 | `self.success.emit({"data": data, "meta": meta})` | `self.success.emit({"data": data, "meta": meta})` | ✅ 一致 |

---

### 3. **MDI 類別定義**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| 類別名稱 | `IdealLapRankingTableMDI` | `HistoricalTrackMapMDI` | ✅ 一致 |
| 繼承基類 | `UniversalAnalysisMDI` | `UniversalAnalysisMDI` | ✅ 一致 |
| 類型註冊 | `"ideal_lap_ranking"` | `"historical_track_map"` | ✅ 正確 |
| 註冊方法 | `ensure_registered()` | `ensure_registered()` | ✅ 一致 |
| Config 結構 | `AnalysisMDIConfig(...)` | `AnalysisMDIConfig(...)` | ✅ 一致 |
| `requires_driver_params` | `False` | `False` | ✅ 一致 |
| `requires_lap_params` | `False` | `False` | ✅ 一致 |

---

### 4. **MDI `__init__` 方法**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| 調用 `ensure_registered()` | ✅ 有 | ✅ 有 | ✅ 一致 |
| 調用 `super().__init__()` | ✅ 有 | ✅ 有 | ✅ 一致 |
| 初始化參數 | `self.year = None`, `self.race = None`, `self.session = None` | `self.year = 2024`, `self.race = None`, `self.session = "R"` | ⚠️ **預設值不同** |
| 狀態變數 | `self._current_data = None`, `self._is_data_loaded = False` | `self._is_data_loaded = False`, `self._current_flags_data = None` | ✅ 功能一致 |

**🔴 發現問題 2**: 預設值設定不一致

**Ideal Lap Ranking**:
```python
self.year = None
self.race = None
self.session = None
```

**Historical Track Map**:
```python
self.year = 2024  # ⚠️ 硬編碼預設值
self.race = None
self.session = "R"  # ⚠️ 硬編碼預設值
```

**原則違反**: **原則 1 - 禁止假設性編程**。應該使用 `None` 並在 `initialize_module` 中從基類獲取。

---

### 5. **`initialize_module()` 方法**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| 驗證 `current_year` | ✅ 有 (`hasattr(self, 'current_year')`) | ❌ **無驗證** | 🔴 **缺失** |
| 驗證 `current_race` | ✅ 有 (`hasattr(self, 'current_race')`) | ❌ **無驗證** | 🔴 **缺失** |
| 驗證 `current_session` | ✅ 有 (`hasattr(self, 'current_session')`) | ❌ **無驗證** | 🔴 **缺失** |
| 參數設置 | `self.year = str(self.current_year)` | ❌ **無參數設置** | 🔴 **缺失** |
| 調用 `super().initialize_module()` | ✅ 有 | ✅ 有 | ✅ 一致 |
| 驗證 `chart_widget` | ✅ 有 (`if not self.chart_widget`) | ❌ **無驗證** | 🔴 **缺失** |
| 驗證 `data_manager` | ✅ 有 (`if not self.data_manager`) | ❌ **無驗證** | 🔴 **缺失** |
| 調用 `load_initial_data()` | ✅ 有 | ✅ 有 | ✅ 一致 |

**🔴 發現問題 3**: Historical Track Map 缺少必要的參數驗證和設置邏輯

**Ideal Lap Ranking 的正確實現**:
```python
def initialize_module(self, parent_widget=None, **kwargs) -> bool:
    # 驗證必要屬性
    if not hasattr(self, 'current_year') or not self.current_year:
        print(f"[IDEAL_LAP_MDI] ❌ 缺少 current_year 屬性")
        return False
        
    if not hasattr(self, 'current_race') or not self.current_race:
        print(f"[IDEAL_LAP_MDI] ❌ 缺少 current_race 屬性")
        return False
        
    if not hasattr(self, 'current_session') or not self.current_session:
        print(f"[IDEAL_LAP_MDI] ❌ 缺少 current_session 屬性")
        return False
    
    # 設置參數
    self.year = str(self.current_year)
    self.race = self.current_race
    self.session = self.current_session
```

**Historical Track Map 的實現** (缺失驗證):
```python
def initialize_module(self, parent_widget=None, **kwargs) -> bool:
    # ❌ 沒有驗證 current_year, current_race, current_session
    # ❌ 沒有設置 self.year, self.race, self.session
    
    # 直接創建 UI...
```

---

### 6. **`load_initial_data()` 方法**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| 狀態更新 | `self.lbl_control_status.setText("正在從 API 載入資料...")` | `self.info_label.setText("Loading from API...")` | ✅ 功能一致 |
| API 參數構建 | `api_params = {"year": self.year, "race": self.race, "session": self.session}` | `api_params = {"year": year, "race": race, "session": session}` | ⚠️ **來源不同** |
| Worker 創建 | `self.api_worker = IdealLapRankingApiWorker(params=api_params, base_url=..., timeout=60.0)` | `self.api_worker = HistoricalTrackMapApiWorker(base_url=..., params=api_params, timeout=60.0, parent=self)` | ⚠️ **參數順序不同** |
| 信號連接 | `progress`, `success`, `failure` | `progress`, `success`, `failure` | ✅ 一致 |
| 連接類型 | **無指定** (默認 `AutoConnection`) | **無指定** (默認 `AutoConnection`) | ✅ 一致 |
| Worker 啟動 | `self.api_worker.start()` | `self.api_worker.start()` | ✅ 一致 |

**🔴 發現問題 4**: Historical Track Map 使用 `getattr()` 動態獲取參數

**Ideal Lap Ranking** (參考實現):
```python
def load_initial_data(self):
    # 直接使用已設置的參數
    api_params = {
        "year": self.year,  # ✅ 在 initialize_module 中已設置
        "race": self.race,
        "session": self.session
    }
```

**Historical Track Map** (當前實現):
```python
def load_initial_data(self):
    # ⚠️ 使用 getattr 動態獲取，因為沒有在 initialize_module 中設置
    year = getattr(self, 'current_year', self.year)  # ⚠️ 繞過驗證
    race = getattr(self, 'current_race', self.race)
    session = getattr(self, 'current_session', self.session)
    
    api_params = {
        "year": year,  # ❌ 可能是 None 或預設值
        "race": race,
        "session": session
    }
```

**原則違反**: **原則 1 - 禁止假設性編程**。應該在 `initialize_module` 中驗證和設置參數，而不是在 `load_initial_data` 中動態推測。

---

### 7. **API 回調處理**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| `_on_api_progress` | ✅ 有 | ✅ 有 | ✅ 一致 |
| `_on_api_success` | ✅ 有 | ✅ 有 | ✅ 一致 |
| `_on_api_failure` | ✅ 有 | ✅ 有 | ✅ 一致 |
| 數據驗證 | `if not isinstance(data, dict)` → `if "analysis_result" not in data` | `if not isinstance(api_data, dict)` → 自定義轉換 | ⚠️ **邏輯不同** |
| 數據轉換 | ❌ 無（直接使用 API 數據） | ✅ 有 (`_transform_api_data_to_gui_format`) | ⚠️ **額外邏輯** |
| 調用處理 | `self._on_data_loaded(data)` | `self._on_data_loaded(gui_data)` | ✅ 功能一致 |

**說明**: Historical Track Map 需要額外的數據轉換（API 格式 → GUI 格式），這是合理的，因為 Function 100 返回的數據結構與 GUI 期望不同。

---

### 8. **`_show_error()` 方法**

| 項目 | Ideal Lap Ranking | Historical Track Map | 狀態 |
|------|-------------------|---------------------|------|
| 方法定義 | ❌ **繼承自基類** | ✅ **自定義實現** | ⚠️ **不同** |
| 實現邏輯 | N/A (基類提供) | `QMessageBox.critical(parent, title, message)` | ✅ 正確 |

**Historical Track Map 的實現**:
```python
def _show_error(self, title: str, message: str):
    """顯示錯誤對話框"""
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)
```

**說明**: 因為 Historical Track Map 不繼承自 QWidget，所以需要自定義 `_show_error` 方法。這是正確的實現。

---

## 🔴 關鍵問題總結

### 問題 1: API Worker 參數順序不一致

**位置**: `HistoricalTrackMapApiWorker.__init__`

**原因**: 參數順序與 Ideal Lap Ranking 不同，可能導致位置參數錯位。

**建議修復**: 統一為 `(params, base_url, timeout, parent)` 順序。

---

### 問題 2: 硬編碼預設值

**位置**: `HistoricalTrackMapMDI.__init__`

**違反原則**: **原則 1 - 禁止假設性編程**

**現有代碼**:
```python
self.year = 2024  # ❌ 硬編碼
self.session = "R"  # ❌ 硬編碼
```

**建議修復**:
```python
self.year = None  # ✅ 等待 initialize_module 設置
self.race = None
self.session = None
```

---

### 問題 3: 缺少參數驗證邏輯（最嚴重）

**位置**: `HistoricalTrackMapMDI.initialize_module()`

**違反原則**: **原則 1 - 禁止假設性編程**

**缺失的邏輯**:
1. ❌ 沒有驗證 `current_year` 是否存在
2. ❌ 沒有驗證 `current_race` 是否存在
3. ❌ 沒有驗證 `current_session` 是否存在
4. ❌ 沒有設置 `self.year`, `self.race`, `self.session`

**建議修復**: 完全複製 Ideal Lap Ranking 的驗證邏輯。

---

### 問題 4: 使用 `getattr()` 繞過驗證

**位置**: `HistoricalTrackMapMDI.load_initial_data()`

**違反原則**: **原則 1 - 禁止假設性編程**

**現有代碼**:
```python
year = getattr(self, 'current_year', self.year)  # ❌ 假設屬性存在
race = getattr(self, 'current_race', self.race)
session = getattr(self, 'current_session', self.session)
```

**問題**: 如果 `current_*` 不存在，回退到 `self.year` (可能是 `None` 或硬編碼值)，導致 API 調用失敗。

**建議修復**: 在 `initialize_module` 中驗證和設置參數，然後直接使用 `self.year`。

---

## ✅ 修復清單

### 修復 1: 統一 API Worker 參數順序

**文件**: `historical_track_map_data_loader.py`

**修改前**:
```python
def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 60.0, parent=None):
```

**修改後**:
```python
def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
```

---

### 修復 2: 移除硬編碼預設值

**文件**: `historical_track_map_mdi.py`

**修改前**:
```python
self.year = 2024
self.race = None
self.session = "R"
```

**修改後**:
```python
self.year = None
self.race = None
self.session = None
```

---

### 修復 3: 添加完整的參數驗證邏輯

**文件**: `historical_track_map_mdi.py`

**在 `initialize_module()` 開頭添加**:
```python
def initialize_module(self, parent_widget=None, **kwargs) -> bool:
    print("[HISTORICAL_TRACK_MAP_MDI] initialize_module 開始...")
    
    try:
        # ✅ 驗證必要屬性（完全複製 Ideal Lap Ranking）
        if not hasattr(self, 'current_year') or not self.current_year:
            print(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 缺少 current_year 屬性")
            return False
            
        if not hasattr(self, 'current_race') or not self.current_race:
            print(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 缺少 current_race 屬性")
            return False
            
        if not hasattr(self, 'current_session') or not self.current_session:
            print(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 缺少 current_session 屬性")
            return False
        
        # ✅ 設置參數（完全複製 Ideal Lap Ranking）
        self.year = str(self.current_year)
        self.race = self.current_race
        self.session = self.current_session
        
        print(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 參數已設置: {self.year} {self.race} {self.session}")
        
        # 繼續原有邏輯...
```

---

### 修復 4: 簡化 `load_initial_data()` 參數獲取

**文件**: `historical_track_map_mdi.py`

**修改前**:
```python
def load_initial_data(self):
    # ⚠️ 使用 getattr 動態獲取
    year = getattr(self, 'current_year', self.year)
    race = getattr(self, 'current_race', self.race)
    session = getattr(self, 'current_session', self.session)
    
    api_params = {
        "year": year,
        "race": race,
        "session": session
    }
```

**修改後**:
```python
def load_initial_data(self):
    # ✅ 直接使用已驗證的參數（完全複製 Ideal Lap Ranking）
    print(f"[HISTORICAL_TRACK_MAP_MDI] 📋 參數: {self.year} {self.race} {self.session}")
    
    api_params = {
        "year": self.year,  # ✅ 已在 initialize_module 驗證
        "race": self.race,
        "session": self.session,
        "force_refresh": False
    }
```

---

## 📌 總結

### 符合原則的部分 ✅

1. ✅ **API Worker 架構**: 完全遵循 Ideal Lap Ranking 的設計
2. ✅ **信號連接**: 使用相同的 `progress`, `success`, `failure` 信號
3. ✅ **錯誤處理**: 使用 `try-except-finally` 結構
4. ✅ **API 端點**: 正確使用 `/api/v2/analysis/execute`
5. ✅ **元數據處理**: 完全一致的元數據結構

### 違反原則的部分 🔴

1. 🔴 **硬編碼預設值**: 違反原則 1（禁止假設性編程）
2. 🔴 **缺少參數驗證**: 違反原則 1（必須先驗證再使用）
3. 🔴 **使用 getattr 繞過驗證**: 違反原則 1（假設屬性存在）
4. 🔴 **參數順序不一致**: 違反原則 3（統一架構模式）

### 建議優先級

1. **P0 (最高)**: 修復 3 - 添加參數驗證邏輯
2. **P0 (最高)**: 修復 4 - 移除 getattr 繞過邏輯
3. **P1 (高)**: 修復 2 - 移除硬編碼預設值
4. **P2 (中)**: 修復 1 - 統一 API Worker 參數順序

---

## 🎯 下一步行動

執行所有 4 項修復，確保 Historical Track Map 完全遵循 Ideal Lap Ranking 的參考實現，消除所有假設性編程。
