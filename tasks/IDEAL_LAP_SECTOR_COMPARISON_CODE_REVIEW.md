# 理想圈分段對比 vs 理想圈排名表格 - 完整逐行對比報告

## 📋 對比摘要

對比兩個模組的實現差異，找出導致運行錯誤的根本原因。

- **參考模組**: `ideal_lap_ranking_table` ✅ (正常運行)
- **新模組**: `ideal_lap_sector_comparison` ❌ (連續兩次錯誤)

---

## ❌ 當前錯誤

### 錯誤 1: AttributeError
```python
# Line 504 in ideal_lap_sector_comparison_mdi.py
self.chart_widget.update_chart(display_data)
# ❌ AttributeError: 'IdealLapSectorComparisonWidget' object has no attribute 'update_chart'
```

### 錯誤 2: TypeError
```python
# Line 419 in ideal_lap_sector_comparison_mdi.py
QMessageBox.warning(
    self,  # ❌ self 是 IdealLapSectorComparisonMDI，不是 QWidget
    "資料載入失敗",
    ...
)
# TypeError: QMessageBox.warning() argument 1 has unexpected type 'IdealLapSectorComparisonMDI'
```

---

## 🔍 逐行對比分析

### 1. MDI 檔案對比

#### 1.1 API Worker 實現 ✅ (基本一致)

**ranking_table_mdi.py** (Lines 56-145):
```python
class IdealLapRankingApiWorker(QThread):
    """理想圈排名 API 請求工作執行緒"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        super().__init__()
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        # ... (API 調用邏輯)
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        query_params: Dict[str, Any] = {
            "function_id": 53,  # ✅ Function 53
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
        }
        # ... (請求處理)
```

**sector_comparison_mdi.py** (Lines 49-168):
```python
class IdealLapSectorComparisonApiWorker(QThread):
    """理想圈分段對比 API 請求工作執行緒"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        super().__init__()
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        # ... (API 調用邏輯)
        endpoint = f"{self.base_url}/api/v2/analysis/execute"
        query_params: Dict[str, Any] = {
            "function_id": 53,  # ✅ Function 53
            "year": int(self.params.get("year")),
            "race": self.params.get("race"),
            "session": self.params.get("session"),
        }
        # ... (請求處理)
```

**✅ 結論**: API Worker 實現基本一致，無明顯問題。

---

#### 1.2 錯誤處理方式 ❌ (關鍵差異)

**ranking_table_mdi.py** (Lines 392-401):
```python
@pyqtSlot(str)
def _on_load_error(self, error_msg: str):
    """資料載入錯誤回調"""
    print(f"❌ [IDEAL_LAP_MDI] 載入錯誤: {error_msg}")
    
    # ✅ 使用基類的 _show_error() 方法
    self._show_error(
        "載入失敗",
        f"無法載入理想圈排名資料:\n\n{error_msg}\n\n請檢查網路連接或手動執行 CLI。"
    )
```

**sector_comparison_mdi.py** (Lines 412-427):
```python
@pyqtSlot(str)
def _on_load_error(self, error_msg: str):
    """資料載入錯誤回調"""
    print(f"❌ [SECTOR_COMPARISON_MDI] 載入錯誤: {error_msg}")
    
    # ❌ 直接使用 QMessageBox.warning()，self 不是 QWidget
    QMessageBox.warning(
        self,  # ❌ 類型錯誤！IdealLapSectorComparisonMDI 不是 QWidget
        "資料載入失敗",
        f"無法載入分段對比資料:\n\n{error_msg}\n\n"
        f"請檢查:\n"
        f"1. API 服務器是否運行\n"
        f"2. 參數是否正確 ({self.year} {self.race} {self.session})\n"
        f"3. JSON 檔案是否存在"
    )
```

**❌ 問題**: 
- ranking_table 使用 `self._show_error()` (基類方法)
- sector_comparison 錯誤地直接使用 `QMessageBox.warning(self, ...)`
- `self` 是 `UniversalAnalysisMDI` 實例，不是 `QWidget`，無法作為 QMessageBox 的父元件

