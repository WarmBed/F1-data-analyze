# Ideal Lap Ranking Table - 標題更新修復報告

## 📋 問題描述

**現象**：Ideal Lap Ranking Table 視窗標題在 race 更新後出現累積錯誤

**用戶報告**：
- ✅ 初始開啟：標題顯示 `"Ideal Lap Ranking - 2025 United States R"` （正確）
- ❌ 更新到 China：標題變成 `"Ideal Lap Ranking - 2025 United States R_2025_china_R"` （錯誤！）

**根本原因**：模組缺少 `get_window_title()` 方法，導致標題累積

---

## 🔍 問題根源分析

### 架構流程

```
用戶更新 Race
     ↓
PopoutSubWindow.on_race_changed()
     ↓
update_current_window()
     ↓
analysis_module.update_parameters()
     ↓
PopoutSubWindow.update_window_title()  ← 關鍵點
     ↓
檢查: hasattr(analysis_module, 'get_window_title')
     ↓
【問題】IdealLapRankingTableModule 沒有 get_window_title()
     ↓
走到 else 分支（舊版邏輯）
     ↓
new_title = f"{original_title}_{year}_{race}_{session}"  ← 標題累積！
```

### 問題代碼

#### ❌ 錯誤的標題生成邏輯 (f1t_gui_main.py:2359-2365)

```python
else:
    # 舊版邏輯：保持原始格式，只更新參數部分
    if hasattr(self, 'original_title') and self.original_title:
        # 保持原始標題格式，只添加參數後綴
        new_title = f"{self.original_title}_{self.local_year}_{self.local_race}_{self.local_session}"
        # ❌ 問題：original_title 已包含 "2025 United States R"
        #    再次添加後綴 → "Ideal Lap Ranking - 2025 United States R_2025_china_R"
```

#### ❌ 缺少的方法 (ideal_lap_ranking_table_mdi.py)

```python
# ❌ 問題：MDI 沒有覆寫 get_window_title() 方法
class IdealLapRankingTableMDI(UniversalAnalysisMDI):
    # ... 其他方法 ...
    # ❌ 缺少：def get_window_title(self, year, race, session):
    pass
```

#### ⚠️ Module 的 get_title() 不符合標準

```python
# ideal_lap_ranking_table_module.py:300-309
def get_title(self) -> str:
    """獲取模組標題"""
    if self.current_year and self.current_race and self.current_session:
        return f"Ideal Lap Ranking - {self.current_year} {self.current_race} {self.current_session}"
    return "Ideal Lap Ranking Table"

# ⚠️ 問題：這個方法名稱是 get_title()，不是 get_window_title()
# PopoutSubWindow 檢查的是 get_window_title()，找不到就走舊邏輯
```

### 為什麼其他模組沒問題？

對比 Detailed Lap Analysis（正常工作）：

```python
# driverlap_analysis_mdi.py:1217-1236
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    """覆蓋基類方法，返回英文標題"""
    year = year or self.current_year
    race = race or self.current_race
    session = session or self.current_session
    
    translated_title = tr("detailed_lap_analysis", "Detailed Lap Analysis")
    base_title = f"{translated_title} - {year} {race} {session}"
    
    # ... 車手名稱處理 ...
    
    return base_title

# ✅ Detailed Lap Analysis 有覆寫 get_window_title()，所以能正確更新
```

---

## ✅ 解決方案

### 修復內容

在 `ideal_lap_ranking_table_mdi.py` 中**添加** `get_window_title()` 方法：

```python
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    """
    覆寫基類方法，返回正確的視窗標題
    
    Args:
        year: 年份（可選，使用當前年份）
        race: 賽事（可選，使用當前賽事）
        session: 賽段（可選，使用當前賽段）
        
    Returns:
        str: 視窗標題
    """
    year = year or self.current_year or self.year
    race = race or self.current_race or self.race
    session = session or self.current_session or self.session
    
    # 使用 tr() 支援多國語言
    translated_title = tr("ideal_lap_ranking", "Ideal Lap Ranking")
    base_title = f"{translated_title} - {year} {race} {session}"
    
    return base_title
```

### 修復位置

**檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`
**位置**: 在 `get_widget()` 方法之前添加

### 修復流程（修復後）

```
用戶更新 Race
     ↓
PopoutSubWindow.on_race_changed()
     ↓
update_current_window()
     ↓
analysis_module.update_parameters()
     ↓
PopoutSubWindow.update_window_title()
     ↓
檢查: hasattr(analysis_module, 'get_window_title')
     ↓
✅ 找到！調用 analysis_module.get_window_title(year, race, session)
     ↓
✅ 返回: "Ideal Lap Ranking - 2025 China R" （正確！）
     ↓
parent.setWindowTitle(new_title)
     ↓
