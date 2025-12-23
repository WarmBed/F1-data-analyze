# Ideal Lap Ranking Table - Parent Window 設置缺失修復報告

**日期**: 2025-10-25  
**問題**: 標題累積 bug 仍然存在（重啟後仍有問題）  
**根本原因**: 模組工廠路徑缺少 `set_parent_window()` 調用  
**嚴重性**: 🔴 Critical（影響所有通過模組工廠創建的 MDI 模組）

---

## 📋 反幻覺編碼五原則宣告

本次修復嚴格遵循以下原則：

### 原則 0：每次執行前宣告五原則
✅ 已宣告

### 原則 1：禁止幻覺編碼 - 必須先驗證再編寫
✅ 使用 `grep_search` 和 `read_file` 驗證所有代碼
✅ 對比其他模組的正確實現（11780-11850）
✅ 確認 Log 中的實際執行流程

### 原則 2：模組資料夾優先 - 複用現有功能
✅ 檢查了其他模組的 `set_parent_window()` 調用模式
✅ 發現正確實現在 Boxplot、Throttle Line Chart 等模組

### 原則 3：通用模組優先 - 統一架構模式
✅ 模組工廠路徑應與專用模組創建路徑保持一致
✅ 所有 MDI 模組都應調用 `set_parent_window()`

### 原則 4：模組多國語言化
✅ 不涉及（本次為架構修復）

### 原則 5：print 輸出會被 logger 導出
✅ 所有 debug 信息都在 Log 中可見

---

## 🔍 問題追蹤清單（逐行驗證）

| # | 檢查項 | 檔案位置 | 狀態 | 詳細說明 |
|---|--------|----------|------|----------|
| 1 | ✅ `get_window_title()` 存在 | `ideal_lap_ranking_table_mdi.py:638-657` | 正常 | 方法已實現，返回正確格式 |
| 2 | ❌ `set_parent_window()` 調用 | `f1t_gui_main.py:11350-11450` | **缺失！** | **模組工廠路徑沒有調用** |
| 3 | ✅ PopoutSubWindow 創建 | `f1t_gui_main.py:11376` | 正常 | `PopoutSubWindow(window_title, mdi_area, analysis_module)` |
| 4 | ❌ 父視窗引用設置 | Log: `parent_window = None` | **失敗！** | 從未設置，導致 `update_window_title()` 失敗 |
| 5 | ✅ `update_window_title()` 存在 | `universal_analysis_mdi_base.py:886-950` | 正常 | 基類方法存在 |
| 6 | ❌ `parent_window` 檢查失敗 | Log: `parent_window=False` | **失敗！** | 因為是 `None`，走入 else 分支 |
| 7 | ❌ 舊版累積邏輯觸發 | `f1t_gui_main.py:2359-2365` | **觸發！** | `f"{original_title}_{year}_{race}_{session}"` |

---

## 🚨 根本原因分析

### 問題流程圖

```
用戶點擊 "Ideal Lap Ranking Table"
    ↓
模組工廠創建 IdealLapRankingTableMDI (11350-11450)
    ↓
PopoutSubWindow 創建成功
    ↓
❌ 缺少 set_parent_window() 調用
    ↓
analysis_module.parent_window = None
    ↓
用戶更新 race: United States → China
    ↓
update_parameters() 調用 update_window_title()
    ↓
檢查 parent_window: None
    ↓
Log: [ERROR] ❌ 無法更新標題：parent_window=False
    ↓
走入 PopoutSubWindow.update_window_title() else 分支
    ↓
使用舊版累積邏輯: f"{original_title}_{year}_{race}_{session}"
    ↓
標題變成: "Ideal Lap Ranking - 2025 United States R_2025_China_R"
```

### 對比正確流程（其他模組）

```python
# ✅ 正確流程（Boxplot 模組 - f1t_gui_main.py:11780-11850）
sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
sub_window.setWidget(analysis_module.get_widget())

# 🔑 關鍵步驟：設置父視窗引用
analysis_module.set_parent_window(sub_window)

# 現在 analysis_module.parent_window = sub_window（不是 None）
```

```python
# ❌ 錯誤流程（模組工廠路徑 - f1t_gui_main.py:11350-11450）
analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
content_widget = analysis_module.get_widget()
analysis_window.setWidget(content_widget)

# ❌ 缺少：analysis_module.set_parent_window(analysis_window)

# 結果：analysis_module.parent_window = None（從未設置）
```

---

## 📊 Log 證據分析

### 初始化階段（正常）

```log
[TITLE] [FIX] 使用當前參數生成標題: Ideal Lap Ranking - 2025 United States R
[OK] [MODULE] 使用模組化架構創建視窗: Ideal Lap Ranking - 2025 United States R
```