**修正方案**:
```python
# ✅ 正確做法 1: 使用基類方法
self._show_error("載入失敗", error_msg)

# ✅ 正確做法 2: 使用 chart_widget 作為 parent
parent = self.chart_widget if hasattr(self, 'chart_widget') else None
QMessageBox.warning(parent, "標題", "訊息")
```

---

#### 1.3 API 成功回調 ❌ (方法調用錯誤)

**ranking_table_mdi.py** (Lines 483-510):
```python
@pyqtSlot(dict)
def _on_api_success(self, result: Dict[str, Any]):
    """API 請求成功"""
    try:
        print("[IDEAL_LAP_MDI] ✅ API 調用成功")
        
        # 提取數據和元數據
        data = result.get("data", {})
        meta = result.get("meta", {})
        
        # 驗證數據結構
        if not isinstance(data, dict):
            raise ValueError("API 返回的數據格式錯誤")
        
        if "analysis_result" not in data:
            raise ValueError("API 數據缺少 'analysis_result'")
        
        # ✅ 調用 _on_data_loaded() 處理數據
        self._on_data_loaded(data)
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status'):
            source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
            self.lbl_control_status.setText(f"✅ 已從 {source_label} 載入資料")
        
    except Exception as e:
        print(f"❌ [IDEAL_LAP_MDI] API 數據處理失敗: {e}")
        import traceback
        traceback.print_exc()
        self._on_api_failure(str(e))
```

**sector_comparison_mdi.py** (Lines 481-516):
```python
@pyqtSlot(dict)
def _on_api_success(self, result: Dict):
    """API 請求成功回調"""
    print("✅ [SECTOR_COMPARISON_API] API 請求成功")
    print(f"[DEBUG] API 返回數據鍵: {list(result.keys())}")
    
    try:
        # 提取實際數據（處理 API Worker 的包裝格式）
        api_data = result.get('data', result)
        print(f"[DEBUG] 實際數據鍵: {list(api_data.keys()) if isinstance(api_data, dict) else type(api_data)}")
        
        # 驗證數據格式
        if not self._validate_api_data(api_data):
            raise ValueError("API 返回數據格式無效")
        
        # 轉換為顯示格式
        display_data = self._transform_api_data_for_display(api_data)
        
        # ❌ 錯誤！調用不存在的方法 update_chart()
        if self.chart_widget:
            self.chart_widget.update_chart(display_data)  # ❌ AttributeError
            print("✅ [SECTOR_COMPARISON_MDI] 圖表已更新（API 數據）")
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
            self.lbl_control_status.setText("API 數據載入成功")
        
        # 保存當前數據
        self._current_data = display_data
        
    except Exception as e:
        print(f"❌ [SECTOR_COMPARISON_API] 數據處理失敗: {e}")
        traceback.print_exc()
        self._on_api_failure(f"數據處理錯誤: {str(e)}")
```

**❌ 問題**:
- ranking_table 調用 `self._on_data_loaded(data)` (存在的回調方法)
- sector_comparison 調用 `self.chart_widget.update_chart(display_data)` ❌ (不存在的方法)
- `IdealLapSectorComparisonWidget` 繼承 `UniversalChartWidget`，沒有 `update_chart()` 方法

**修正方案**:
```python
# ✅ 應該調用 _on_data_loaded() 處理數據
self._on_data_loaded(display_data)
```

---

#### 1.4 數據載入流程對比

**ranking_table_mdi.py**:
```
load_initial_data() 
  → 創建 API Worker
  → _on_api_success() 
    → _on_data_loaded(data)  ✅
      → 從 data 提取 ranking 和 summary
      → chart_widget.populate_table(ranking)  ✅ (方法存在)
      → chart_widget.update_statistics_panel(summary)  ✅ (方法存在)
```

**sector_comparison_mdi.py**:
```
load_initial_data() 
  → 創建 API Worker
  → _on_api_success() 
    → chart_widget.update_chart(display_data)  ❌ (方法不存在)
    → 保存 self._current_data
```

**❌ 問題**: 
- sector_comparison 完全跳過了 `_on_data_loaded()` 回調
- 直接嘗試調用不存在的 `update_chart()` 方法

---

#### 1.5 _show_error() 方法實現