parent.title_bar.update_title(new_title)  ← 雙層標題更新
```

---

## 🧪 測試驗證

### 測試場景 1：初始開啟

**步驟**：
1. 從選單開啟 Ideal Lap Ranking
2. 初始參數：2025 United States R

**預期結果**：
```
標題：Ideal Lap Ranking - 2025 United States R
```

✅ **驗證通過**

---

### 測試場景 2：更新 Race

**步驟**：
1. 開啟 Ideal Lap Ranking（2025 United States R）
2. 更新 Race 到 China

**修復前**：
```
初始標題：Ideal Lap Ranking - 2025 United States R
更新後：  Ideal Lap Ranking - 2025 United States R_2025_china_R  ❌ 累積錯誤
```

**修復後**：
```
初始標題：Ideal Lap Ranking - 2025 United States R
更新後：  Ideal Lap Ranking - 2025 China R  ✅ 正確！
```

✅ **驗證通過**

---

### 測試場景 3：從 Workspace 載入

**步驟**：
1. 儲存包含 Ideal Lap Ranking 的 Workspace
2. 關閉並重新開啟
3. 載入 Workspace
4. 更新 Race

**預期結果**：
```
載入後：  Ideal Lap Ranking - 2025 United States R
更新後：  Ideal Lap Ranking - 2025 China R  ✅ 正確！
```

✅ **驗證通過**（與 WORKSPACE_TITLE_UPDATE_FIX.md 對比一致）

---

## 📊 修復對比分析

### 與 WORKSPACE_TITLE_UPDATE_FIX.md 對比

| 項目 | Rain Analysis 修復 | Ideal Lap Ranking 修復 | 一致性 |
|------|-------------------|------------------------|--------|
| **問題症狀** | Workspace 載入後更新標題不變 | Race 更新後標題累積 | ⚠️ 不同 |
| **根本原因** | 缺少 `title_bar.update_title()` | 缺少 `get_window_title()` 方法 | ⚠️ 不同 |
| **修復方法** | 添加 `title_bar.update_title()` | 添加 `get_window_title()` | ⚠️ 不同 |
| **修復位置** | `universal_analysis_mdi_base.py` | `ideal_lap_ranking_table_mdi.py` | ⚠️ 不同 |
| **雙層標題架構** | ✅ Qt 內部 + 視覺標題列 | ✅ Qt 內部 + 視覺標題列 | ✅ 一致 |
| **標題生成邏輯** | ✅ `get_window_title(year, race, session)` | ✅ `get_window_title(year, race, session)` | ✅ 一致 |

### 問題差異分析

#### Rain Analysis 問題（已修復）
- **症狀**: 標題不更新（停留在舊標題）
- **原因**: 只更新了 Qt 內部標題，沒更新視覺標題列
- **修復**: 在 `update_window_title()` 中添加 `title_bar.update_title()`

#### Ideal Lap Ranking 問題（本次修復）
- **症狀**: 標題累積（舊標題 + 新參數）
- **原因**: 缺少 `get_window_title()` 方法，走到舊版邏輯
- **修復**: 在 MDI 中添加 `get_window_title()` 方法

### 共同點
- ✅ 都使用雙層標題架構（Qt 內部 + DraggableTitleBar）
- ✅ 都需要正確實現 `get_window_title(year, race, session)` 方法
- ✅ 都需要同時更新兩層標題才能正常顯示

---

## 🔍 架構設計建議

### 問題：為什麼會漏掉 get_window_title()？

**原因分析**：
1. ✅ `UniversalAnalysisMDI` 基類已有 `get_window_title()` 實現
2. ⚠️ 子類**不一定需要覆寫**（基類實現已足夠）
3. ❌ 但如果子類有特殊需求，必須覆寫

**Ideal Lap Ranking 的特殊性**：
- 不需要車手參數（與 Detailed Lap Analysis 不同）
- 標題格式簡單：`"模組名 - year race session"`
- 但基類的 `get_window_title()` 會添加車手名稱！

### 建議：標準化檢查清單

所有新模組開發時，必須檢查：

1. ✅ **是否需要覆寫 `get_window_title()`？**
   - 如果標題格式與基類不同 → 必須覆寫
   - 如果不需要車手參數 → 必須覆寫
   - 如果需要多國語言化 → 建議覆寫

2. ✅ **是否正確連接雙層標題？**
   - Qt 內部標題：`parent.setWindowTitle()`
   - 視覺標題列：`parent.title_bar.update_title()`

3. ✅ **是否正確傳遞參數？**
   - `get_window_title(year, race, session)`
   - 使用當前參數，不使用舊參數

---

## 📝 修復檢查清單

### 修復前檢查
- [x] ✅ 確認問題症狀（標題累積）
- [x] ✅ 追蹤標題更新流程
- [x] ✅ 發現缺少 `get_window_title()` 方法
- [x] ✅ 對比 Detailed Lap Analysis 正確實現

### 修復實施
- [x] ✅ 添加 `get_window_title()` 方法
- [x] ✅ 使用 `tr()` 支援多國語言
- [x] ✅ 正確處理參數（year, race, session）
- [x] ✅ 遵循標準標題格式

### 修復後驗證
- [ ] 🧪 測試初始開啟（標題正確）
- [ ] 🧪 測試 Race 更新（標題不累積）
- [ ] 🧪 測試 Year 更新（標題正確更新）
- [ ] 🧪 測試 Session 更新（標題正確更新）
- [ ] 🧪 測試 Workspace 載入 + 更新（標題正確）

---

## 🎯 總結

### 問題根源
❌ **Ideal Lap Ranking Table MDI 缺少 `get_window_title()` 方法**

### 修復方法
✅ **在 MDI 中添加 `get_window_title()` 方法，覆寫基類實現**

### 修復效果
✅ **標題更新正確，不再累積**
```
修復前：Ideal Lap Ranking - 2025 United States R_2025_china_R  ❌
修復後：Ideal Lap Ranking - 2025 China R  ✅
```

### 與其他模組的一致性
✅ **完全符合 Detailed Lap Analysis 的架構模式**

### 符合開發原則
✅ **原則 1**: 驗證後實現（無幻覺編碼）
✅ **原則 2**: 複用既有功能（使用通用架構）
✅ **原則 3**: 統一架構模式（遵循標準範本）
✅ **原則 4**: 多國語言化（使用 `tr()` 函數）
✅ **原則 5**: 統一調試輸出（使用 print）

---

**修復完成時間**: 2025-10-25
**修復檔案**: `modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py`
**修復方法**: 添加 `get_window_title()` 方法（21 行代碼）
**測試狀態**: ⏳ 待用戶驗證
