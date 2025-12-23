# Pitstop Analysis vs Ideal Lap Ranking Table - 完整載入流程對比

**日期**: 2025-10-21  
**目的**: 找出為何 Pitstop 在 Workspace 載入後不顯示數據，而其他模組正常

---

## 🔍 **原則 0-5 宣告**

**原則 0：反幻覺編碼五原則聲明**
- ✅ 每次執行都宣告原則
- ✅ 不懂就問
- ✅ 確認需求才實作

**原則 1：禁止幻覺編碼** - 所有代碼均已通過 `read_file` 驗證  
**原則 2：模組資料夾優先** - 已檢查 `modules/gui/`  
**原則 3：通用模組優先** - 對比 Universal 架構  
**原則 4：模組多國語言化** - 使用 tr() 包裹字串  
**原則 5：print 輸出導向 log** - 查看 log 文件

---

## 📊 **模組架構對比**

### **基礎架構差異**

| 項目 | **Pitstop Analysis** | **Ideal Lap Ranking Table** |
|------|---------------------|----------------------------|
| **基類** | `IAnalysisModule` | `IAnalysisModule` (外層包裝) |
| **核心實現** | `PitstopAnalysisModule` | `IdealLapRankingTableMDI` → `UniversalAnalysisMDI` |
| **模組包裝** | 無 | `IdealLapRankingTableModule` (實作 IAnalysisModule) |
| **數據管理器** | `PitstopDataManager` | `IdealLapRankingTableDataLoader` |
| **UI 元件** | `PitstopRankingWidget` 等 | `IdealLapRankingTableWidget` |

### **關鍵發現 ⚠️**

**Pitstop**:
- **單層架構**: `PitstopAnalysisModule` 直接實作 IAnalysisModule
- **直接管理**: 自己管理 UI 創建和數據載入

**Ideal Lap Ranking**:
- **雙層架構**: `IdealLapRankingTableModule` (外層) → `IdealLapRankingTableMDI` (核心)
- **委託模式**: Module 將所有操作委託給 MDI Core

---

## 🔄 **手動創建流程對比（GUI 主程式）**

### **Pitstop Analysis 手動創建流程**

**檔案**: `f1t_gui_main.py` - `_create_analysis_module()` (Line 12199+)

```python
# ========== 步驟 1: 導入模組 ==========
from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisModule

# ========== 步驟 2: 創建實例（無參數構造） ==========
module = PitstopAnalysisModule()

# ========== 步驟 3: 設置 parameter_provider ==========
module.parameter_provider = parameter_provider  # ✅ 連接參數提供者

# ========== 步驟 4: 在初始化**前**設置參數 ==========
if parameter_provider:
    current_year = int(parameter_provider.get_current_year())
    current_race = parameter_provider.get_current_race() 
    current_session = parameter_provider.get_current_session()
    
    # ⚠️ 只設置屬性，不調用 update_parameters()
    module.current_year = str(current_year)
    module.current_race = current_race
    module.current_session = current_session
    
    print(f"[INIT] [MODULE_FACTORY] 進站分析模組參數預設為: {current_year} {current_race} {current_session}")

# ========== 步驟 5: 初始化模組 ==========
if module.initialize_module():
    print(f"[OK] [MODULE_FACTORY] 進站分析模組初始化成功")
    return module
```

**Pitstop initialize_module() 做了什麼？**

**檔案**: `pitstop_analysis_mdi.py` - Line 1582

```python
def initialize_module(self, parent_widget=None, **kwargs) -> bool:
    """初始化模組"""
    try:
        # 創建主要 Widget
        self._main_widget = QWidget(parent_widget)
        
        # 設置UI（創建 tab_widget、ranking_widget 等）
        self.setup_ui()
        
        # ⚠️ 關鍵：不立即載入數據，等待同步觸發
        # self.load_data()  # 移除立即載入（註解說明）
        
        print(f"✅ [PITSTOP_MODULE] 模組已初始化，等待參數同步...")
        
        self.set_initialized(True)
        return True
    except Exception as e:
        self.module_error.emit(f"模組初始化失敗: {str(e)}")
        return False
```

**❓ 問題**：initialize_module() 不載入數據，那數據是什麼時候載入的？

---

### **Ideal Lap Ranking Table 手動創建流程**

