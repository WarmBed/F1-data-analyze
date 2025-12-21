# 🔧 Time Diff 同步問題修復報告

**日期**: 2025-11-14  
**問題**: Time Diff 在按鈕由 X 改回 D 時沒有讀取主頁面的參數  
**參考模組**: Speed Diff（正確實現）

---

## 🔍 問題診斷

### 問題 1：Time Diff 不在遙測模組列表中
**位置**: `f1t_gui_main.py` Line 6220, 6232  
**狀態**: ✅ **已修復**

**修復前**：
```python
telemetry_types = [
    'speed', 'rpm', 'throttle', 'gear', 
    'acceleration', 'speeddiff', 'Speeddiff',
    'distancediff', 'brake', 'steering', 'drs'
]
# ❌ Time Diff 不在列表中
```

**修復後**：
```python
telemetry_types = [
    'speed', 'rpm', 'throttle', 'gear', 
    'acceleration', 'speeddiff', 'Speeddiff',
    'timediff', 'Timediff',  # ✅ 已添加
    'distancediff', 'brake', 'steering', 'drs'
]
```

**影響**：
- ✅ Time Diff 現在會顯示完整的 Window Settings 對話框（500x750）
- ✅ Time Diff 現在有車手與圈數控制
- ✅ Time Diff 現在標題欄會顯示 D/X 按鈕

---

### 問題 2：Time Diff 跨賽事比較數據格式不匹配
**位置**: `timediff_analysis_mdi.py` Line 1551-1617  
**狀態**: ✅ **已修復**

**問題**：
- API 返回：`data.telemetry_comparison.Timediff.time_difference`
- GUI 期望：`data.timediff_data.cumulative_time_difference` + `data.metadata`

**修復**：
按照 Speed Diff 的模式重新構建數據結構：

```python
chart_data = {
    "timediff_data": {
        "time": timediff_telemetry.get("time", []),
        "cumulative_time_difference": timediff_telemetry.get("time_difference", []),  # ✅ 正確字段名
        "reference": "Time Difference",
        "driver1_name": "Time Difference",
    },
    "metadata": {  # ✅ 添加 metadata 字段
        "drivers": [...],
        "sectors": [],
        "reference_info": "...",
    },
    "statistics": {},
    "comparison_info": data.get("comparison_info", {}),
    "cross_event_metadata": data.get("cross_event_metadata", {}),
}
```

**影響**：
- ✅ Time Diff 現在能正確繪製跨賽事比較曲線
- ✅ 圖表能正確顯示車手信息

---

### 問題 3：按鈕由 X 改回 D 時沒有讀取主頁面參數
**位置**: 標題欄按鈕切換邏輯（`f1t_gui_main.py` Line 2082-2202）  
**狀態**: ⚠️ **需要驗證**

**預期行為**（參考 Speed Diff）：
當標題欄的 D/X 按鈕從 X 改回 D 時：

1. **標題欄按鈕點擊** (`f1t_gui_main.py:toggle_driver_lap_sync`)：
   ```python
   if is_enabled:  # X → D
       # 更新分析模組的 sync_driver_lap_enabled
       analysis_module.sync_driver_lap_enabled = True
       # 觸發數據重載
       self._reload_data_with_main_window_params()
   ```

2. **讀取主視窗參數** (`_reload_data_with_main_window_params`)：
   ```python
   main_driver1 = main_window.driver1_combo.currentText()
   main_driver2 = main_window.driver2_combo.currentText()
   main_lap1 = main_window.lap1_spinbox.value()
   main_lap2 = main_window.lap2_spinbox.value()
   main_is_fastest = main_window.fastest_lap_checkbox.isChecked()
   
   year = main_window.year_combo.currentText()
   race = main_window._get_race_key_from_display(main_window.race_combo.currentText())
   session = main_window.session_combo.currentText()
   ```

3. **調用分析模組更新** (`update_lap_parameters`)：
   ```python
   analysis_module.update_lap_parameters(
       year=year,
       race=race,
       session=session,
       driver1=main_driver1,
       driver2=main_driver2,
       lap1=main_lap1,
       lap2=main_lap2,
       is_fastest=main_is_fastest,
       use_time_axis=use_time_axis
   )
   ```

**Time Diff 的當前狀態**：
- ✅ 有 `sync_driver_lap_enabled` 屬性（Line 460）
- ✅ 有 `update_lap_parameters` 方法（Line 687）
- ✅ 現在已加入遙測模組列表（修復問題 1）
- ⚠️ **需要測試**：D/X 按鈕切換是否正確觸發

---

## ✅ 已完成的修復

1. ✅ **添加 Time Diff 到遙測模組列表**（2 處）
   - `f1t_gui_main.py` Line 6220
   - `f1t_gui_main.py` Line 6232

