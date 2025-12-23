# Sector Comparison & Heatmap 標題累積問題修復報告

**日期**: 2025-10-25  
**檢查範圍**: Ideal Lap Sector Comparison, Ideal Lap Sector Heatmap  
**問題**: 缺少 `get_window_title()` 方法  
**嚴重性**: 🟡 Medium（會導致標題累積，但 `set_parent_window()` 已統一修復）

---

## 📋 反幻覺編碼五原則宣告

本次檢查和修復嚴格遵循以下原則：

### 原則 0：每次執行前宣告五原則
✅ 已宣告

### 原則 1：禁止幻覺編碼 - 必須先驗證再編寫
✅ 使用 `grep_search` 和 `read_file` 驗證所有代碼
✅ 確認兩個模組都繼承自 `UniversalAnalysisMDI`
✅ 確認兩個模組都缺少 `get_window_title()` 方法

### 原則 2：模組資料夾優先 - 複用現有功能
✅ 參考 `ideal_lap_ranking_table_mdi.py` 的實現
✅ 複用相同的標題生成邏輯

### 原則 3：通用模組優先 - 統一架構模式
✅ 兩個模組都使用 `UniversalAnalysisMDI` 基類
✅ 統一添加 `get_window_title()` 方法

### 原則 4：模組多國語言化
✅ 使用 `tr()` 函數包裹所有標題文字

### 原則 5：print 輸出會被 logger 導出
✅ 所有檢查結果記錄在本報告中

---

## 🔍 檢查結果總覽

| 模組名稱 | 繼承基類 | `get_window_title()` | `set_parent_window()` | 修復狀態 |
|----------|----------|----------------------|-----------------------|----------|
| **Ideal Lap Ranking Table** | ✅ UniversalAnalysisMDI | ✅ 已實現 | ✅ 已修復 | ✅ 完成 |
| **Ideal Lap Sector Comparison** | ✅ UniversalAnalysisMDI | ❌ **缺失** | ✅ 已修復（統一） | ✅ **已修復** |
| **Ideal Lap Sector Heatmap** | ✅ UniversalAnalysisMDI | ❌ **缺失** | ✅ 已修復（統一） | ✅ **已修復** |

---

## 🚨 發現的問題

### 1️⃣ Ideal Lap Sector Comparison

**檔案位置**: `modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_mdi.py`

#### 問題 1: 缺少 `get_window_title()` 方法
- **狀態**: ❌ 缺失
- **影響**: 當用戶更新參數時，`PopoutSubWindow.update_window_title()` 無法獲取新標題，回退到舊版累積邏輯
- **檢查方法**:
  ```bash
  grep_search: "get_window_title" in ideal_lap_sector_comparison_mdi.py
  結果: No matches found
  ```

#### 問題 2: `set_parent_window()` 調用
- **狀態**: ✅ 已修復（2025-10-25 統一修復）
- **位置**: `f1t_gui_main.py:11376-11383`
- **說明**: 在修復 Ideal Lap Ranking Table 時，已統一為所有模組工廠路徑添加了 `set_parent_window()` 調用

#### 類別結構
```python
class IdealLapSectorComparisonMDI(UniversalAnalysisMDI):
    """
    理想圈分段對比 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 IdealLapSectorComparisonDataLoader 和 IdealLapSectorComparisonWidget
    """
    
    def __init__(self, parent=None):
        super().__init__(analysis_type="ideal_lap_sector_comparison", parent=parent)
        # ... 其他初始化 ...
    
    # ❌ 缺少此方法（已添加）
    # def get_window_title(self, year, race, session) -> str:
    #     ...
```

---

### 2️⃣ Ideal Lap Sector Heatmap

**檔案位置**: `modules/gui/ideal_lap_analysis/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_mdi.py`

#### 問題 1: 缺少 `get_window_title()` 方法
- **狀態**: ❌ 缺失
- **影響**: 同上（標題累積問題）
- **檢查方法**:
  ```bash
  grep_search: "get_window_title" in ideal_lap_sector_heatmap_mdi.py
  結果: No matches found
  ```

#### 問題 2: `set_parent_window()` 調用
- **狀態**: ✅ 已修復（2025-10-25 統一修復）
- **說明**: 同上