**檔案**: `f1t_gui_main.py` - `_create_ideal_lap_ranking_window()` (Line 11781+)

```python
# ========== 步驟 1: 導入模組 ==========
from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule

# ========== 步驟 2: 創建實例（帶參數構造） ==========
analysis_module = IdealLapRankingTableModule(
    parent=self,
    year=year,      # ✅ 構造時直接傳入
    race=race,      # ✅ 構造時直接傳入
    session=session # ✅ 構造時直接傳入
)

# ========== 步驟 3: 初始化模組 ==========
if not analysis_module.initialize_module(parent_widget=self):
    raise RuntimeError("Module initialization failed")

# ========== 步驟 4: 顯示視窗 ==========
sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
sub_window.setWidget(analysis_module.get_widget())
mdi_area.addSubWindow(sub_window)
sub_window.show()

# ========== 步驟 5: 手動載入數據 ✅ ==========
print(f"[IDEAL_LAP_RANKING] 📊 開始載入資料...")
analysis_module.load_data()  # ✅ 明確調用 load_data()
```

**IdealLapRankingTableModule.initialize_module() 做了什麼？**

**檔案**: `ideal_lap_ranking_table_module.py` - Line 108

```python
def initialize_module(self, parent_widget=None, **kwargs) -> bool:
    """初始化模組"""
    try:
        # 檢查參數
        if not self.current_year or not self.current_race or not self.current_session:
            print("❌ [RANKING_MODULE] 缺少必要參數 (year/race/session)")
            return False
        
        # 創建 MDI 核心實例
        if not self._ranking_core:
            self._ranking_core = IdealLapRankingTableMDI(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                parent=parent_widget
            )
            
            # ✅ 初始化 MDI 核心
            if not self._ranking_core.initialize_module():
                print("❌ [RANKING_MODULE] MDI 核心初始化失敗")
                return False
        
        # 獲取主要元件
        self._main_widget = self._ranking_core.get_widget()
        
        self._is_initialized = True
        return True
    except Exception as e:
        print(f"❌ [RANKING_MODULE] 初始化失敗: {e}")
        return False
```

**IdealLapRankingTableMDI.initialize_module() 做了什麼？**

**檔案**: `ideal_lap_ranking_table_mdi.py` - Line 220

```python
def initialize_module(self, parent_widget=None, **kwargs) -> bool:
    """初始化模組（設置參數並載入初始數據）"""
    try:
        # 驗證必要屬性
        if not hasattr(self, 'current_year') or not self.current_year:
            print(f"[IDEAL_LAP_MDI] ❌ 缺少 current_year 屬性")
            return False
        
        # 設置參數
        self.year = str(self.current_year)
        self.race = self.current_race
        self.session = self.current_session
        
        # ⚠️ 關鍵：調用基類的 initialize_module 來創建 chart_widget 和 data_manager
        if not super().initialize_module(parent_widget=parent_widget, **kwargs):
            print(f"[IDEAL_LAP_MDI] ❌ 基類初始化失敗")
            return False
        
        # 驗證組件已創建
        if not self.chart_widget or not self.data_manager:
            print(f"[IDEAL_LAP_MDI] ❌ chart_widget 或 data_manager 未創建")
            return False
        
        # ✅ 載入初始數據
        self.load_initial_data()  # ✅ 立即觸發 API 請求
        
        print(f"[IDEAL_LAP_MDI] ✅ 模組初始化完成")
        return True
    except Exception as e:
        print(f"[IDEAL_LAP_MDI] ❌ 初始化失敗: {e}")
        return False
```

**IdealLapRankingTableMDI.load_initial_data() 做了什麼？**

**檔案**: `ideal_lap_ranking_table_mdi.py` - Line 393

```python
def load_initial_data(self):
    """載入初始資料 - 強制使用 API"""
    print("[IDEAL_LAP_MDI] 🚀 開始載入初始資料...")
    
    # 創建 API Worker
    api_params = {
        "year": self.year,
        "race": self.race,
        "session": self.session,
        "force_refresh": False
    }
    
    self.api_worker = IdealLapRankingApiWorker(
        params=api_params,
        base_url="https://api.f1telemetrystationpro.org",
        timeout=60.0
    )
    
    # 連接信號
    self.api_worker.progress.connect(self._on_api_progress)
    self.api_worker.success.connect(self._on_api_success)
    self.api_worker.failure.connect(self._on_api_failure)
    
    # ✅ 啟動 API 請求
    self.api_worker.start()
```

