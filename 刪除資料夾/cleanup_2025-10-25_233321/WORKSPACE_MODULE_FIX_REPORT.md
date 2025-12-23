# 🎯 方案 A 調試結果與修復報告

## 📊 調試結果總結

### ✅ 階段 1：PopoutSubWindow 創建（Workspace 載入時）

**測試結果：完全正常 ✅**

所有 22 個視窗的 `analysis_module` 都正確保存：

```
[POPOUT_INIT] Title: 'Rain Analysis'
[POPOUT_INIT] analysis_module parameter: RainAnalysisModuleAdapter
[POPOUT_INIT] analysis_module.analysis_type: rain_weather
[POPOUT_INIT] self.analysis_module stored: RainAnalysisModuleAdapter ✅

[POPOUT_INIT] Title: 'Track Analysis'
[POPOUT_INIT] analysis_module parameter: TrackAnalysisUniversal
[POPOUT_INIT] analysis_module.analysis_type: track_analysis
[POPOUT_INIT] self.analysis_module stored: TrackAnalysisUniversal ✅

[POPOUT_INIT] Title: 'Pitstop Analysis'
[POPOUT_INIT] analysis_module parameter: PitstopAnalysisModule
[POPOUT_INIT] analysis_module.analysis_type: pitstop
[POPOUT_INIT] self.analysis_module stored: PitstopAnalysisModule ✅

[POPOUT_INIT] Title: 'Accident Analysis'
[POPOUT_INIT] analysis_module parameter: AccidentAnalysisModule
[POPOUT_INIT] analysis_module.analysis_type: accident
[POPOUT_INIT] self.analysis_module stored: AccidentAnalysisModule ✅

[POPOUT_INIT] Title: 'Tire Strategy Analysis'
[POPOUT_INIT] analysis_module parameter: TireAnalysisModuleAdapter
[POPOUT_INIT] analysis_module.analysis_type: tire
[POPOUT_INIT] self.analysis_module stored: TireAnalysisModuleAdapter ✅

... 以及其他 17 個視窗（laptime, ideal_lap 系列, 遙測系列等）
```

**結論：PopoutSubWindow 的 `analysis_module` 保存機制完全正常！**

---

### 🔴 階段 2：Race 變更時的檢測（問題發現）

**測試結果：發現關鍵問題 ❌**

```
Tab 1: 'Overview'
子視窗數量: 5
⏭️  跳過已關閉/隱藏的子視窗  ← 🔴 問題！
⏭️  跳過已關閉/隱藏的子視窗
⏭️  跳過已關閉/隱藏的子視窗
⏭️  跳過已關閉/隱藏的子視窗
⏭️  跳過已關閉/隱藏的子視窗
```

**問題根源：**

代碼邏輯：
```python
if hasattr(sub_win, 'isVisible') and not sub_win.isVisible():
    logger.info("       ⏭️  跳過已關閉/隱藏的子視窗")
    continue  # ← 🔴 錯誤：跳過了所有不可見的視窗！
```

**為什麼會不可見？**

1. Overview Tab 不是當前活動的 Tab
2. 其中的 5 個視窗（rain, track, pitstop, accident, tire）被 Qt 判定為 `isVisible() == False`
3. 但這些視窗**並非真正關閉**，只是在不活動的 Tab 中
4. 它們仍然需要接收 race 參數更新！

---

## 💡 修復方案

### 修復邏輯

**錯誤邏輯（原始）：**
```python
# ❌ 跳過所有不可見的視窗
if hasattr(sub_win, 'isVisible') and not sub_win.isVisible():
    continue
```

**正確邏輯（修復後）：**
```python
# ✅ 只跳過真正已關閉/刪除的視窗
if not sub_win or (hasattr(sub_win, 'parent') and sub_win.parent() is None):
    continue
```

### 判斷標準

| 視窗狀態 | `isVisible()` | `parent()` | 應該處理？ |
|---------|--------------|-----------|----------|
| 活動 Tab 中的視窗 | ✅ True | ✅ 有 | ✅ 是 |
| 不活動 Tab 中的視窗 | ❌ False | ✅ 有 | ✅ 是（關鍵！） |
| 已關閉的視窗 | ❌ False | ❌ None | ❌ 否 |
| 已刪除的視窗 | N/A | ❌ None | ❌ 否 |