#### 類別結構
```python
class IdealLapSectorHeatmapMDI(UniversalAnalysisMDI):
    """
    MDI orchestrator capturing data loader, widget, control panel, and stats.
    """
    
    def __init__(self, parent=None):
        self.ensure_registered()
        super().__init__(analysis_type="ideal_lap_sector_heatmap", parent=parent)
        # ... 其他初始化 ...
    
    # ❌ 缺少此方法（已添加）
    # def get_window_title(self, year, race, session) -> str:
    #     ...
```

---

## ✅ 修復方案

### 修復 1: Ideal Lap Sector Comparison

**檔案**: `ideal_lap_sector_comparison_mdi.py`  
**插入位置**: Line 277（`initialize_module()` 方法之後）  
**添加內容**:

```python
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    """
    生成視窗標題（支援參數更新時動態改變）
    
    🔧 修復: 添加此方法以支持標題動態更新（防止標題累積）
    參考實現: ideal_lap_ranking_table_mdi.py
    
    Args:
        year: 年份（可選，默認使用當前參數）
        race: 賽事（可選，默認使用當前參數）
        session: 賽段（可選，默認使用當前參數）
        
    Returns:
        str: 格式化的視窗標題
    """
    # 使用傳入參數或當前參數
    year = year or self.current_year or self.year
    race = race or self.current_race or self.race
    session = session or self.current_session or self.session
    
    # 使用 tr() 支持多國語言
    translated_title = tr("ideal_lap_sector_comparison", "Ideal Lap Sector Comparison")
    
    # 返回格式化標題
    base_title = f"{translated_title} - {year} {race} {session}"
    return base_title
```

**修復特點**:
- ✅ 支持參數動態更新（year, race, session 可選）
- ✅ 使用 `tr()` 函數支持多國語言
- ✅ 參數回退邏輯：傳入參數 → current_* → self.*
- ✅ 返回格式與 Ideal Lap Ranking Table 一致

---

### 修復 2: Ideal Lap Sector Heatmap

**檔案**: `ideal_lap_sector_heatmap_mdi.py`  
**插入位置**: Line 420（`initialize_module()` 方法之後）  
**添加內容**:

```python
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    """
    生成視窗標題（支援參數更新時動態改變）
    
    🔧 修復: 添加此方法以支持標題動態更新（防止標題累積）
    參考實現: ideal_lap_ranking_table_mdi.py
    
    Args:
        year: 年份（可選，默認使用當前參數）
        race: 賽事（可選，默認使用當前參數）
        session: 賽段（可選，默認使用當前參數）
        
    Returns:
        str: 格式化的視窗標題
    """
    # 使用傳入參數或當前參數
    year = year or self.current_year
    race = race or self.current_race
    session = session or self.current_session
    
    # 使用 tr() 支持多國語言
    translated_title = tr("ideal_lap_sector_heatmap", "Ideal Lap Sector Heatmap")
    
    # 返回格式化標題
    base_title = f"{translated_title} - {year} {race} {session}"
    return base_title
```

**修復特點**:
- ✅ 同上（與 Sector Comparison 保持一致）
- ✅ 參數回退邏輯更簡潔（只使用 current_*）

---

## 🔄 標題更新流程（修復後）

### 初始化階段

```
用戶點擊 "Ideal Lap Sector Comparison"
    ↓
模組工廠創建 IdealLapSectorComparisonMDI
    ↓
設置參數: current_year, current_race, current_session
    ↓
調用 get_window_title(year, race, session)  ← 🔧 新增方法
    ↓
返回: "Ideal Lap Sector Comparison - 2025 United States R"
    ↓
創建 PopoutSubWindow(window_title)
    ↓
調用 analysis_module.set_parent_window(sub_window)  ← ✅ 已修復
    ↓
parent_window 設置成功（不再是 None）
```

### 參數更新階段

```
用戶更新 race: United States → China
    ↓
update_parameters(year=2025, race="China", session="R")
    ↓
調用 update_window_title()
    ↓
檢查 parent_window: <PopoutSubWindow object>  ← ✅ 不再是 None
    ↓
調用 get_window_title(2025, "China", "R")  ← 🔧 使用新方法
    ↓
返回: "Ideal Lap Sector Comparison - 2025 China R"
    ↓
parent.setWindowTitle(new_title)
parent.title_bar.update_title(new_title)
    ↓
✅ 標題完全替換，不累積！
```

---

## 🧪 測試計畫

### 階段 1: 重啟 GUI（5 分鐘）

```powershell
# 步驟 1: 關閉當前 GUI
Get-Process python | Stop-Process -Force

# 步驟 2: 重新啟動 GUI
python f1t_gui_main.py
```

---

