# 🔧 Sync Checkbox AttributeError 修復報告

## 📋 問題描述

### 錯誤訊息
```
Traceback (most recent call last):
  File "C:\Users\mike2\OneDrive\Code\F1-data-analyze/f1t_gui_main.py", line 6715, in _apply_driver_lap_settings
    year1 = self.main_window.current_year
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'StyleHMainWindow' object has no attribute 'current_year'
```

### 根本原因
在 `_apply_driver_lap_settings()` 方法的 Line 6715-6717，錯誤地假設主視窗有 `current_year`, `current_race`, `current_session` 屬性，但實際上主視窗使用 **QComboBox** 存儲這些參數，而不是直接屬性。

### 錯誤代碼（Line 6715-6717）
```python
# ❌ 錯誤：假設存在這些屬性
year1 = self.main_window.current_year
race1 = self.main_window.current_race
session1 = self.main_window.current_session
```

---

## 🔍 根因分析

### 主視窗參數存儲方式
根據對 `f1t_gui_main.py` 的完整調查，主視窗（`StyleHMainWindow`）使用以下方式存儲參數：

```python
# 主視窗實際存儲方式
self.year_combo = QComboBox()          # 年份下拉框
self.race_combo = QComboBox()          # 賽事下拉框
self.session_combo = QComboBox()       # 會話下拉框
self.driver1_combo = QComboBox()       # 車手1下拉框
self.driver2_combo = QComboBox()       # 車手2下拉框
self.lap1_spinbox = QSpinBox()         # 圈數1
self.lap2_spinbox = QSpinBox()         # 圈數2
self.fastest_lap_checkbox = QCheckBox() # 最速圈
```

### 正確的讀取方式
根據 `update_all_lap_analysis()` 方法（Line 8800-8823）的參考實現：

```python
# ✅ 正確：從 combo box 讀取
driver1 = self.driver1_combo.currentText()
driver2_data = self.driver2_combo.currentData()
driver2 = self.driver2_combo.currentText() if driver2_data is not None else None
lap1 = self.lap1_spinbox.value()
lap2 = self.lap2_spinbox.value()
is_fastest = self.fastest_lap_checkbox.isChecked()
use_time_axis = self.use_time_axis_checkbox.isChecked()
year = self.year_combo.currentText()
race_display = self.race_combo.currentText()
race = self._get_race_key_from_display(race_display)  # 移除日期後綴
session = self.session_combo.currentText()
```

---

## ✅ 修復方案

### 修復代碼（Line 6715-6720）
```python
# ✅ 修復：從主視窗 combo box 讀取
year1 = self.main_window.year_combo.currentText()
race1_display = self.main_window.race_combo.currentText()
race1 = self.main_window._get_race_key_from_display(race1_display)
session1 = self.main_window.session_combo.currentText()
year2 = year1  # 強制相同
race2 = race1  # 強制相同
session2 = session1  # 強制相同
```

### 關鍵修復點
1. **使用 `year_combo.currentText()`** 而不是 `current_year`
2. **使用 `race_combo.currentText()`** 而不是 `current_race`
3. **調用 `_get_race_key_from_display()`** 移除賽事名稱的日期後綴（例如："Japan (2025-04-06)" → "Japan"）
4. **使用 `session_combo.currentText()`** 而不是 `current_session`

---

## 🧪 測試驗證

### 自動測試結果
執行 `python test_sync_fix.py`：

```
✅ 已移除錯誤的 current_year 屬性
✅ 正確使用 year_combo.currentText()
✅ 正確使用 race_combo.currentText()
✅ 正確使用 _get_race_key_from_display()
✅ 正確使用 session_combo.currentText()
```

### 手動測試步驟
1. 啟動 GUI：`python f1t_gui_main.py`
2. 主 GUI 設定：2025 Brazil R, NOR, driver2=None, lap1
3. 開啟 Speed Analysis（設定為跨賽事：2025 AU R vs 2025 AU Q）
4. 右鍵 Speed Analysis → Settings
5. 勾選「Sync Driver & Lap with Main GUI」
6. 點擊 OK
7. **驗證**：
   - ✅ 無 AttributeError 錯誤
   - ✅ 圖表應顯示 Brazil R 的 NOR 曲線（不是 AU）
   - ✅ 狀態列消失（因為啟用同步）
   - ✅ 視窗標題更新為 "Speed Analysis - Brazil R"