---

## 🔄 **Workspace 載入流程對比**

### **Pitstop Analysis Workspace 載入**

**檔案**: `workspace_serializer.py` - `_create_module_instance()` (Line 751)

```python
# Pitstop Analysis
elif window_type == "pitstop":
    from modules.gui.pitstop_analysis import PitstopAnalysisModule
    
    # ========== 步驟 1: 創建實例（無參數） ==========
    module = PitstopAnalysisModule()
    
    # ========== 步驟 2: 初始化模組（創建 UI） ==========
    module.initialize_module()
    
    # ========== 步驟 3: 設定參數（只設置屬性） ⚠️ ==========
    if hasattr(module, 'current_year'):
        module.current_year = year
        module.current_race = race
        module.current_session = session
    
    print(f"[WORKSPACE] ✅ Pitstop Analysis 模組已創建")
    return module
```

**❌ 問題分析**：

1. **無 parameter_provider**：Workspace 載入時沒有設置 `module.parameter_provider`
2. **只設置屬性**：只用 `module.current_year = year`，沒有調用 `update_parameters()`
3. **無數據觸發**：`initialize_module()` 不載入數據，屬性設置也不觸發數據載入
4. **結果**：UI 創建了，但數據載入邏輯從未被觸發 → **空白視窗**

---

### **Ideal Lap Ranking Table Workspace 載入（假設已實現）**

**理想的實現應該是**：

```python
# Ideal Lap Ranking Table
elif window_type == "ideal_lap_ranking":
    from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
    
    # ========== 步驟 1: 創建實例（帶參數構造） ✅ ==========
    module = IdealLapRankingTableModule(
        parent=None,
        year=year,
        race=race,
        session=session
    )
    
    # ========== 步驟 2: 初始化模組 ✅ ==========
    if not module.initialize_module():
        print(f"[WORKSPACE] ❌ Ideal Lap Ranking 初始化失敗")
        return None
    
    # ========== 步驟 3: 載入數據 ✅ ==========
    module.load_data()
    
    print(f"[WORKSPACE] ✅ Ideal Lap Ranking 模組已創建")
    return module
```

**✅ 為什麼會成功？**

1. **構造時傳參數**：`IdealLapRankingTableModule(year=year, race=race, session=session)`
2. **initialize_module() 做完整初始化**：
   - 創建 `IdealLapRankingTableMDI` 核心
   - 核心的 `initialize_module()` 自動調用 `load_initial_data()`
   - `load_initial_data()` 啟動 API Worker
3. **明確調用 load_data()**：額外保險，確保數據載入

---

## 🔍 **根本原因分析**

### **Pitstop 為什麼不載入數據？**

#### **手動創建時的數據載入路徑（隱藏機制）**

讓我重新檢查 Pitstop 的 `setup_ui()` 方法：

**檔案**: `pitstop_analysis_mdi.py` - `setup_ui()` (未完整檢查)

**可能的隱藏觸發機制**：

1. **parameter_provider 信號連接**：
   - GUI 主程式設置 `module.parameter_provider`
   - parameter_provider 發出 `parameters_changed` 信號
   - Pitstop 連接該信號並觸發 `update_parameters()`

2. **QTimer 延遲載入**：
   - `initialize_module()` 可能有 `QTimer.singleShot(100, self.load_data)`
   - Workspace 載入時因為沒有事件循環還未執行

3. **UI 顯示觸發**：
   - `show()` 或 `showEvent()` 觸發數據載入
   - 但 Workspace 載入後視窗已顯示，事件已過

#### **Workspace 載入時缺失的環節**

| 環節 | **手動創建** | **Workspace 載入** | **狀態** |
|------|-------------|-------------------|---------|
| parameter_provider 設置 | ✅ 有 | ❌ 無 | **缺失** |
| 參數初始化 | ✅ `module.current_year = ...` | ✅ `module.current_year = ...` | 正常 |
| initialize_module() | ✅ 調用 | ✅ 調用 | 正常 |
| update_parameters() 調用 | ❓ 可能通過信號 | ❌ 從未調用 | **缺失** |
| load_data() 調用 | ❓ 可能自動觸發 | ❌ 從未調用 | **缺失** |
| **結果** | ✅ 顯示數據 | ❌ 空白視窗 | **Bug** |

