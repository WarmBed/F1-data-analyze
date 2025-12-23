# 同步勾選後仍保持跨賽事狀態問題修復報告

## 🚨 用戶問題

**問題描述**：勾選「與主視窗同步車手與圈數」後，Speed 模組仍然停留在跨賽事狀態，沒有切換回單賽事模式。

---

## 🔍 問題根本原因分析

### 問題流程追蹤

1. **初始狀態**：用戶在跨賽事模式（例如：車手1=2025 Japan R, 車手2=2024 Bahrain R）
2. **用戶操作**：勾選「與主視窗同步車手與圈數」
3. **主視窗處理** (`f1t_gui_main.py` Line 6657):
   ```python
   sync_enabled = self.sync_driver_lap_checkbox.isChecked()  # True
   analysis_module.sync_driver_lap_enabled = sync_enabled  # ✅ 設為 True
   ```

4. **讀取對話框參數** (Line 6667-6673):
   ```python
   year1 = self.driver1_year_combo.currentText()  # "2025"
   year2 = self.driver2_year_combo.currentText()  # "2024" ← ❌ 仍是舊值！
   session1 = self.driver1_session_combo.currentText()  # "R"
   session2 = self.driver2_session_combo.currentText()  # "Q" ← ❌ 仍是舊值！
   ```

5. **跨賽事檢測** (Line 6696):
   ```python
   is_cross_event = (year1 != year2) or (session1 != session2)  # True ❌
   ```

6. **錯誤分支** (Line 6703):
   ```python
   if is_cross_event:
       # ❌ 調用跨賽事比較方法
       analysis_module.update_cross_event_comparison(...)
   ```

7. **同步被重置** (`speed_analysis_mdi.py` Line 1034):
   ```python
   def update_cross_event_comparison(...):
       # ⚠️ 關鍵：跨賽事比較時停用同步
       self.sync_driver_lap_enabled = False  # ❌ 又被設回 False！
   ```

### 根本原因

**邏輯衝突**：
- 主視窗先設置 `sync_enabled = True`
- 但從對話框讀取的參數仍然是跨賽事值（year1 != year2）
- 導致系統誤判為跨賽事，調用 `update_cross_event_comparison`
- `update_cross_event_comparison` 又將 `sync_enabled` 設回 `False`

**設計缺陷**：
- 沒有在勾選同步時**強制切換回單賽事模式**
- 沒有在勾選同步時**使用主視窗的參數覆蓋對話框參數**

---

## ✅ 修復方案

### 修復位置：`f1t_gui_main.py` Line 6692-6696

**修復策略**：
1. 當 `sync_enabled = True` 時，**強制使用主視窗參數**
2. 將 `year2`, `session2` 強制設為與 `year1`, `session1` 相同
3. 強制設置 `is_cross_event = False`
4. 確保調用 `update_lap_parameters` 而不是 `update_cross_event_comparison`

### 修復前代碼

```python
# === 檢測是否為跨賽事比較 ===
is_cross_event = (year1 != year2) or (session1 != session2)

if is_cross_event:
    # ... 調用 update_cross_event_comparison
```

### 修復後代碼

```python
# === 檢測是否為跨賽事比較 ===
# ⚠️ 關鍵修復：如果啟用同步，強制使用主視窗參數（單賽事模式）
if sync_enabled:
    print(f"[SYNC_FIX] 🔒 已啟用同步，強制使用主視窗參數（單賽事模式）")
    # 從主視窗獲取當前參數
    year1 = self.main_window.current_year
    race1 = self.main_window.current_race
    session1 = self.main_window.current_session
    year2 = year1  # 強制相同
    race2 = race1  # 強制相同
    session2 = session1  # 強制相同
    
    print(f"[SYNC_FIX] 主視窗參數: {year1} {race1} {session1}")
    print(f"[SYNC_FIX] 強制設定: year2={year2}, session2={session2}")
    
    # 更新分析模組的跨賽事參數為主視窗值
    analysis_module.driver1_year = year1
    analysis_module.driver1_race = race1
    analysis_module.driver1_session = session1
    analysis_module.driver2_year = year2
    analysis_module.driver2_race = race2
    analysis_module.driver2_session = session2
    
    is_cross_event = False  # 強制設為 False
    print(f"[SYNC_FIX] ✅ 已強制切換為單賽事模式（is_cross_event = False）")
else:
    is_cross_event = (year1 != year2) or (session1 != session2)

if is_cross_event:
    # ... 調用 update_cross_event_comparison（只在 sync_enabled = False 時）
```