**ranking_table_mdi.py** (Lines 625-638):
```python
def _show_error(self, title: str, message: str):
    """
    顯示錯誤對話框
    
    Args:
        title: 對話框標題
        message: 錯誤訊息
    """
    # ✅ MDI 不是 QWidget，需要使用 chart_widget 作為 parent
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)
```

**sector_comparison_mdi.py**:
```python
# ❌ 完全沒有 _show_error() 方法！
# 導致基類調用失敗
```

**❌ 問題**: 
- ranking_table 正確實現了 `_show_error()` 方法
- sector_comparison 完全缺少此方法
- 如果基類或其他方法調用 `self._show_error()`，會導致 AttributeError

---

### 2. Widget 檔案對比

#### 2.1 基類差異 ⚠️ (重要差異)

**IdealLapRankingTableWidget** (ranking_table_widget.py Line 41):
```python
class IdealLapRankingTableWidget(QWidget):
    """
    理想圈排名表格元件
    
    繼承自 QWidget，純粹的表格元件，不包含圖表功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... 初始化表格
```

**IdealLapSectorComparisonWidget** (sector_comparison_widget.py Line 25):
```python
class IdealLapSectorComparisonWidget(UniversalChartWidget):
    """
    理想圈分段對比圖表元件
    
    繼承自 UniversalChartWidget，專門用於繪製棒狀圖
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... 初始化圖表
```

**⚠️ 結論**: 
- ranking_table 使用 `QWidget` 基類（表格元件）
- sector_comparison 使用 `UniversalChartWidget` 基類（圖表元件）
- 基類不同，導致可用方法不同

---

#### 2.2 數據填充方法 ❌ (方法名稱不一致)

**IdealLapRankingTableWidget** (Lines 154-172):
```python
def populate_table(self, ranking_data: List[Dict[str, Any]]):
    """
    填充表格資料
    
    Args:
        ranking_data: 車手排名資料列表
    """
    try:
        self._ranking_data = ranking_data
        row_count = len(ranking_data)
        
        self.table.setSortingEnabled(False)
        self.table.setRowCount(row_count)
        
        for row, driver in enumerate(ranking_data):
            self._set_row_data(row, driver)
        
        self.table.setSortingEnabled(True)
        print(f"[TABLE_WIDGET] ✅ 已載入 {row_count} 位車手")
        
    except Exception as e:
        print(f"❌ 填充表格失敗: {e}")
```

**IdealLapSectorComparisonWidget**:
```python
# ❌ 沒有 populate_table() 方法！
# ❌ 沒有 update_chart() 方法！
# ✅ 有 draw_comparison_bars() 方法
def draw_comparison_bars(self, comparison_data: List[Dict], statistics: Dict = None):
    """繪製分段對比棒狀圖"""
    # ... (繪圖邏輯)
```

**❌ 問題**: 
- ranking_table 的數據填充方法叫 `populate_table()`
- sector_comparison 的數據填充方法叫 `draw_comparison_bars()`
- MDI 錯誤地調用不存在的 `update_chart()`

**修正方案**:
```python
# ❌ 錯誤調用
self.chart_widget.update_chart(display_data)

# ✅ 正確調用（方法 1）
self.chart_widget.draw_comparison_bars(
    display_data.get("comparison_data", []),
    display_data.get("statistics", {})
)

# ✅ 正確調用（方法 2）- 通過 _on_data_loaded()
self._on_data_loaded(display_data)
```

---

#### 2.3 統計面板更新方法

**IdealLapRankingTableWidget** (Lines 174-230):
```python
def update_statistics_panel(self, summary_data: Dict[str, Any]):
    """
    更新統計摘要面板
    
    Args:
        summary_data: 統計資料字典
    """
    try:
        self._summary_data = summary_data
        
        # 更新標籤
        total_drivers = summary_data.get("total_drivers", 20)
        self.lbl_total_drivers.setText(f"總車手數: {total_drivers}")
        
        # ... (更新其他統計標籤)
        
    except Exception as e:
        print(f"❌ 更新統計面板失敗: {e}")
```

**IdealLapSectorComparisonWidget**:
```python
# ❌ 沒有 update_statistics_panel() 方法！
# ✅ 統計面板在 SectorComparisonControlPanel 中
```