### 更新參數階段（失敗）

```log
[REFRESH] [MODULE] Ideal Lap Ranking - 2025 United States R 參數已更新: {'year': '2025', 'race': 'United States', 'session': 'R'}

[UPDATE_TITLE_DEBUG] ========== 開始更新視窗標題 ==========
[UPDATE_TITLE_DEBUG] hasattr(self, 'parent_window'): True
[UPDATE_TITLE_DEBUG] parent_window 值: None  ← 🚨 問題核心！
[UPDATE_TITLE_DEBUG] parent_window 類型: None

[ERROR] ❌ 無法更新標題：parent_window=False, hasattr=False
```

### 結果

因為 `parent_window = None`，`update_window_title()` 無法更新標題，走入 PopoutSubWindow 的舊版邏輯，導致標題累積。

---

## ✅ 修復方案

### 修改位置

**檔案**: `f1t_gui_main.py`  
**行數**: 11376-11383  
**修改類型**: 添加 `set_parent_window()` 調用

### 修改前

```python
analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)

# 設置模組的widget
content_widget = analysis_module.get_widget()
analysis_window.setWidget(content_widget)

# [REMOVED] 不再需要重新設置標題，因為已經使用 get_window_title 設置正確標題
print(f"[TITLE] [OK] 視窗標題已設置為: {window_title}")
```

### 修改後

```python
analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)

# 設置模組的widget
content_widget = analysis_module.get_widget()
analysis_window.setWidget(content_widget)

# 🔧 [CRITICAL FIX] 設置模組的父視窗引用（與其他模組保持一致）
if hasattr(analysis_module, 'set_parent_window'):
    analysis_module.set_parent_window(analysis_window)
    print(f"[LINK] [INIT] 已設置模組的父視窗引用: {window_title}")

# [REMOVED] 不再需要重新設置標題，因為已經使用 get_window_title 設置正確標題
print(f"[TITLE] [OK] 視窗標題已設置為: {window_title}")
```

---

## 🧪 測試計畫

### 階段 1: 重啟驗證（5 分鐘）

```powershell
# 步驟 1: 關閉當前 GUI
Get-Process python | Stop-Process -Force

# 步驟 2: 重新啟動 GUI
python f1t_gui_main.py
```

### 階段 2: 初始化檢查

- [ ] 打開 Ideal Lap Ranking Table
- [ ] 檢查 Log 是否出現：`[LINK] [INIT] 已設置模組的父視窗引用`
- [ ] 檢查初始標題：應為 `Ideal Lap Ranking - 2025 United States R`

### 階段 3: 參數更新測試

**測試場景 1**: United States → China
- [ ] 初始標題：`Ideal Lap Ranking - 2025 United States R`
- [ ] 更新後標題：`Ideal Lap Ranking - 2025 China R` ✅（不累積）

**測試場景 2**: China → Japan
- [ ] 更新前標題：`Ideal Lap Ranking - 2025 China R`
- [ ] 更新後標題：`Ideal Lap Ranking - 2025 Japan R` ✅（完全替換）

**測試場景 3**: 連續多次更新
- [ ] Belgium → Singapore → Monaco → Italy
- [ ] 每次更新標題應完全替換，不累積參數

### 階段 4: Log 驗證

檢查以下 Log 輸出：

```log
✅ 預期 Log（修復後）:
[LINK] [INIT] 已設置模組的父視窗引用: Ideal Lap Ranking - 2025 United States R
[UPDATE_TITLE_DEBUG] parent_window 值: <PopoutSubWindow object>  ← 不再是 None
[UPDATE_TITLE_DEBUG] parent_window 類型: PopoutSubWindow
[TITLE] [MODULE] 使用模組標題: Ideal Lap Ranking - 2025 China R
[LABEL] [TITLE] 標題已更新: Ideal Lap Ranking - 2025 China R
```

```log
❌ 錯誤 Log（如果仍有問題）:
[UPDATE_TITLE_DEBUG] parent_window 值: None  ← 仍然是 None
[ERROR] ❌ 無法更新標題：parent_window=False
[TITLE] [LEGACY] 使用舊版標題格式: ...  ← 不應出現
```

---

## 📊 MDI 視窗標題 Debug 指南

### 問題: "MDI視窗標題該怎print才能跟GUI顯示一樣？"

MDI 視窗有**兩層標題系統**：

#### 1. Qt 內部標題（QMdiSubWindow.windowTitle()）

```python
# 在 universal_analysis_mdi_base.py 的 update_window_title() 中：
parent = getattr(self, 'parent_window', None)
if parent:
    print(f"[TITLE_DEBUG] Qt windowTitle(): {parent.windowTitle()}")
```