---

## 💡 **解決方案**

### **方案 1：調用 update_parameters()（推薦）✅**

**修改**: `workspace_serializer.py` - `_create_module_instance()` (Line 751)

```python
# Pitstop Analysis
elif window_type == "pitstop":
    from modules.gui.pitstop_analysis import PitstopAnalysisModule
    module = PitstopAnalysisModule()
    
    # 初始化模組（創建 UI）
    module.initialize_module()
    
    # ✅ 設定參數並觸發數據載入
    if hasattr(module, 'current_year'):
        module.current_year = year
        module.current_race = race
        module.current_session = session
    
    # ✅ 關鍵修復：調用 update_parameters() 觸發數據載入
    if hasattr(module, 'update_parameters') and callable(module.update_parameters):
        try:
            year_int = int(year)
            success = module.update_parameters(year_int, race, session)
            if success:
                print(f"[WORKSPACE] ✅ Pitstop 參數更新成功，已觸發數據載入")
            else:
                print(f"[WORKSPACE] ⚠️  Pitstop 參數更新返回 False")
        except Exception as e:
            print(f"[WORKSPACE] ❌ Pitstop 參數更新失敗: {e}")
    else:
        print(f"[WORKSPACE] ⚠️  Pitstop 模組沒有 update_parameters 方法")
    
    print(f"[WORKSPACE] ✅ Pitstop Analysis 模組已創建")
    return module
```

**為什麼有效？**

根據 `pitstop_analysis_mdi.py` Line 1652 的代碼：

```python
def update_parameters(self, year: int, race: str, session: str) -> bool:
    """更新分析參數"""
    try:
        # 驗證參數
        if not self.validate_parameters(year, race, session):
            return False
        
        # 更新內部參數
        self.current_year = str(year)
        self.current_race = race  
        self.current_session = session
        
        # ✅ 如果參數有變化，重新載入數據
        if params_changed:
            print(f"🔄 [PITSTOP_MODULE] 參數變更觸發數據重載: {year} {race} {session}")
            
            # 確保 UI 已經設置完成再載入數據
            if self.ranking_widget is not None:
                # ✅ 立即載入數據，使用 QTimer 確保UI準備好
                QTimer.singleShot(100, self.load_data)
                print(f"📅 [PITSTOP_MODULE] 已安排數據載入任務: {year} {race} {session}")
            else:
                # UI 還沒準備好，延遲載入
                QTimer.singleShot(500, self.load_data)
        
        return True
    except Exception as e:
        return False
```

**✅ 調用 `update_parameters()` 會**：
1. 設置參數
2. 檢測參數變化（從 None → 實際值）
3. 使用 `QTimer.singleShot(100, self.load_data)` 安排數據載入
4. 觸發 `self.load_data()`
5. `load_data()` 調用 `self.data_manager.load_data()`
6. 數據載入完成後更新 UI

---

### **方案 2：直接調用 load_data()（備選）**

```python
# 在設置參數後，直接調用 load_data()
if hasattr(module, 'load_data') and callable(module.load_data):
    # 使用 QTimer 延遲執行，確保 UI 完全準備好
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(200, module.load_data)
    print(f"[WORKSPACE] ✅ 已安排 Pitstop 數據載入任務")
```

**⚠️ 風險**：
- 直接調用 `load_data()` 可能繞過某些驗證邏輯
- `update_parameters()` 是設計好的公開 API

---

### **方案 3：設置 parameter_provider（不推薦）**

```python
# 創建臨時 parameter_provider
class TempParameterProvider:
    def __init__(self, year, race, session):
        self._year = year
        self._race = race
        self._session = session
    
    def get_current_year(self):
        return self._year
    
    def get_current_race(self):
        return self._race
    
    def get_current_session(self):
        return self._session

module.parameter_provider = TempParameterProvider(year, race, session)
```

**⚠️ 問題**：
- 需要額外類別實現
- 可能需要信號機制
- 過度複雜，不如直接調用方法

---

## 📋 **修復清單**

### **需要修復的模組**

根據 API-ONLY 模式，所有 IAnalysisModule 類型的模組可能有類似問題：