**⚠️ 結論**: 
- ranking_table 的統計面板在 Widget 內部
- sector_comparison 的統計面板在獨立的 ControlPanel 元件
- 架構設計不同，但不影響功能（只要正確調用）

---

#### 2.4 清空方法

**IdealLapRankingTableWidget** (Lines 232-236):
```python
def clear_table(self):
    """清空表格"""
    self.table.setRowCount(0)
    self._ranking_data = []
    print("[TABLE_WIDGET] 表格已清空")
```

**IdealLapSectorComparisonWidget**:
```python
# ❌ 沒有 clear_table() 方法！
# ❌ 沒有 clear_chart() 方法！
# ⚠️ UniversalChartWidget 可能有基類的清空方法，但未明確定義
```

**⚠️ 結論**: 
- ranking_table 提供 `clear_table()` 方法
- sector_comparison 缺少對應的清空方法
- 如果 MDI 調用 `self.chart_widget.clear_table()`，會導致 AttributeError

---

### 3. _on_data_loaded() 實現對比 ❌ (關鍵差異)

#### 3.1 ranking_table 的完整實現

**ranking_table_mdi.py** (Lines 371-391):
```python
@pyqtSlot(dict)
def _on_data_loaded(self, raw_data: Dict):
    """
    資料載入完成回調
    
    Args:
        raw_data: 來自 API 或本地 JSON 的原始資料
    """
    try:
        print("[IDEAL_LAP_MDI] ✅ 收到資料載入完成信號")
        
        # ✅ 驗證數據結構
        if not raw_data or not raw_data.get("analysis_result"):
            raise ValueError("資料格式不正確或缺少 'analysis_result'")
        
        result = raw_data["analysis_result"]
        ranking = result.get("ranking", [])
        summary = result.get("summary", {})
        
        print(f"[IDEAL_LAP_MDI] 📊 資料統計:")
        print(f"   - 車手數: {len(ranking)}")
        print(f"   - 總車手: {summary.get('total_drivers', 0)}")
        
        # ✅ 更新表格
        if self.chart_widget and hasattr(self.chart_widget, 'populate_table'):
            self.chart_widget.populate_table(ranking)
            self.chart_widget.update_statistics_panel(summary)
            print("[IDEAL_LAP_MDI] ✅ 表格已更新")
        
        self._current_data = raw_data
        
    except Exception as e:
        print(f"❌ [IDEAL_LAP_MDI] 資料處理失敗: {e}")
        import traceback
        traceback.print_exc()
        self._on_load_error(f"資料處理錯誤: {str(e)}")
```

#### 3.2 sector_comparison 的實現

**sector_comparison_mdi.py** (Lines 387-410):
```python
@pyqtSlot(dict)
def _on_data_loaded(self, data: Dict[str, Any]):
    """數據載入完成回調"""
    try:
        print("[SECTOR_COMPARISON_MDI] 收到資料載入完成信號")
        
        # ⚠️ 驗證邏輯不同
        if not data or not data.get("success"):
            error_msg = data.get("error", "未知錯誤") if data else "資料為空"
            self._on_load_error(f"資料載入失敗: {error_msg}")
            return
        
        self._current_data = data
        self._is_data_loaded = True
        
        # ✅ 提取數據
        comparison_data = data.get("comparison_data", [])
        statistics = data.get("statistics", {})
        
        print(f"[SECTOR_COMPARISON_MDI] 更新圖表，共 {len(comparison_data)} 位車手")
        
        # ✅ 正確調用圖表方法
        if self.chart_widget:
            self.chart_widget.draw_comparison_bars(comparison_data, statistics)
        
        # ✅ 更新統計面板
        if self.control_panel:
            self.control_panel.update_statistics(statistics)
        
        print("✅ [SECTOR_COMPARISON_MDI] 資料處理完成")
        
    except Exception as e:
        print(f"❌ [SECTOR_COMPARISON_MDI] 資料處理失敗: {e}")
        import traceback
        traceback.print_exc()
        self._on_load_error(f"資料處理錯誤: {str(e)}")
```