---

## 📊 完整修復總結

### 本次修復包含兩個部分

#### Part 1: accept_settings 的 else 分支（Line 6618-6641）
**問題**：勾選同步後，else 分支是空的，沒有處理代碼

**修復**：
```python
else:
    # 啟用同步：從主視窗讀取參數並應用
    print(f"[SYNC_MODE] 車手與圈數同步已啟用，從主視窗讀取參數")
    
    # ✅ 從主視窗讀取所有參數
    main_driver1 = self.main_window.driver1_combo.currentText()
    main_driver2_data = self.main_window.driver2_combo.currentData()
    main_driver2 = self.main_window.driver2_combo.currentText() if main_driver2_data is not None else None
    main_lap1 = self.main_window.lap1_spinbox.value()
    main_lap2 = self.main_window.lap2_spinbox.value()
    main_is_fastest = self.main_window.fastest_lap_checkbox.isChecked()
    
    # ✅ 調用 _apply_driver_lap_settings 實際套用主視窗參數
    self._apply_driver_lap_settings(main_driver1, main_driver2, main_lap1, main_lap2, main_is_fastest)
    print(f"[SYNC_MODE] ✅ 主視窗參數已套用到當前視窗")
```

#### Part 2: _apply_driver_lap_settings 的屬性讀取（Line 6715-6720）
**問題**：使用不存在的 `current_year/current_race/current_session` 屬性

**修復**：
```python
# ✅ 修復：從主視窗 combo box 讀取
year1 = self.main_window.year_combo.currentText()
race1_display = self.main_window.race_combo.currentText()
race1 = self.main_window._get_race_key_from_display(race1_display)
session1 = self.main_window.session_combo.currentText()
```

---

## 🎯 預期效果

### 勾選同步後
1. **即時更新**：點擊 OK 後立即顯示主 GUI 的曲線
2. **參數同步**：Year/Race/Session/Driver1/Driver2/Lap1/Lap2 全部使用主視窗參數
3. **狀態列消失**：因為啟用同步，不再顯示獨立參數提示
4. **視窗標題更新**：顯示主視窗的賽事資訊

### 取消同步後
1. **保持獨立**：使用對話框中設定的參數
2. **狀態列顯示**：提示當前視窗使用獨立參數
3. **跨賽事支援**：允許設定不同的 Year/Session 進行比較

---

## 📝 參考代碼位置

### 主視窗參數定義
- **Year Combo**: Line 813-814
- **Race Combo**: Line 829-831
- **Session Combo**: Line 基礎設定
- **Driver1 Combo**: Line 813, 971-972
- **Driver2 Combo**: Line 829-831, 868, 974-975
- **Lap SpinBox**: Line 基礎設定

### 參考實現
- **update_all_lap_analysis**: Line 8740-9190（完整的參數讀取範例）
- **_apply_driver_lap_settings**: Line 6662-6860（套用參數邏輯）

---

## ✅ 修復狀態

| 項目 | 狀態 |
|------|------|
| AttributeError 修復 | ✅ 完成 |
| accept_settings else 分支 | ✅ 完成 |
| 主視窗參數讀取 | ✅ 完成 |
| 移除無效調用 | ✅ 完成 |
| 自動測試通過 | ✅ 通過 |
| 待手動驗證 | ⏳ 待測試 |

---

## 🔗 相關文件

- 原始問題報告：`tasks/SYNC_CHECKBOX_CROSS_EVENT_FIX_REPORT.md`
- 測試腳本：`test_sync_fix.py`
- 修改檔案：`f1t_gui_main.py`

---

**修復完成時間**：2025-11-13  
**修復狀態**：✅ 已完成，待手動測試驗證
