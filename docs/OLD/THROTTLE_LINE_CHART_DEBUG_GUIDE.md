# Throttle Line Chart Driver 2 過濾問題 - 調試指南

## 🎯 調試目的

用戶回報：即使勾選了過濾選項（Filter Pit Stop、Filter Yellow Flag、Filter Red Flag），Driver 2 仍然顯示未過濾的數據。

本次調試在所有關鍵位置增加了大量 `print` 輸出，以追蹤完整的數據流和過濾狀態。

---

## 🔍 已增加的調試點

### 1. ThrottleLineChartDataLoader.__init__()

**位置**: `throttle_line_chart_data_loader.py` L143-157

**調試輸出**:
```python
🔍🔍🔍 [DataLoader.__init__] Initial filters from settings_manager: {...}
🔍🔍🔍 [DataLoader.__init__] Current filter attributes BEFORE update: pit=..., yellow=..., red=...
🔍🔍🔍 [DataLoader.__init__] Current filter attributes AFTER update: pit=..., yellow=..., red=...
🔍🔍🔍 [DataLoader.__init__] Successfully connected to boxplot_settings_changed signal
```

**檢查重點**:
- `settings_manager.get_boxplot_settings()` 返回的初始值是否正確
- `update_filter_settings()` 是否成功更新了 `_filter_pit_laps` 等屬性
- 是否成功連接到 `boxplot_settings_changed` 信號

---

### 2. update_filter_settings()

**位置**: `throttle_line_chart_data_loader.py` L862-920

**調試輸出**:
```python
🔍🔍🔍 [update_filter_settings] Called with: pit=..., yellow=..., red=..., reprocess=...
🔍🔍🔍 [update_filter_settings] Current values BEFORE: pit=..., yellow=..., red=...
✅✅✅ [update_filter_settings] filter_pit_laps changed: ... → ...
✅✅✅ [update_filter_settings] Settings changed! New values: pit=..., yellow=..., red=...
🔄🔄🔄 [update_filter_settings] Reprocessing data with new filters...
✅✅✅ [update_filter_settings] Reprocessing completed successfully
```

**檢查重點**:
- 傳入的參數值是否正確
- 是否檢測到設定變更（changed=True）
- 如果 `reprocess=True`，是否成功重新處理數據
- 如果 `reprocess=False`，是否跳過了數據重建

---

### 3. _apply_filters()

**位置**: `throttle_line_chart_data_loader.py` L469-562

**調試輸出**:
```python
🔍🔍🔍 [_apply_filters] Starting filtering process...
🔍🔍🔍 [_apply_filters] Input lap_records count: 47
🔍🔍🔍 [_apply_filters] Filter settings: pit=True, yellow=True, red=True
🔍🔍🔍 [_apply_filters] Caution laps (Yellow Flag): {26, 27, 28}
🔍🔍🔍 [_apply_filters] Red flag laps: {35, 36}
🚫 [_apply_filters] Removed Yellow Flag lap: 26
🚫 [_apply_filters] Removed Red Flag lap: 35
🚫 [_apply_filters] Removed Pit Stop lap: 15
✅✅✅ [_apply_filters] Filtering completed:
  - Original laps: 47
  - Removed Pit: 3, Yellow: 3, Red: 2
  - Remaining laps: 39
```

**檢查重點**:
- 過濾設定是否正確（pit/yellow/red 的 True/False 值）
- 是否正確提取了 Yellow Flag 和 Red Flag 的圈數集合
- 是否真的移除了這些圈數（檢查 "Removed" 訊息）
- 過濾前後的圈數差異是否合理

---

### 4. _on_driver2_selection_changed()

**位置**: `throttle_line_chart_mdi.py` L822-874

**調試輸出**:
```python
================================================================================
🔍🔍🔍 [_on_driver2_selection_changed] Called with driver_code: NOR
🔍🔍🔍 [MDI] Current _global_filter_settings: {'filter_pit_laps': True, ...}
================================================================================

🔍🔍🔍 [_on_driver2_selection_changed] Creating temp_loader for Driver2...
🔍🔍🔍 [Driver2 Loader Created] Filter settings: pit=True, yellow=True, red=True
🔍🔍🔍 [_on_driver2_selection_changed] Calling temp_loader.load_data() for NOR...
```

**檢查重點**:
- `_global_filter_settings` 的值是否正確
- `temp_loader` 創建時的過濾設定是否正確
- 是否成功調用了 `load_data()`

---

### 5. _on_driver2_data_loaded()

**位置**: `throttle_line_chart_mdi.py` L876-902