**⚠️ 對比結論**:
- ranking_table: 檢查 `analysis_result` 鍵，調用 `populate_table()` 和 `update_statistics_panel()`
- sector_comparison: 檢查 `success` 鍵，調用 `draw_comparison_bars()` ✅ (這裡是正確的)
- **問題**: `_on_api_success()` 沒有調用 `_on_data_loaded()`，直接調用不存在的 `update_chart()`

---

### 4. API 失敗回調對比

#### 4.1 ranking_table 的備援機制

**ranking_table_mdi.py** (Lines 518-555):
```python
@pyqtSlot(str)
def _on_api_failure(self, error_msg: str):
    """API 請求失敗 - 嘗試備援方案"""
    print(f"❌ [IDEAL_LAP_MDI] API 調用失敗: {error_msg}")
    
    # 嘗試本地 JSON 作為備援
    print("[IDEAL_LAP_MDI] 🔄 嘗試從本地 JSON 載入...")
    
    if hasattr(self, 'lbl_control_status'):
        self.lbl_control_status.setText("API 失敗，嘗試本地檔案...")
    
    # ✅ 檢查 data_loader 是否存在
    if not hasattr(self, 'data_loader'):
        print("❌ [IDEAL_LAP_MDI] 資料載入器未初始化")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText("❌ 載入失敗")
        # ✅ 使用 _show_error() 方法
        self._show_error("載入失敗", f"API 失敗且無法使用備援方案:\n{error_msg}")
        return
    
    # ✅ 使用資料載入器嘗試讀取本地 JSON
    success = self.data_loader.load_data(
        year=self.year,
        race=self.race,
        session=self.session
    )
    
    if not success:
        print("❌ [IDEAL_LAP_MDI] 本地 JSON 載入也失敗")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText("❌ API 和本地檔案都載入失敗")
        # ✅ 使用 _show_error() 方法
        self._show_error(
            "載入失敗",
            f"API 調用失敗:\n{error_msg}\n\n本地檔案也找不到。\n\n請檢查網路連接或手動執行 CLI 生成資料。"
        )
    else:
        print("[IDEAL_LAP_MDI] ✅ 成功從本地 JSON 載入")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText("⚠️ 從本地檔案載入（API 失敗）")
```

#### 4.2 sector_comparison 的備援機制

**sector_comparison_mdi.py** (Lines 518-564):
```python
@pyqtSlot(str)
def _on_api_failure(self, error_msg: str):
    """API 請求失敗回調（回退到本地 JSON）"""
    print(f"⚠️ [SECTOR_COMPARISON_API] API 請求失敗: {error_msg}")
    print("🔄 [SECTOR_COMPARISON_MDI] 嘗試回退到本地 JSON 檔案...")
    
    # 更新狀態
    if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
        self.lbl_control_status.setText("API 失敗，嘗試本地 JSON...")
    
    # ⚠️ 使用 data_manager 而非 data_loader（名稱不一致）
    if self.data_manager:
        try:
            self.data_manager.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
            print("✅ [SECTOR_COMPARISON_MDI] 本地 JSON 載入成功（回退模式）")
            
            if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
                self.lbl_control_status.setText("已載入本地 JSON（API 失敗回退）")
                
        except Exception as fallback_error:
            print(f"❌ [SECTOR_COMPARISON_MDI] 本地 JSON 載入也失敗: {fallback_error}")
            
            # ❌ 完全失敗 - 使用 QMessageBox.critical(self, ...)
            QMessageBox.critical(
                self,  # ❌ 類型錯誤！
                "數據載入完全失敗",
                f"API 和本地 JSON 載入均失敗:\n\n"
                f"API 錯誤: {error_msg}\n"
                f"JSON 錯誤: {str(fallback_error)}\n\n"
                f"請檢查:\n"
                f"1. API 服務器是否運行在 https://api.f1telemetrystationpro.org\n"
                f"2. 本地 JSON 檔案是否存在\n"
                f"3. 參數是否正確 ({self.year} {self.race} {self.session})"
            )
            
            if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
                self.lbl_control_status.setText("數據載入失敗（API + JSON 均失敗）")
```

**❌ 對比結論**:
1. **屬性名稱不一致**: 
   - ranking_table 使用 `self.data_loader`
   - sector_comparison 使用 `self.data_manager`
   - 原因: 基類 `UniversalAnalysisMDI` 的屬性是 `data_manager`