#### 2. 視覺標題欄（DraggableTitleBar）

```python
# 在 f1t_gui_main.py 的 PopoutSubWindow.update_window_title() 中：
if hasattr(self, 'title_bar') and self.title_bar:
    print(f"[TITLE_DEBUG] DraggableTitleBar 文字: {self.title_bar.title_label.text()}")
```

### 建議的完整 Debug Print

在 `universal_analysis_mdi_base.py` 的 `update_window_title()` 中添加：

```python
def update_window_title(self) -> None:
    """更新視窗標題 - 確保完全替換，不累積舊標題"""
    try:
        # 🔍 DEBUG: 檢查 parent_window 狀態
        print(f"[TITLE_DEBUG] ========== 開始更新視窗標題 ==========")
        print(f"[TITLE_DEBUG] hasattr(self, 'parent_window'): {hasattr(self, 'parent_window')}")
        
        parent = getattr(self, 'parent_window', None)
        print(f"[TITLE_DEBUG] parent_window 值: {parent}")
        print(f"[TITLE_DEBUG] parent_window 類型: {type(parent).__name__ if parent else 'None'}")
        
        if parent:
            # 🎯 GUI 顯示的標題（Qt 內部）
            print(f"[TITLE_DEBUG] Qt windowTitle(): {parent.windowTitle()}")
            
            # 🎯 視覺標題欄文字（DraggableTitleBar）
            if hasattr(parent, 'title_bar') and parent.title_bar:
                print(f"[TITLE_DEBUG] DraggableTitleBar 文字: {parent.title_bar.title_label.text()}")
            
            # 🎯 模組的 get_window_title() 返回值
            if hasattr(self, 'get_window_title'):
                expected_title = self.get_window_title(
                    self.current_year, 
                    self.current_race, 
                    self.current_session
                )
                print(f"[TITLE_DEBUG] get_window_title() 返回: {expected_title}")
        
        print(f"[TITLE_DEBUG] =====================================")
        
        # ... 原有更新邏輯 ...
```

### GUI 顯示標題的來源

GUI 上顯示的標題來自：
1. **主要**：`DraggableTitleBar.title_label.text()` - 視覺標題欄
2. **備用**：`QMdiSubWindow.windowTitle()` - Qt 內部標題

兩者應保持同步，通過 `PopoutSubWindow.update_window_title()` 同時更新：
```python
self.setWindowTitle(new_title)  # 更新 Qt 內部
self.title_bar.update_title(new_title)  # 更新視覺標題欄
```

---

## 🎯 影響範圍

此修復影響**所有通過模組工廠創建的 MDI 模組**：

| 模組類型 | 受影響 | 修復狀態 |
|----------|--------|----------|
| Ideal Lap Ranking Table | ✅ 是 | ✅ 已修復 |
| Ideal Lap Sector Heatmap | ✅ 是 | ✅ 已修復 |
| Ideal Lap Sector Comparison | ✅ 是 | ✅ 已修復 |
| Rain Analysis | ❌ 否 | N/A（使用專用路徑） |
| Lap Analysis | ❌ 否 | N/A（使用專用路徑） |
| Boxplot | ❌ 否 | N/A（使用專用路徑） |

**注意**: 專用模組創建路徑（如 Boxplot）已正確實現 `set_parent_window()`，不受此問題影響。

---

## 📝 總結

### 問題根源
模組工廠路徑（`f1t_gui_main.py:11350-11450`）在創建 MDI 子視窗後，**忘記調用 `set_parent_window()`**，導致模組的 `parent_window` 始終為 `None`。

### 為何重啟後仍有問題
即使實現了 `get_window_title()`，如果 `parent_window = None`，`update_window_title()` 無法執行，標題更新會回退到 PopoutSubWindow 的舊版邏輯，造成累積。

### 修復方式
在模組工廠路徑中添加與其他模組一致的 `set_parent_window()` 調用，確保 `parent_window` 不為 `None`。

### 驗證方式
1. 檢查 Log 是否出現 `[LINK] [INIT] 已設置模組的父視窗引用`
2. 檢查更新參數時 `parent_window` 不再是 `None`
3. 檢查標題更新是否完全替換（不累積）

---

## 🔄 下一步

1. **立即**: 重啟 GUI 驗證修復
2. **測試**: 多次更新參數，確認標題不累積
3. **檢查**: 其他通過模組工廠創建的模組是否正常
4. **優化**: 考慮在模組工廠中統一處理 `set_parent_window()`，避免遺漏

---

**修復完成時間**: 2025-10-25  
**修復工程師**: GitHub Copilot  
**遵循原則**: 反幻覺編碼五原則 ✅