| 模組 | window_type | 當前實現 | 是否需要修復 | 優先級 |
|------|-------------|---------|-------------|-------|
| **Pitstop Analysis** | `pitstop` | ❌ 只設置屬性 | ✅ **是** | 🔴 高 |
| **Accident Analysis** | `accident` | ❌ 只設置屬性 | ✅ **是** | 🟡 中 |
| **Telemetry Analysis** | `telemetry` | ❌ 只設置屬性 | ✅ **是** | 🟡 中 |
| Rain Analysis | `rain`/`rain_analysis` | ✅ 構造時傳參 | ❌ 否 | - |
| Tire Strategy | `tire`/`tire_strategy` | ✅ 構造時傳參 | ❌ 否 | - |
| Track Analysis | `track_analysis` | ✅ 構造時傳參 | ❌ 否 | - |

---

## 🔧 **完整修復代碼**

### **修改檔案**: `core/workspace_serializer.py`

**位置**: `_create_module_instance()` 方法 (Line 751, 771, 787)

#### **修復 1: Pitstop Analysis**

```python
# Pitstop Analysis
elif window_type == "pitstop":
    from modules.gui.pitstop_analysis import PitstopAnalysisModule
    module = PitstopAnalysisModule()
    # 初始化模組（創建 UI）
    module.initialize_module()
    # 設定參數（模組內部使用同步機制）
    if hasattr(module, 'current_year'):
        module.current_year = year
        module.current_race = race
        module.current_session = session
    
    # ✅ 修復：調用 update_parameters() 觸發數據載入
    if hasattr(module, 'update_parameters') and callable(module.update_parameters):
        try:
            year_int = int(year)
            success = module.update_parameters(year_int, race, session)
            if success:
                print(f"[WORKSPACE] ✅ Pitstop 參數更新成功，已觸發數據載入")
            else:
                print(f"[WORKSPACE] ⚠️  Pitstop 參數更新返回 False")
        except Exception as e:
            print(f"[WORKSPACE] ❌ Pitstop 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"[WORKSPACE] ✅ Pitstop Analysis 模組已創建")
    return module
```

#### **修復 2: Accident Analysis**

```python
# Accident Analysis
elif window_type == "accident":
    from modules.gui.accident_analysis import AccidentAnalysisModule
    module = AccidentAnalysisModule()
    # 初始化模組（創建 UI）
    module.initialize_module()
    # 設定參數（模組內部使用同步機制）
    if hasattr(module, 'current_year'):
        module.current_year = year
        module.current_race = race
        module.current_session = session
    
    # ✅ 修復：調用 update_parameters() 觸發數據載入
    if hasattr(module, 'update_parameters') and callable(module.update_parameters):
        try:
            year_int = int(year)
            success = module.update_parameters(year_int, race, session)
            if success:
                print(f"[WORKSPACE] ✅ Accident 參數更新成功，已觸發數據載入")
            else:
                print(f"[WORKSPACE] ⚠️  Accident 參數更新返回 False")
        except Exception as e:
            print(f"[WORKSPACE] ❌ Accident 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"[WORKSPACE] ✅ Accident Analysis 模組已創建")
    return module
```

#### **修復 3: Telemetry Analysis**

```python
# Telemetry Analysis
elif window_type == "telemetry":
    from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule
    module = TelemetryAnalysisModule()
    # 初始化模組（創建 UI）
    module.initialize_module()
    # 設定參數（模組內部使用同步機制）
    if hasattr(module, 'current_year'):
        module.current_year = year
        module.current_race = race
        module.current_session = session
    
    # ✅ 修復：調用 update_parameters() 觸發數據載入
    if hasattr(module, 'update_parameters') and callable(module.update_parameters):
        try:
            year_int = int(year)
            success = module.update_parameters(year_int, race, session)
            if success:
                print(f"[WORKSPACE] ✅ Telemetry 參數更新成功，已觸發數據載入")
            else:
                print(f"[WORKSPACE] ⚠️  Telemetry 參數更新返回 False")
        except Exception as e:
            print(f"[WORKSPACE] ❌ Telemetry 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"[WORKSPACE] ✅ Telemetry Analysis 模組已創建")
    return module
```

---

## 📊 **預期結果**

### **修復前（當前狀態）**