2. **錯誤對話框調用**: 
   - ranking_table 使用 `self._show_error()` ✅
   - sector_comparison 使用 `QMessageBox.critical(self, ...)` ❌

---

## 📝 差異總結表

| 項目 | ranking_table ✅ | sector_comparison ❌ | 影響 |
|------|-----------------|---------------------|------|
| **基類** | QWidget | UniversalChartWidget | ⚠️ 方法不同 |
| **數據填充方法** | `populate_table()` | `draw_comparison_bars()` | ⚠️ 名稱不同 |
| **統計更新方法** | `update_statistics_panel()` | 無（在 ControlPanel） | ⚠️ 架構不同 |
| **清空方法** | `clear_table()` | 無 | ⚠️ 缺少方法 |
| **錯誤處理** | `_show_error()` | 無（直接用 QMessageBox） | ❌ 類型錯誤 |
| **API 成功回調** | 調用 `_on_data_loaded()` | 調用 `update_chart()` | ❌ 方法不存在 |
| **data_loader/manager** | `data_loader` | `data_manager` | ✅ 已修正 |
| **備援機制** | 檢查 `data_loader` 存在性 | 檢查 `data_manager` 存在性 | ✅ 一致 |
| **_on_data_loaded()** | 提取 `analysis_result` | 提取 `comparison_data` | ⚠️ 數據結構不同 |

---

## 🛠️ 必要修正清單

### 優先級 1: 立即修正（阻斷性錯誤）

#### 1.1 修正 _on_api_success() 方法調用
**檔案**: `ideal_lap_sector_comparison_mdi.py` Line 504

```python
# ❌ 錯誤代碼
if self.chart_widget:
    self.chart_widget.update_chart(display_data)  # ❌ 方法不存在
    print("✅ [SECTOR_COMPARISON_MDI] 圖表已更新（API 數據）")

# ✅ 修正方案 1: 調用 _on_data_loaded()（推薦）
if api_data:
    self._on_data_loaded(api_data)
    print("✅ [SECTOR_COMPARISON_MDI] 圖表已更新（API 數據）")

# ✅ 修正方案 2: 直接調用 draw_comparison_bars()
if self.chart_widget:
    comparison_data = display_data.get("comparison_data", [])
    statistics = display_data.get("statistics", {})
    self.chart_widget.draw_comparison_bars(comparison_data, statistics)
```

#### 1.2 添加 _show_error() 方法
**檔案**: `ideal_lap_sector_comparison_mdi.py` (新增方法)

```python
def _show_error(self, title: str, message: str):
    """
    顯示錯誤對話框
    
    Args:
        title: 對話框標題
        message: 錯誤訊息
    """
    # MDI 不是 QWidget，需要使用 chart_widget 作為 parent
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)
```

#### 1.3 修正所有 QMessageBox 直接調用
**檔案**: `ideal_lap_sector_comparison_mdi.py` Lines 419, 545

```python
# ❌ 錯誤代碼
QMessageBox.warning(self, "標題", "訊息")
QMessageBox.critical(self, "標題", "訊息")

# ✅ 修正代碼
self._show_error("標題", "訊息")
```

---

### 優先級 2: 建議修正（一致性問題）

#### 2.1 統一錯誤處理方式
所有錯誤對話框都使用 `_show_error()` 方法，而非直接調用 QMessageBox。

#### 2.2 補充缺少的方法
添加 `clear_chart()` 或 `clear_data()` 方法，保持與 ranking_table 的一致性。

#### 2.3 API 數據驗證一致性
確保 `_validate_api_data()` 和 `_transform_api_data_for_display()` 正確處理 Function 53 的數據格式。

---

## 🔍 根本原因分析

### 為什麼會出現這些錯誤？

1. **假設性編程**：
   - Agent 假設 `UniversalChartWidget` 有 `update_chart()` 方法
   - 沒有實際檢查 Widget 的可用方法
   - 沒有參考 ranking_table 的實際調用方式

2. **基類理解不足**：
   - `UniversalAnalysisMDI` 不是 `QWidget`，無法直接作為 QMessageBox 的 parent
   - 沒有理解基類提供的 `_show_error()` 模式

