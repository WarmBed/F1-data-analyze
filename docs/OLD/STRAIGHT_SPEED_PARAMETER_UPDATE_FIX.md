# 參數更新觸發問題診斷報告

## 問題描述
用戶報告：在主 GUI 變更 race 時，`all_drivers_straight_line_speed` 模組沒有觸發更新。

---

## 根因分析

### 問題發現
在 `f1t_gui_main.py` 的 `update_all_lap_analysis()` 方法中（第 7145 行），定義了需要更新的模組類型：

```python
session_only_types = {
    'rain_weather', 'pitstop', 'accident', 'tire', 'ideal_lap',
    'ideal_lap_ranking', 'ideal_lap_sector_comparison', 'ideal_lap_sector_heatmap',
    'laptime_boxplot', 'throttle_boxplot', 'track_analysis'
}
```

**問題**：這個集合中**缺少 `'all_drivers_straight_line_speed'`**！

### 模組註冊確認
在 `all_drivers_straight_line_speed_mdi.py` 中：
```python
analysis_type="all_drivers_straight_line_speed"
```

### 參數更新流程
```
1. 用戶變更 race ComboBox
    ↓
2. on_race_changed() 被觸發
    ↓
3. _schedule_parameter_broadcast("race_changed")
    ↓
4. 350ms 延遲後調用 _broadcast_pending_parameters()
    ↓
5. on_race_parameters_changed()
    ↓
6. update_all_lap_analysis()
    ↓
7. 檢查模組類型是否在 session_only_types 中
    ↓
8. ❌ all_drivers_straight_line_speed 不在列表中
    ↓
9. ❌ 被跳過，不會調用 update_parameters()
```

### 與 ideal_lap_sector_comparison 對比

| 項目 | ideal_lap_sector_comparison | all_drivers_straight_line_speed |
|------|----------------------------|--------------------------------|
| analysis_type | `"ideal_lap_sector_comparison"` | `"all_drivers_straight_line_speed"` |
| 是否在 all_analysis_types | ✅ 是 | ✅ 是 |
| 是否在 session_only_types | ✅ 是 | ❌ **不是（問題所在）** |
| 更新方法調用 | ✅ 會被調用 | ❌ 不會被調用 |

---

## 修正方案

### 方案 1：添加到 session_only_types（推薦）
在 `f1t_gui_main.py` 的兩個位置添加 `'all_drivers_straight_line_speed'`：

#### 位置 1：`_get_telemetry_analysis_windows()` - 第 7056 行
```python
all_analysis_types = {
    # ... 其他類型
    'ideal_lap_sector_comparison', # 理想圈分段對比
    'ideal_lap_sector_heatmap',    # 理想圈分段熱力圖
    'track_analysis',  # 賽道分析
    'all_drivers_straight_line_speed',  # ✅ 新增：全車手直線速度
}
```

#### 位置 2：`update_all_lap_analysis()` - 第 7145 行
```python
session_only_types = {
    'rain_weather', 'pitstop', 'accident', 'tire', 'ideal_lap',
    'ideal_lap_ranking', 'ideal_lap_sector_comparison', 'ideal_lap_sector_heatmap',
    'laptime_boxplot', 'throttle_boxplot', 'track_analysis',
    'all_drivers_straight_line_speed',  # ✅ 新增：全車手直線速度
}
```

#### 位置 3：`update_all_lap_analysis()` - 第 7035 行
```python
all_analysis_types = {
    # ... 其他類型
    'ideal_lap_sector_comparison', # 理想圈分段對比
    'ideal_lap_sector_heatmap',    # 理想圈分段熱力圖
    'track_analysis',  # 賽道分析
    'all_drivers_straight_line_speed',  # ✅ 新增：全車手直線速度
}
```

---

## 修正後的流程

```
1. 用戶變更 race ComboBox
    ↓
2. on_race_changed() 被觸發
    ↓
3. _schedule_parameter_broadcast("race_changed")
    ↓
4. 350ms 延遲後調用 _broadcast_pending_parameters()
    ↓
5. on_race_parameters_changed()
    ↓
6. update_all_lap_analysis()
    ↓
7. 檢查模組類型是否在 session_only_types 中
    ↓
8. ✅ all_drivers_straight_line_speed 在列表中
    ↓
9. ✅ 調用 update_parameters(year, race, session)
    ↓
10. ✅ 基類 UniversalAnalysisMDI.update_parameters() 處理
    ↓
11. ✅ _load_data_with_current_parameters() 觸發
    ↓
12. ✅ data_manager.load_data() 重新載入數據
```

---

## 修正檔案
- `f1t_gui_main.py`
  - 第 7056 行：添加到 `all_analysis_types`（`_get_telemetry_analysis_windows` 方法）
  - 第 7035 行：添加到 `all_analysis_types`（`update_all_lap_analysis` 方法）
  - 第 7145 行：添加到 `session_only_types`（`update_all_lap_analysis` 方法）

---

## 測試驗證

### 驗證步驟
1. 啟動主 GUI
2. 打開 "All Drivers Straight Line Speed" 模組
3. 在主 GUI 變更 race ComboBox
4. 觀察模組是否自動重新載入數據

### 預期結果
- ✅ 模組應該顯示「正在載入...」狀態
- ✅ 調用 API 或讀取對應 race 的 JSON 檔案
- ✅ 表格更新為新 race 的數據

### 調試日誌
修正後應該看到以下日誌：
```
🔍 [BATCH_DEBUG] 模組 X/N: analysis_type=all_drivers_straight_line_speed
🔍 [BATCH_DEBUG] 識別為賽事級模組
🔍 [BATCH_DEBUG] 嘗試調用 update_parameters, kwargs={'year': '2025', 'race': 'Singapore', 'session': 'Q'}
🚨 [BASE_CRITICAL] _load_data_with_current_parameters 被調用
🚨 [BASE_CRITICAL] 調用 data_manager.load_data({'year': 2025, 'race': 'Singapore', 'session': 'Q'})
```

---

**診斷完成時間**: 2025-10-14
**根因**: `all_drivers_straight_line_speed` 未在 `session_only_types` 列表中
**修正方案**: 添加到三個 `all_analysis_types` 集合中
**影響範圍**: 參數自動更新功能