---

## 📊 修復效果

### 修復前流程

```
用戶勾選同步
    ↓
sync_enabled = True  ✅
    ↓
year1 = "2025", year2 = "2024"  ❌ 對話框舊值
    ↓
is_cross_event = True  ❌ 誤判
    ↓
update_cross_event_comparison()
    ↓
sync_enabled = False  ❌ 又被重置！
    ↓
❌ 結果：仍在跨賽事狀態
```

### 修復後流程

```
用戶勾選同步
    ↓
sync_enabled = True  ✅
    ↓
檢測 sync_enabled == True
    ↓
year1 = main_window.current_year  ✅ 使用主視窗參數
year2 = year1  ✅ 強制相同
session2 = session1  ✅ 強制相同
    ↓
is_cross_event = False  ✅ 強制單賽事
    ↓
update_lap_parameters()  ✅ 調用單賽事方法
    ↓
✅ 結果：成功切換回單賽事模式
```

---

## 🎯 預期行為

修復後，當用戶勾選「與主視窗同步」時：

1. ✅ `sync_driver_lap_enabled` 保持為 `True`（不會被重置）
2. ✅ 自動切換回單賽事模式（使用主視窗參數）
3. ✅ `year2` 和 `session2` 自動與 `year1` 和 `session1` 同步
4. ✅ 狀態列隱藏（因為 `sync_enabled = True`）
5. ✅ 後續的主視窗參數變更會同步到分析模組

---

## 📋 測試檢查清單

### 測試步驟

1. [ ] 開啟 Speed Analysis 模組
2. [ ] 取消同步勾選（停用同步）
3. [ ] 設置跨賽事參數（例如：車手1=2025 Japan R, 車手2=2024 Bahrain R）
4. [ ] 確認進入跨賽事模式（狀態列顯示跨賽事資訊）
5. [ ] **重新勾選「與主視窗同步」**
6. [ ] **確認自動切換回單賽事模式**
7. [ ] **確認 `year2` 和 `session2` 已同步為主視窗值**
8. [ ] **確認狀態列隱藏**（同步模式）
9. [ ] 在主視窗更改參數
10. [ ] 確認 Speed Analysis 同步更新

### 預期結果

| 測試項目 | 預期結果 | 狀態 |
|---------|---------|------|
| 勾選同步後 `sync_enabled` | `True` | ⏳ 待測試 |
| 勾選同步後 `is_cross_event` | `False` | ⏳ 待測試 |
| 勾選同步後 `year2` | 等於 `year1` | ⏳ 待測試 |
| 勾選同步後 `session2` | 等於 `session1` | ⏳ 待測試 |
| 勾選同步後狀態列 | 隱藏 | ⏳ 待測試 |
| 主視窗參數變更 | 同步更新 | ⏳ 待測試 |

---

## 🔗 相關問題

### 同時修復的問題

1. ✅ 取消同步勾選後狀態列沒有更新（已修復 `_setup_ui` 和 `update_lap_parameters`）
2. ✅ 勾選同步後仍保持跨賽事狀態（本次修復）

### 待確認的問題

1. ⏳ Throttle 模組是否有相同問題（應該有，因為邏輯相同）
2. ⏳ 其他遙測模組（RPM, Gear, Brake）是否有相同問題

---

## 📝 修復總結

### 修改檔案

- **`f1t_gui_main.py`**: 1 處修改（Line 6692-6726）

### 修改內容

- **新增代碼**: 28 行
- **刪除代碼**: 4 行
- **修改邏輯**: 同步勾選時強制使用主視窗參數

### 遵循原則

✅ **反幻覺編碼原則**：
1. ✅ 使用 `grep_search` 追蹤 `sync_driver_lap_enabled` 的所有使用位置
2. ✅ 使用 `read_file` 讀取實際代碼，理解完整流程
3. ✅ 追蹤從主視窗到分析模組的完整調用鏈
4. ✅ 修復根本原因，而不是症狀

---

**修復完成時間**: 2025-11-13  
**問題類型**: 邏輯缺陷  
**嚴重程度**: 高（影響用戶體驗）  
**修復方法**: 強制使用主視窗參數當同步啟用