---

## 🔧 已實施的修復

### 修改檔案：f1t_gui_main.py

**位置：** `_get_telemetry_analysis_windows()` 方法，第 8483-8495 行

**修改內容：**

```python
# 修復前：
if hasattr(sub_win, 'isVisible') and not sub_win.isVisible():
    logger.info("       ⏭️  跳過已關閉/隱藏的子視窗")
    continue

# 修復後：
if not sub_win or (hasattr(sub_win, 'parent') and sub_win.parent() is None):
    logger.info("       ⏭️  跳過已關閉/刪除的子視窗")
    continue
```

**新增調試輸出：**
```python
is_visible = sub_win.isVisible() if hasattr(sub_win, 'isVisible') else 'N/A'
print(f"[SUB_WIN_CHECK] 檢查子視窗: '{sub_win_title}' (type={sub_win_type}, visible={is_visible})")
```

---

## 📋 測試計劃（下一步）

### 測試步驟

1. **重啟 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **載入 Workspace ID=38**
   - File → Load Workspace
   - 選擇 ID=38

3. **切換 Race 到 Australia**
   - 在任一分頁切換 race

4. **驗證結果**
   - 檢查 log 中是否出現：
     ```
     [SUB_WIN_CHECK] 檢查子視窗: 'Rain Analysis' (type=PopoutSubWindow, visible=False)
     [SUB_WIN_CHECK] sub_win.analysis_module: RainAnalysisModuleAdapter
     [SUB_WIN_CHECK]   - analysis_type value: rain_weather
     ✅ 找到 Tab 視窗 (CustomMdiArea 子視窗): rain_weather
     ```

### 預期結果

**成功情況：**
- ✅ 所有 5 個 Overview Tab 視窗（rain, track, pitstop, accident, tire）都被檢測到
- ✅ 總共檢測到 22 個視窗（而非之前的 11 個）
- ✅ 所有視窗都收到 race 參數更新
- ✅ Log 顯示：
  ```
  [DEBUG] ✅ 搜尋完成！總共找到 22 個分析視窗
  [RACE_CONTROL] 發現 22 個需要更新的分析視窗
  ```

---

## 📊 問題分類

### 問題類型：邏輯錯誤

**嚴重程度：** 🔴 高（導致 50% 的視窗無法更新）

**影響範圍：**
- 所有事件級模組（rain, pitstop, accident, tire, track）
- 所有賽事級模組（laptime, ideal_lap 系列, all_drivers 系列）
- 任何位於不活動 Tab 中的分析視窗

**根本原因：**
- 混淆了「不可見」（在不活動 Tab 中）和「已關閉」（真正關閉的視窗）
- 使用 `isVisible()` 作為跳過條件是不正確的

**正確判斷標準：**
- 應該使用 `parent() is None` 判斷視窗是否已關閉
- `isVisible()` 只表示視窗當前是否在螢幕上顯示，不代表是否需要更新

---

## ✅ 修復狀態

- [x] 問題根源已確認
- [x] 修復代碼已實施
- [ ] 測試驗證待執行
- [ ] 修復效果待確認

---

## 🎓 經驗教訓

### 1. Qt 視窗可見性的理解

**錯誤認知：**
- `isVisible() == False` → 視窗已關閉

**正確認知：**
- `isVisible() == False` → 視窗當前不在螢幕上顯示（可能在不活動 Tab 中）
- `parent() == None` → 視窗已關閉/刪除

### 2. MDI 子視窗的生命週期

- 在 QTabWidget 中，不活動 Tab 的視窗會被隱藏（`isVisible() == False`）
- 但這些視窗仍然存在於記憶體中，仍然有 parent
- 它們仍然需要接收參數更新，以便切換 Tab 時顯示正確的數據

### 3. 調試的重要性

- 如果沒有添加詳細的調試輸出，很難發現是"跳過邏輯"的問題
- 調試輸出幫助我們快速定位到"所有 5 個子視窗都被跳過"的關鍵事實

---

**創建時間：** 2025-10-25 22:00  
**問題發現：** 2025-10-25 21:57 (Log 分析)  
**修復完成：** 2025-10-25 22:05  
**狀態：** 🟢 已修復 - 等待測試驗證