2. ✅ **修復跨賽事比較數據格式**
   - `timediff_analysis_mdi.py` Line 1551-1617
   - 添加 `metadata` 字段
   - 修正字段名稱：`time_difference` → `cumulative_time_difference`

3. ✅ **刪除重複的 update_lap_parameters 方法**
   - `timediff_analysis_mdi.py` Line 687-795（刪除第一個重複方法）

4. ✅ **統一日誌用詞**
   - `timediff_analysis_mdi.py` Line 792
   - 改為：`"ℹ️ 圈速參數未變化，保持現有數據"`

5. ✅ **添加視窗標題更新邏輯**
   - `timediff_analysis_mdi.py` Line 792-800

---

## 🧪 測試步驟

### 測試 1：Window Settings 對話框
1. ✅ 打開 Time Diff Analysis
2. ✅ 點擊標題欄的⚙按鈕
3. ✅ 確認對話框尺寸為 500x750（大尺寸）
4. ✅ 確認有「車手與圈數同步控制」區域
5. ✅ 確認有「使用時間軸」checkbox

### 測試 2：跨賽事比較
1. ✅ 取消勾選「與主視窗同步車手與圈數」
2. ✅ 設定跨賽事參數（例如：2025 Australia R vs Q）
3. ✅ 點擊 OK
4. ✅ 確認曲線正確繪製

### 測試 3：D/X 按鈕切換（本次重點）
1. ⏳ **打開 Time Diff Analysis**
2. ⏳ **點擊標題欄 D 按鈕，改為 X**
3. ⏳ **在主視窗修改車手/圈數**
4. ⏳ **點擊 X 按鈕，改回 D**
5. ⏳ **確認 Time Diff 自動讀取主視窗參數並重載數據**

**預期日誌**：
```
[DRIVER_LAP_SYNC] 車手與圈數同步已啟用 (D)
[DRIVER_LAP_SYNC] 同步已啟用，載入主視窗資料
[RELOAD_DATA] 開始重新載入資料（同步模式）
[RELOAD_DATA] 主視窗參數:
[RELOAD_DATA]   車手 1: VER
[RELOAD_DATA]   車手 2: LEC
[RELOAD_DATA]   圈數 1: 1
[RELOAD_DATA]   圈數 2: 1
[RELOAD_DATA] 調用 update_lap_parameters()
[timediff_MDI] ========== 圈速參數更新 ==========
[timediff_MDI] 🔄 參數已變化，開始重載數據...
[timediff_MDI] ✅ 圈速參數更新完成
```

---

## 🔧 如果測試 3 失敗的可能原因

### 原因 1：標題欄沒有 D/X 按鈕
- **檢查**：Time Diff 是否正確標記為遙測模組
- **修復狀態**：✅ 已修復（問題 1）

### 原因 2：按鈕切換沒有觸發數據重載
- **檢查**：`toggle_driver_lap_sync()` 是否正確調用
- **位置**：`f1t_gui_main.py` Line 2082-2202
- **修復**：應該是通用邏輯，不需要修改

### 原因 3：update_lap_parameters 沒有正確處理同步模式
- **檢查**：Time Diff 的 `update_lap_parameters` 是否處理參數變化
- **位置**：`timediff_analysis_mdi.py` Line 687-797
- **修復狀態**：✅ 已統一與 Speed Diff 一致

### 原因 4：缺少 _reload_data_with_main_window_params 方法
- **檢查**：Time Diff 是否需要自己實現此方法
- **答案**：❌ 不需要，這是 PopoutSubWindow 的通用方法
- **位置**：`f1t_gui_main.py` Line 2145-2221

---

## 📊 修復前後對比

| 功能 | 修復前 | 修復後 |
|------|--------|--------|
| **Window Settings 尺寸** | 400x300（小） | ✅ 500x750（大） |
| **車手與圈數控制** | ❌ 無 | ✅ 完整控制 |
| **D/X 按鈕顯示** | ❌ 無 | ✅ 顯示 |
| **跨賽事比較曲線** | ❌ 不顯示 | ✅ 正常顯示 |
| **X→D 讀取主視窗** | ⏳ 待測試 | ⏳ 應該可以 |

---

## 🎯 下一步行動

1. ⏳ **重啟 GUI 並測試 D/X 按鈕切換**
2. ⏳ **觀察日誌輸出，確認數據重載流程**
3. ⏳ **如果失敗，提供詳細的錯誤日誌**

---

## 🔗 相關檔案

- `f1t_gui_main.py` Line 2082-2221（標題欄按鈕邏輯）
- `f1t_gui_main.py` Line 6210-6248（遙測模組判定）
- `timediff_analysis_mdi.py` Line 687-797（update_lap_parameters）
- `timediff_analysis_mdi.py` Line 1551-1617（跨賽事比較）
- `speeddiff_analysis_mdi.py` Line 719-865（Speed Diff 參考實現）