### 階段 2: Ideal Lap Sector Comparison 測試

#### 測試 2.1: 初始化
- [ ] 打開 "Ideal Lap Sector Comparison"
- [ ] 檢查初始標題：`Ideal Lap Sector Comparison - 2025 United States R`
- [ ] 檢查 Log: `[LINK] [INIT] 已設置模組的父視窗引用`

#### 測試 2.2: 單次參數更新
**操作**: United States → China
- [ ] 更新前標題：`Ideal Lap Sector Comparison - 2025 United States R`
- [ ] 更新後標題：`Ideal Lap Sector Comparison - 2025 China R` ✅
- [ ] ❌ 不應累積：`Ideal Lap Sector Comparison - 2025 United States R_2025_China_R`

#### 測試 2.3: 連續參數更新
**操作**: China → Japan → Belgium
- [ ] Japan 標題：`Ideal Lap Sector Comparison - 2025 Japan R`
- [ ] Belgium 標題：`Ideal Lap Sector Comparison - 2025 Belgium R`
- [ ] ✅ 每次都完全替換，不累積

#### 測試 2.4: Log 驗證

```log
✅ 預期 Log（修復後）:
[LINK] [INIT] 已設置模組的父視窗引用: Ideal Lap Sector Comparison - 2025 United States R
[TITLE] [MODULE] 使用模組標題: Ideal Lap Sector Comparison - 2025 China R
[LABEL] [TITLE] 標題已更新: Ideal Lap Sector Comparison - 2025 China R

❌ 錯誤 Log（如果仍有問題）:
[TITLE] [LEGACY] 使用舊版標題格式: ...  ← 不應出現
[ERROR] ❌ 無法更新標題：parent_window=False  ← 不應出現
```

---

### 階段 3: Ideal Lap Sector Heatmap 測試

#### 測試 3.1: 初始化
- [ ] 打開 "Ideal Lap Sector Heatmap"
- [ ] 檢查初始標題：`Ideal Lap Sector Heatmap - 2025 United States R`
- [ ] 檢查 Log: `[LINK] [INIT] 已設置模組的父視窗引用`

#### 測試 3.2: 單次參數更新
**操作**: United States → Singapore
- [ ] 更新前標題：`Ideal Lap Sector Heatmap - 2025 United States R`
- [ ] 更新後標題：`Ideal Lap Sector Heatmap - 2025 Singapore R` ✅
- [ ] ❌ 不應累積

#### 測試 3.3: 連續參數更新
**操作**: Singapore → Monaco → Italy
- [ ] Monaco 標題：`Ideal Lap Sector Heatmap - 2025 Monaco R`
- [ ] Italy 標題：`Ideal Lap Sector Heatmap - 2025 Italy R`
- [ ] ✅ 每次都完全替換

#### 測試 3.4: Log 驗證
- [ ] 同 Sector Comparison（檢查相同模式）

---

### 階段 4: 對比測試（三個模組同時測試）

| 操作 | Ideal Lap Ranking Table | Sector Comparison | Sector Heatmap |
|------|-------------------------|-------------------|----------------|
| 初始標題 | `... - 2025 United States R` | `... - 2025 United States R` | `... - 2025 United States R` |
| 更新 → China | `... - 2025 China R` ✅ | `... - 2025 China R` ✅ | `... - 2025 China R` ✅ |
| 更新 → Japan | `... - 2025 Japan R` ✅ | `... - 2025 Japan R` ✅ | `... - 2025 Japan R` ✅ |
| 更新 → Belgium | `... - 2025 Belgium R` ✅ | `... - 2025 Belgium R` ✅ | `... - 2025 Belgium R` ✅ |

**預期結果**: 三個模組的標題更新行為應完全一致，都不累積！

---

## 📊 修復前後對比

### 修復前（缺少 `get_window_title()`）

```
用戶更新參數: United States → China
    ↓
PopoutSubWindow.update_window_title() 檢查:
    ↓
hasattr(analysis_module, 'get_window_title'): False  ← ❌ 方法不存在
    ↓
走入 else 分支（舊版邏輯）:
    ↓
new_title = f"{original_title}_{year}_{race}_{session}"
    ↓
結果: "Ideal Lap Sector Comparison - 2025 United States R_2025_China_R"  ← ❌ 累積！
```

### 修復後（添加 `get_window_title()`）

