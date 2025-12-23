# Straight Speed Analysis 動態欄位顯示功能實作任務

**日期**: 2025-10-20  
**狀態**: 🚧 進行中

---

## ✅ 已完成階段

### 階段 1: Settings Manager（完成 ✅）
- ✅ 新增 `StraightSpeedAnalysisSettings` dataclass
- ✅ 新增 `get_straight_speed_analysis_settings()` 方法
- ✅ 新增 `update_straight_speed_analysis_settings()` 方法
- ✅ 新增 `straight_speed_analysis_settings_changed` signal

### 階段 2: System Settings Dialog（完成 ✅）
- ✅ 新增 "Straight Speed Analysis" 分頁
- ✅ 新增 "All Drivers Speed" 群組（4 個 checkbox）
- ✅ 新增 "All Drivers Brake" 群組（3 個 checkbox）
- ✅ 實作 `_load_current_settings()` 載入設定
- ✅ 實作 `_reset_speed_analysis_defaults()` 重置預設值
- ✅ 實作 `_on_accept()` 儲存設定

---

## 🚧 待完成階段

### 階段 3: All Drivers Speed Table Widget
**檔案**: `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`

#### 3.1 欄位映射定義
```python
# 欄位索引映射（根據顯示狀態動態計算）
COLUMN_DRIVER = 0      # 永遠顯示
COLUMN_TEAM = 1        # 永遠顯示
COLUMN_MAX_SPEED = 2   # 可隱藏
COLUMN_ACCEL_TIME = 3  # 永遠顯示（必須）
COLUMN_AVG_ACCEL = 4   # 永遠顯示（必須）
COLUMN_START_SPEED = 5 # 可隱藏
COLUMN_MAX_SPEED_TIME = 6  # 可隱藏
COLUMN_PERFORMANCE_BAR = 7 # 可隱藏
```

#### 3.2 新增方法
- `__init__()` - 註冊 settings signal
- `_get_visible_columns()` - 返回可見欄位列表
- `_create_table_with_visible_columns()` - 根據設定創建表格
- `_get_column_index(logical_column)` - 獲取邏輯欄位的實際索引
- `_on_settings_changed(settings)` - 處理設定變更

#### 3.3 修改現有方法
- `_create_table()` - 使用 `_get_visible_columns()`
- `_populate_row()` - 使用 `_get_column_index()` 動態填充

---

### 階段 4: All Drivers Brake Table Widget
**檔案**: `modules/gui/all_drivers_brake_performance_analysis/all_drivers_brake_performance_table_widget.py`

#### 4.1 欄位映射定義
```python
COLUMN_DRIVER = 0      # 永遠顯示
COLUMN_TEAM = 1        # 永遠顯示
COLUMN_MAX_DECEL = 2   # 可隱藏
COLUMN_BRAKE_TIME = 3  # 永遠顯示（必須）
COLUMN_AVG_DECEL = 4   # 永遠顯示（必須）
COLUMN_START_SPEED = 5 # 可隱藏
COLUMN_PERFORMANCE_BAR = 6 # 可隱藏
```

#### 4.2 實作與 Speed Widget 相同的方法

---

## 📋 實作細節

### 欄位顯示邏輯

**All Drivers Speed:**
- 永遠顯示: Driver (0), Team (1), Accel Time (3), Avg Accel (4)
- 預設顯示: Performance Bar (7)
- 預設隱藏: Max Speed (2), Start Speed (5), Max Speed Time (6)

**All Drivers Brake:**
- 永遠顯示: Driver (0), Team (1), Brake Time (3), Avg Decel (4)
- 預設顯示: Performance Bar (6)
- 預設隱藏: Max Decel (2), Start Speed (5)

### 動態欄位計算範例

假設設定為：
```python
{
    "speed_show_max_speed": False,  # 隱藏
    "speed_show_start_speed": True,  # 顯示
    "speed_show_max_speed_time": False,  # 隱藏
    "speed_show_performance_bar": True  # 顯示
}
```

實際欄位順序：
```
0. Driver (永遠)
1. Team (永遠)
2. Accel Time (永遠)
3. Avg Accel (永遠)
4. Start Speed (顯示)
5. Performance Bar (顯示)
```

邏輯欄位 5 (Start Speed) 映射到實際欄位 4
邏輯欄位 7 (Performance Bar) 映射到實際欄位 5

---

## 🧪 測試計劃

### 測試 1: Settings Dialog
1. 開啟 Tool → System Settings
2. 切換到 "Straight Speed Analysis" 分頁
3. 驗證預設值（Performance Bar 勾選，其他未勾選）
4. 修改設定後按 OK
5. 重新開啟 System Settings，驗證設定已儲存

### 測試 2: Speed Widget 欄位顯示
1. 開啟 All Drivers Speed 模組
2. 驗證預設只顯示：Driver, Team, Accel Time, Avg Accel, Performance Bar
3. 修改 System Settings，勾選 Max Speed
4. 關閉並重新開啟 All Drivers Speed
5. 驗證 Max Speed 欄位已顯示

### 測試 3: Brake Widget 欄位顯示
1. 開啟 All Drivers Brake 模組
2. 驗證預設只顯示：Driver, Team, Brake Time, Avg Decel, Performance Bar
3. 修改 System Settings，隱藏 Performance Bar
4. 關閉並重新開啟 All Drivers Brake
5. 驗證 Performance Bar 已隱藏

### 測試 4: 排序功能
1. 在隱藏部分欄位的情況下
2. 測試所有可見欄位的排序功能
3. 驗證排序正確且不影響隱藏欄位

---

## 📝 注意事項

1. **必須顯示欄位**：Accel Time, Avg Accel, Brake Time, Avg Decel 永遠不可隱藏
2. **車手和車隊**：永遠顯示，不在設定中
3. **實時更新**：關閉 System Settings 後生效（新開啟的視窗）
4. **欄位索引**：使用動態計算，不要硬編碼
5. **向後兼容**：如果設定不存在，使用預設值

---

## 🔍 下一步行動

執行階段 3 和階段 4 的實作...