**調試輸出**:
```python
================================================================================
🔍🔍🔍 [_on_driver2_data_loaded] Called
🔍🔍🔍 [_on_driver2_data_loaded] Data received: True
🔍🔍🔍 [_on_driver2_data_loaded] Data keys: ['metadata', 'driver', 'lap_records', ...]
🔍🔍🔍 [_on_driver2_data_loaded] lap_records count: 39
🔍🔍🔍 [_on_driver2_data_loaded] filters_applied: {'filter_pit_laps': True, ...}
================================================================================

🔍🔍🔍 [_on_driver2_data_loaded] Calling chart_widget.update_data()...
✅✅✅ [Driver2 Data Loaded] Successfully loaded data for NOR
```

**檢查重點**:
- 接收到的 `data` 是否包含所有必要的鍵
- `lap_records` 的數量是否已經過濾（應該少於原始圈數）
- `filters_applied` 的設定是否正確

---

### 6. _on_global_filter_settings_changed()

**位置**: `throttle_line_chart_mdi.py` L904-933

**調試輸出**:
```python
================================================================================
🔍🔍🔍 [_on_global_filter_settings_changed] Called
🔍🔍🔍 [MDI] Received settings: {'filter_pit_laps': True, ...}
================================================================================

🌐🌐🌐 [Global Settings Updated] New state: pit=True, yellow=True, red=True
🔍🔍🔍 [_on_global_filter_settings_changed] Updating Driver 1 filter settings...
✅✅✅ [_on_global_filter_settings_changed] Driver 1 updated
🔄🔄🔄 [Reload Driver2] Detected Driver2=NOR, reloading with new filter settings...
```

**檢查重點**:
- 接收到的 `settings` 值是否正確
- `_global_filter_settings` 是否成功更新
- 是否調用了 Driver 1 的 `update_filter_settings()`
- 如果 Driver 2 存在，是否觸發了重新載入

---

## 📋 測試步驟

### 測試場景 1: 初始載入（過濾啟用）

1. **開啟 Throttle Line Chart**
   - 檢查 `[DataLoader.__init__]` 輸出，確認初始過濾設定

2. **選擇 Driver 1: VER**
   - 檢查 `[_apply_filters]` 輸出，確認過濾是否生效
   - 記錄 "Original laps" 和 "Remaining laps" 的數量

3. **選擇 Driver 2: NOR**
   - 檢查 `[_on_driver2_selection_changed]` 輸出
   - 檢查 `[Driver2 Loader Created]` 的過濾設定
   - 檢查 `[_apply_filters]` 輸出（應該有兩次，一次 Driver 1，一次 Driver 2）
   - 檢查 `[_on_driver2_data_loaded]` 的 lap_records 數量

4. **檢查圖表**
   - 確認 VER 和 NOR 在 R/Y/P 標記處**沒有數據點**

---

### 測試場景 2: Driver 2 載入後改變設定

1. **開啟 Throttle Line Chart**
2. **選擇 Driver 1: VER**
3. **選擇 Driver 2: NOR**
4. **開啟 System Settings，勾選過濾選項**
   - 檢查 `[_on_global_filter_settings_changed]` 輸出
   - 確認 "Updating Driver 1 filter settings..." 出現
   - 確認 "Reload Driver2" 訊息出現
   - 檢查 `[_on_driver2_selection_changed]` 再次被調用
   - 檢查新的 `[_apply_filters]` 輸出（Driver 2 重新過濾）

5. **檢查圖表**
   - 確認 VER 和 NOR 在 R/Y/P 標記處**仍然沒有數據點**

---

### 測試場景 3: 改變設定後載入 Driver 2

1. **開啟 Throttle Line Chart**
2. **選擇 Driver 1: VER**
3. **開啟 System Settings，勾選過濾選項**
   - 檢查 `[_on_global_filter_settings_changed]` 輸出
   - 確認 "No Driver2 loaded, skipping reload" 訊息

4. **選擇 Driver 2: NOR**
   - 檢查 `[Driver2 Loader Created]` 的過濾設定（應該使用最新設定）
   - 檢查 `[_apply_filters]` 輸出

5. **檢查圖表**
   - 確認 VER 和 NOR 在 R/Y/P 標記處**沒有數據點**

---

## 🎯 問題診斷檢查表

### 如果 Driver 2 仍然顯示未過濾的數據

請檢查以下輸出：

#### 檢查點 1: temp_loader 的初始過濾設定

```
🔍🔍🔍 [Driver2 Loader Created] Filter settings: pit=?, yellow=?, red=?
```