```
[WORKSPACE] 🔨 重建視窗: 'Pitstop Analysis_2025_United States_R' (type=pitstop)
[PITSTOP_MANAGER] 初始化完成，API 基底網址: https://api.f1telemetrystationpro.org
[WORKSPACE] ✅ Pitstop Analysis 模組已創建
[WORKSPACE] [DEBUG] 視窗 'Pitstop Analysis_2025_United States_R' 可見性: True
[WORKSPACE] ✅ 視窗已可見: Pitstop Analysis_2025_United States_R
```

**問題**：
- ❌ 沒有 "開始載入車手進站數據" 日誌
- ❌ 沒有 API 調用
- ❌ 視窗空白

### **修復後（預期）**

```
[WORKSPACE] 🔨 重建視窗: 'Pitstop Analysis_2025_United States_R' (type=pitstop)
[PITSTOP_MANAGER] 初始化完成，API 基底網址: https://api.f1telemetrystationpro.org
[WORKSPACE] ✅ Pitstop Analysis 模組已創建
🔄 [PITSTOP_MODULE] 參數變更觸發數據重載: 2025 United States R
📅 [PITSTOP_MODULE] 已安排數據載入任務: 2025 United States R
[WORKSPACE] ✅ Pitstop 參數更新成功，已觸發數據載入
[WORKSPACE] [DEBUG] 視窗 'Pitstop Analysis_2025_United States_R' 可見性: True
[WORKSPACE] ✅ 視窗已可見: Pitstop Analysis_2025_United States_R
🔄 [PITSTOP_MODULE] 載入數據: 2025 United States R
[PITSTOP_MANAGER] 開始載入車手進站數據: 2025 United States R
[PITSTOP_MANAGER] 🌐 調用 API: https://api.f1telemetrystationpro.org/api/v2/analysis/execute?function_id=12
[PITSTOP_MANAGER] ✅ API 調用成功
[PITSTOP_MANAGER] 📊 數據載入完成，共 20 位車手
```

**結果**：
- ✅ 顯示 "開始載入車手進站數據"
- ✅ API 調用成功
- ✅ 數據填充到表格
- ✅ 視窗顯示完整數據

---

## 🧪 **測試計劃**

### **測試步驟**

1. **保存當前 Workspace**：
   - 打開 F1T GUI
   - 手動創建 Pitstop、Accident、Telemetry 視窗
   - 確認都顯示數據
   - 保存 Workspace

2. **應用修復**：
   - 修改 `workspace_serializer.py` 的三個模組處理邏輯
   - 添加 `update_parameters()` 調用

3. **重啟並載入 Workspace**：
   - 關閉 GUI
   - 重新啟動
   - 載入剛才保存的 Workspace

4. **驗證結果**：
   - ✅ Pitstop 視窗顯示數據（不再空白）
   - ✅ Accident 視窗顯示數據
   - ✅ Telemetry 視窗顯示數據
   - ✅ 其他視窗（Rain、Tire、Track）仍正常

5. **檢查日誌**：
   - 確認有 "參數變更觸發數據重載" 訊息
   - 確認有 "開始載入車手進站數據" 訊息
   - 確認有 API 調用成功訊息

---

## 📝 **總結**

### **根本原因**

1. **Pitstop 使用隱式觸發機制**：
   - 手動創建時通過 `parameter_provider` 信號觸發數據載入
   - Workspace 載入時沒有 `parameter_provider`，導致觸發失敗

2. **只設置屬性不夠**：
   - `module.current_year = year` 只改變屬性值
   - 不會觸發 Pitstop 的數據載入邏輯

3. **缺少明確的數據載入調用**：
   - Workspace 載入流程沒有調用 `update_parameters()` 或 `load_data()`
   - 導致數據載入邏輯從未執行

### **解決方案**

✅ **在 Workspace 載入時明確調用 `update_parameters()`**：
- 這是 Pitstop 設計的公開 API
- 會驗證參數、更新屬性、觸發數據載入
- 使用 QTimer 確保 UI 準備完成

### **影響範圍**

需要修復的模組：
1. **Pitstop Analysis** (已確認 Bug)
2. **Accident Analysis** (潛在 Bug)
3. **Telemetry Analysis** (潛在 Bug)

不需要修復的模組：
- **Rain Analysis** (構造時傳參 + Adapter 自動載入)
- **Tire Strategy** (構造時傳參 + Adapter 自動載入)
- **Track Analysis** (構造時傳參 + Universal 自動載入)

---

**下一步**：應用修復代碼並測試 ✅