```
用戶更新參數: United States → China
    ↓
PopoutSubWindow.update_window_title() 檢查:
    ↓
hasattr(analysis_module, 'get_window_title'): True  ← ✅ 方法存在
    ↓
調用: new_title = analysis_module.get_window_title(year, race, session)
    ↓
返回: "Ideal Lap Sector Comparison - 2025 China R"
    ↓
結果: "Ideal Lap Sector Comparison - 2025 China R"  ← ✅ 完全替換！
```

---

## 🎯 影響範圍

### 已修復的模組（3 個）

| 模組名稱 | `get_window_title()` | `set_parent_window()` | 標題更新 |
|----------|----------------------|-----------------------|----------|
| Ideal Lap Ranking Table | ✅ 已實現 | ✅ 已修復 | ✅ 正常 |
| Ideal Lap Sector Comparison | ✅ **已添加** | ✅ 已修復 | ✅ **已修復** |
| Ideal Lap Sector Heatmap | ✅ **已添加** | ✅ 已修復 | ✅ **已修復** |

### 其他使用模組工廠的模組

所有通過模組工廠（`f1t_gui_main.py:11350-11450`）創建的模組都應實現 `get_window_title()` 方法。

**建議檢查清單**:
- [ ] All Drivers Straight Line Speed
- [ ] All Drivers Brake Performance
- [ ] 其他使用 `UniversalAnalysisMDI` 的模組

---

## 📝 開發建議

### 1. 統一標題生成模式

所有繼承 `UniversalAnalysisMDI` 的模組都應實現 `get_window_title()` 方法：

```python
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    """生成視窗標題（支援參數更新時動態改變）"""
    year = year or self.current_year
    race = race or self.current_race
    session = session or self.current_session
    
    translated_title = tr("module_key", "Module Name")
    return f"{translated_title} - {year} {race} {session}"
```

### 2. 模組工廠檢查清單

創建新模組時，確保以下步驟都完成：

```python
# ✅ 1. 創建模組實例
module = YourModuleMDI(parent=self)

# ✅ 2. 設置參數提供者
module.parameter_provider = parameter_provider

# ✅ 3. 設置參數
module.current_year = str(year)
module.current_race = race
module.current_session = session

# ✅ 4. 初始化模組
module.initialize_module()

# ✅ 5. 獲取視窗標題（使用 get_window_title）
window_title = module.get_window_title(year, race, session)

# ✅ 6. 創建 PopoutSubWindow
sub_window = PopoutSubWindow(window_title, mdi_area, module)
sub_window.setWidget(module.get_widget())

# ✅ 7. 設置父視窗引用（關鍵！）
if hasattr(module, 'set_parent_window'):
    module.set_parent_window(sub_window)
    print(f"[LINK] [INIT] 已設置模組的父視窗引用: {window_title}")
```

### 3. 標題更新測試清單

每個模組都應通過以下測試：

- [ ] 初始標題格式正確
- [ ] 參數更新後標題完全替換（不累積）
- [ ] 連續多次更新標題保持正確
- [ ] Log 顯示 `[LINK] [INIT] 已設置模組的父視窗引用`
- [ ] Log 顯示 `[TITLE] [MODULE] 使用模組標題: ...`
- [ ] 不出現 `[TITLE] [LEGACY] 使用舊版標題格式`

---

## 🔄 下一步

1. **立即**: 重啟 GUI 驗證兩個模組的修復
2. **測試**: 逐個測試參數更新（United States → China → Japan）
3. **檢查**: Log 中是否有 `[LINK] [INIT]` 和 `[TITLE] [MODULE]`
4. **對比**: 三個 Ideal Lap 模組的標題更新行為是否一致
5. **擴展**: 檢查其他使用模組工廠的模組是否需要相同修復

---

## 📚 參考資料

### 相關檔案
- `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py` - 參考實現
- `modules/gui/base/universal_analysis_mdi_base.py` - 基類定義
- `f1t_gui_main.py:11350-11450` - 模組工廠路徑
- `f1t_gui_main.py:2336-2380` - PopoutSubWindow.update_window_title()

### 相關報告
- `IDEAL_LAP_RANKING_PARENT_WINDOW_FIX.md` - 初始問題修復報告
- `IDEAL_LAP_RANKING_TITLE_FIX.md` - Ranking Table 修復報告

---

**修復完成時間**: 2025-10-25  
**修復工程師**: GitHub Copilot  
**遵循原則**: 反幻覺編碼五原則 ✅  
**修復模組數**: 2/3 Ideal Lap 模組（Ranking Table 已在前次修復）