**預期**: `pit=True, yellow=True, red=True`（如果過濾啟用）

**如果不正確**:
- 檢查 `settings_manager.get_boxplot_settings()` 的返回值
- 檢查 System Settings 是否真的勾選了過濾選項
- 檢查 `_global_filter_settings` 的值

---

#### 檢查點 2: _apply_filters 是否執行

```
🔍🔍🔍 [_apply_filters] Starting filtering process...
🔍🔍🔍 [_apply_filters] Filter settings: pit=?, yellow=?, red=?
```

**預期**: Filter settings 應該與 Driver2 Loader Created 的值一致

**如果不正確**:
- 檢查 `update_filter_settings()` 是否成功更新了屬性
- 檢查是否有其他地方修改了 `_filter_pit_laps` 等屬性

---

#### 檢查點 3: 過濾是否真的移除了圈數

```
🚫 [_apply_filters] Removed Yellow Flag lap: 26
🚫 [_apply_filters] Removed Red Flag lap: 35
🚫 [_apply_filters] Removed Pit Stop lap: 15
✅✅✅ [_apply_filters] Filtering completed:
  - Original laps: 47
  - Removed Pit: ?, Yellow: ?, Red: ?
  - Remaining laps: ?
```

**預期**: Removed 數量應該 > 0，Remaining laps < Original laps

**如果不正確**:
- 檢查 `extract_caution_laps()` 是否正確提取了 Yellow Flag 圈數
- 檢查 `extract_red_flag_laps()` 是否正確提取了 Red Flag 圈數
- 檢查 `lap_is_pit_stop()` 是否正確判斷了 Pit Stop

---

#### 檢查點 4: 數據傳遞到圖表

```
🔍🔍🔍 [_on_driver2_data_loaded] lap_records count: ?
```

**預期**: lap_records count 應該等於 "Remaining laps"

**如果不正確**:
- 檢查 `_process_data()` 是否正確處理了過濾後的數據
- 檢查 `chart_widget.update_data()` 是否正確接收了數據

---

#### 檢查點 5: 設定變更時 Driver 2 是否重新載入

```
🔄🔄🔄 [Reload Driver2] Detected Driver2=NOR, reloading with new filter settings...
```

**預期**: 當改變設定時，如果 Driver 2 已載入，應該看到此訊息

**如果沒有此訊息**:
- 檢查 `self.driver2` 是否為空
- 檢查 `_on_global_filter_settings_changed()` 是否被觸發

---

## 🔧 疑難排解

### 問題 1: temp_loader 的過濾設定是 False，但應該是 True

**可能原因**:
- `settings_manager.get_boxplot_settings()` 返回的值不正確
- System Settings 的勾選狀態沒有保存到 settings_manager

**解決方案**:
- 檢查 `core/gui_settings_manager.py` 的實現
- 確認 System Settings 的 checkbox 是否正確連接到 settings_manager

---

### 問題 2: _apply_filters 沒有移除任何圈數

**可能原因**:
- `extract_caution_laps()` 返回空集合
- `extract_red_flag_laps()` 返回空集合
- `lap_is_pit_stop()` 始終返回 False

**解決方案**:
- 檢查 `driver_payload` 是否包含正確的 flag 信息
- 檢查 `smart_markers_summary` 是否包含 Pit Stop 信息

---

### 問題 3: 設定變更時 Driver 2 沒有重新載入

**可能原因**:
- `self.driver2` 為空
- `_on_global_filter_settings_changed()` 沒有被觸發

**解決方案**:
- 確認 `_on_driver2_selection_changed()` 中正確設定了 `self.driver2 = driver_code`
- 確認 settings_manager 的 `boxplot_settings_changed` 信號正確發送

---

## 📊 預期的正常輸出範例

### 完整流程（Driver 2 載入 + 設定變更）