3. **架構不一致**：
   - ranking_table 使用表格（QTableWidget）
   - sector_comparison 使用圖表（matplotlib）
   - 方法名稱和調用方式完全不同，但沒有正確適配

4. **缺少端到端驗證**：
   - 代碼編寫後沒有實際運行測試
   - 沒有檢查方法調用鏈的完整性
   - 沒有驗證所有引用的方法是否存在

---

## ✅ 完整修正計畫

### 步驟 1: 修正 _on_api_success()
```python
@pyqtSlot(dict)
def _on_api_success(self, result: Dict):
    """API 請求成功回調"""
    try:
        print("✅ [SECTOR_COMPARISON_API] API 請求成功")
        
        # 提取實際數據
        api_data = result.get('data', result)
        meta = result.get('meta', {})
        
        # 驗證數據格式
        if not self._validate_api_data(api_data):
            raise ValueError("API 返回數據格式無效")
        
        # ✅ 直接調用 _on_data_loaded() 處理數據
        self._on_data_loaded(api_data)
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
            source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
            self.lbl_control_status.setText(f"✅ 已從 {source_label} 載入資料")
        
    except Exception as e:
        print(f"❌ [SECTOR_COMPARISON_API] 數據處理失敗: {e}")
        traceback.print_exc()
        self._on_api_failure(f"數據處理錯誤: {str(e)}")
```

### 步驟 2: 添加 _show_error() 方法
```python
def _show_error(self, title: str, message: str):
    """顯示錯誤對話框"""
    parent = self.chart_widget if hasattr(self, 'chart_widget') else None
    QMessageBox.critical(parent, title, message)
```

### 步驟 3: 替換所有 QMessageBox 直接調用
在整個檔案中搜索並替換：
```python
# 搜索
QMessageBox.warning(self,
QMessageBox.critical(self,
QMessageBox.information(self,

# 替換為
self._show_error(
```

### 步驟 4: 驗證 _on_data_loaded() 的數據格式
確保數據包含：
- `comparison_data`: 車手對比列表
- `statistics`: 統計資料

---

## 🎯 測試驗證清單

完成修正後，必須驗證：

- [ ] GUI 啟動無錯誤
- [ ] 點擊「理想圈分段對比」樹狀項目
- [ ] API 請求成功（網路可用時）
- [ ] 圖表正常繪製
- [ ] 統計面板正常更新
- [ ] API 失敗時回退到本地 JSON
- [ ] 本地 JSON 也失敗時顯示錯誤對話框（無類型錯誤）
- [ ] 排序功能正常
- [ ] 重新載入功能正常

---

## 📚 經驗教訓

1. **必須完全複製參考實現**：
   - 不能假設方法存在
   - 必須檢查實際的方法調用
   - 必須理解基類的設計模式

2. **錯誤處理必須一致**：
   - 使用基類提供的 `_show_error()` 方法
   - 不直接使用 `QMessageBox.warning(self, ...)`
   - 理解 MDI 不是 QWidget

3. **端到端測試必不可少**：
   - 代碼編寫後立即測試
   - 驗證所有方法調用鏈
   - 檢查所有異常處理路徑

4. **數據流必須清晰**：
   - API → _on_api_success → _on_data_loaded → Widget
   - 不跳過中間步驟
   - 保持與參考實現一致

---

## 📌 總結

**當前問題根源**：
- `_on_api_success()` 調用不存在的 `update_chart()` 方法
- 所有 `QMessageBox` 調用使用錯誤的 parent 類型（`self` 不是 QWidget）
- 缺少 `_show_error()` 輔助方法

**修正策略**：
1. 修改 `_on_api_success()` 調用 `_on_data_loaded()`
2. 添加 `_show_error()` 方法
3. 替換所有直接的 QMessageBox 調用

**預期結果**：
- 消除 AttributeError: 'update_chart' 不存在
- 消除 TypeError: QMessageBox 父元件類型錯誤
- 模組正常運行，完全符合 ranking_table 的穩定性

---

**報告完成時間**: 2025-10-09  
**對比檔案數**: 4 個（2 個 MDI + 2 個 Widget）  
**發現問題數**: 12 個  
**阻斷性錯誤**: 2 個  
**建議修正**: 10 個