```
# 步驟 1: 開啟 Throttle Line Chart
🔍🔍🔍 [DataLoader.__init__] Initial filters from settings_manager: {'filter_pit_laps': True, 'filter_yellow_flags': True, 'filter_red_flags': True}
🔍🔍🔍 [DataLoader.__init__] Current filter attributes BEFORE update: pit=True, yellow=True, red=True
🔍🔍🔍 [DataLoader.__init__] Current filter attributes AFTER update: pit=True, yellow=True, red=True
🔍🔍🔍 [DataLoader.__init__] Successfully connected to boxplot_settings_changed signal

# 步驟 2: 選擇 Driver 1: VER
🔍🔍🔍 [_apply_filters] Starting filtering process...
🔍🔍🔍 [_apply_filters] Input lap_records count: 47
🔍🔍🔍 [_apply_filters] Filter settings: pit=True, yellow=True, red=True
🔍🔍🔍 [_apply_filters] Caution laps (Yellow Flag): {26, 27, 28}
🔍🔍🔍 [_apply_filters] Red flag laps: {35, 36}
🚫 [_apply_filters] Removed Yellow Flag lap: 26
🚫 [_apply_filters] Removed Yellow Flag lap: 27
🚫 [_apply_filters] Removed Yellow Flag lap: 28
🚫 [_apply_filters] Removed Red Flag lap: 35
🚫 [_apply_filters] Removed Red Flag lap: 36
🚫 [_apply_filters] Removed Pit Stop lap: 15
🚫 [_apply_filters] Removed Pit Stop lap: 30
🚫 [_apply_filters] Removed Pit Stop lap: 42
✅✅✅ [_apply_filters] Filtering completed:
  - Original laps: 47
  - Removed Pit: 3, Yellow: 3, Red: 2
  - Remaining laps: 39

# 步驟 3: 選擇 Driver 2: NOR
================================================================================
🔍🔍🔍 [_on_driver2_selection_changed] Called with driver_code: NOR
🔍🔍🔍 [MDI] Current _global_filter_settings: {'filter_pit_laps': True, 'filter_yellow_flags': True, 'filter_red_flags': True}
================================================================================

🔍🔍🔍 [_on_driver2_selection_changed] Creating temp_loader for Driver2...
🔍🔍🔍 [DataLoader.__init__] Initial filters from settings_manager: {'filter_pit_laps': True, 'filter_yellow_flags': True, 'filter_red_flags': True}
🔍🔍🔍 [Driver2 Loader Created] Filter settings: pit=True, yellow=True, red=True
🔍🔍🔍 [_apply_filters] Starting filtering process...
🔍🔍🔍 [_apply_filters] Input lap_records count: 47
🔍🔍🔍 [_apply_filters] Filter settings: pit=True, yellow=True, red=True
✅✅✅ [_apply_filters] Filtering completed:
  - Original laps: 47
  - Removed Pit: 3, Yellow: 3, Red: 2
  - Remaining laps: 39

================================================================================
🔍🔍🔍 [_on_driver2_data_loaded] Called
🔍🔍🔍 [_on_driver2_data_loaded] lap_records count: 39
✅✅✅ [Driver2 Data Loaded] Successfully loaded data for NOR
================================================================================

# 步驟 4: 改變 System Settings（取消勾選過濾）
================================================================================
🔍🔍🔍 [_on_global_filter_settings_changed] Called
🔍🔍🔍 [MDI] Received settings: {'filter_pit_laps': False, 'filter_yellow_flags': False, 'filter_red_flags': False}
================================================================================

🌐🌐🌐 [Global Settings Updated] New state: pit=False, yellow=False, red=False
🔍🔍🔍 [_on_global_filter_settings_changed] Updating Driver 1 filter settings...
✅✅✅ [update_filter_settings] filter_pit_laps changed: True → False
✅✅✅ [update_filter_settings] filter_yellow_flags changed: True → False
✅✅✅ [update_filter_settings] filter_red_flags changed: True → False
🔄🔄🔄 [update_filter_settings] Reprocessing data with new filters...
✅✅✅ [_apply_filters] Filtering completed:
  - Original laps: 47
  - Removed Pit: 0, Yellow: 0, Red: 0
  - Remaining laps: 47
✅✅✅ [_on_global_filter_settings_changed] Driver 1 updated
🔄🔄🔄 [Reload Driver2] Detected Driver2=NOR, reloading with new filter settings...

# Driver 2 重新載入
🔍🔍🔍 [_on_driver2_selection_changed] Called with driver_code: NOR
🔍🔍🔍 [Driver2 Loader Created] Filter settings: pit=False, yellow=False, red=False
✅✅✅ [_apply_filters] Filtering completed:
  - Original laps: 47
  - Removed Pit: 0, Yellow: 0, Red: 0
  - Remaining laps: 47
✅✅✅ [Driver2 Data Loaded] Successfully loaded data for NOR
```

---

## ✅ 測試完成後

將調試輸出貼到 Issue 或回覆中，我會根據輸出分析問題所在。

**特別關注**:
- Driver2 Loader Created 的過濾設定
- _apply_filters 的 Removed 數量
- _on_driver2_data_loaded 的 lap_records count
- 設定變更時是否觸發 Driver 2 重新載入
