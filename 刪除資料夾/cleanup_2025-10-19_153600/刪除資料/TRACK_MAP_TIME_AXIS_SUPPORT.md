# Track Map 時間軸支援實作完成報告

**日期**: 2025-10-12  
**狀態**: ✅ 實作完成，待測試

---

## 📋 需求說明

當使用者在 Lap Analysis 模組勾選 `[ ] Use time axis` 時，需要讓 Track Map 也能：
1. 同步切換到時間軸模式
2. 接收時間值（秒）而非距離值（公尺）
3. 正確在賽道地圖上顯示對應位置的標記

---

## ✅ 實作內容

### 1. **CLI 功能 2 加入時間戳**（已完成）

#### 修改檔案：`CLI_modules/cli/analyzer/track_position_analysis.py`

**變更內容**：
- ✅ 從 FastF1 `pos_data` 或 `car_data` 提取 `Time` 或 `SessionTime` 欄位
- ✅ 將 pandas Timedelta 轉換為秒數存入 `time_seconds`
- ✅ 更新 JSON 輸出包含 `time_reference: "seconds_from_lap_start"`

**JSON 結構範例**：
```json
{
  "point_index": 1,
  "distance_m": 0.0,
  "position_x": -1244.0,
  "position_y": -1287.0,
  "time_seconds": 0.07  // ✅ 新增時間戳
}
```

---

### 2. **TrackMapWidget 時間軸支援**（已完成）

#### 修改檔案：`modules/gui/track_analysis/track_map_widget.py`

**新增屬性**：
```python
self._use_time_axis: bool = False  # 當前是否使用時間軸模式
self._time_lookup: List[Tuple[float, float, float]] = []  # 時間查找表 (time, x, y)
self._time_values: List[float] = []  # 時間值列表（用於二分搜索）
self._time_available: bool = False  # 是否有時間數據可用
```

**新增方法**：

1. **`set_time_axis_mode(use_time_axis: bool) -> bool`**
   - 設置時間軸模式
   - 如果沒有時間數據則返回 `False`
   - 切換時清除現有標記避免單位混淆

2. **`is_time_axis_mode() -> bool`**
   - 返回當前是否使用時間軸

3. **`is_time_axis_available() -> bool`**
   - 返回是否有時間數據可用

4. **`_find_world_coordinate_by_time(time_value: float) -> Optional[Tuple[float, float]]`**
   - 基於時間值查找世界座標（線性插值）
   - 與 `_find_world_coordinate()` 邏輯相同，但使用時間查找表

5. **`_update_dynamic_marker_by_time(time_value: float)`**
   - 基於時間值更新動態標記（滑鼠懸停）

6. **`_update_fixed_marker_by_time(time_value: float)`**
   - 基於時間值更新固定標記（點擊）

**修改的方法**：

1. **`_build_distance_lookup()`**
   - 同時建立距離和時間的查找表
   - 檢測 `time_seconds` 欄位是否存在
   - 設置 `_time_available` 標記

2. **`on_x_linkage_received(distance_or_time_value, y_relative)`**
   - 根據當前模式自動選擇使用距離或時間查找
   - 時間軸模式：調用 `_update_dynamic_marker_by_time()`
   - 距離軸模式：調用 `_update_dynamic_marker()`

3. **`on_click_linkage_received(distance_or_time_value)`**
   - 根據當前模式自動選擇使用距離或時間查找
   - 時間軸模式：調用 `_update_fixed_marker_by_time()`
   - 距離軸模式：調用 `_update_fixed_marker()`

---

### 3. **LinkageManager 時間軸廣播**（已完成）

#### 修改檔案：`modules/gui/lap_analysis/linkage/linkage_manager.py`

**新增信號**：
```python
time_axis_mode_changed = pyqtSignal(bool)  # 時間軸模式變更信號
```

**新增屬性**：
```python
self.time_axis_mode: bool = False  # 當前時間軸模式
```

**新增方法**：

1. **`set_time_axis_mode(use_time_axis: bool)`**
   - 設置時間軸模式並廣播給所有註冊的模組
   - 調用每個模組的 `set_time_axis_mode()` 方法
   - 發送 `time_axis_mode_changed` 信號

2. **`is_time_axis_mode() -> bool`**
   - 返回當前時間軸模式狀態

---

## 🔄 連動流程

### 場景 1：使用者在 Lap Analysis 勾選 "Use time axis"

```
[Speed Analysis MDI]
  └─> 勾選 checkbox.setChecked(True)
      └─> _on_time_axis_toggled(Qt.Checked)
          └─> chart_widget.toggle_time_axis(True)
              └─> set_time_axis_mode(True)
                  └─> linkage_manager.set_time_axis_mode(True)  // 廣播
                      └─> [所有註冊模組].set_time_axis_mode(True)
                          ├─> [Throttle Analysis] ✅
                          ├─> [RPM Analysis] ✅
                          ├─> [Gear Analysis] ✅
                          └─> [Track Map] ✅ 同步切換
```

### 場景 2：滑鼠在圖表上移動（時間軸模式）

```
[Speed Chart Widget]
  └─> mouseMoveEvent(event)
      └─> time_value = 45.5  // 秒
          └─> linkage_manager.send_x_linkage(45.5, 0.6)
              └─> [Track Map].on_x_linkage_received(45.5, 0.6)
                  └─> 檢查 self._use_time_axis == True
                      └─> _update_dynamic_marker_by_time(45.5)
                          └─> _find_world_coordinate_by_time(45.5)
                              └─> 查找 _time_lookup，找到對應位置
                                  └─> 顯示綠色標記 ●
```

### 場景 3：切回距離軸模式

```
[Speed Analysis MDI]
  └─> 取消勾選 checkbox.setChecked(False)
      └─> _on_time_axis_toggled(Qt.Unchecked)
          └─> chart_widget.toggle_time_axis(False)
              └─> set_time_axis_mode(False)
                  └─> linkage_manager.set_time_axis_mode(False)
                      └─> [Track Map].set_time_axis_mode(False)
                          └─> 清除標記，恢復距離軸模式 ✅
```

---

## 📊 數據結構

### CLI JSON 輸出（功能 2）

```json
{
  "data": {
    "position_records": [
      {
        "point_index": 1,
        "distance_m": 0.0,
        "position_x": -1244.0,
        "position_y": -1287.0,
        "time_seconds": 0.07
      },
      {
        "point_index": 2,
        "distance_m": 1301.485,
        "position_x": -2187.0,
        "position_y": -390.0,
        "time_seconds": 1.71
      }
      // ... 50 個點
    ]
  },
  "cache_used": false,
  "function_id": "2"
}
```

### Track Map 內部查找表

```python
# 距離查找表
self._distance_lookup = [
    (0.0, -1244.0, -1287.0),        # (distance_m, x, y)
    (1301.485, -2187.0, -390.0),
    ...
]
self._distance_values = [0.0, 1301.485, ...]  # 用於 bisect_left

# 時間查找表
self._time_lookup = [
    (0.07, -1244.0, -1287.0),       # (time_seconds, x, y)
    (1.71, -2187.0, -390.0),
    ...
]
self._time_values = [0.07, 1.71, ...]  # 用於 bisect_left
```

---

## 🎯 關鍵技術細節

### 1. **線性插值算法**

兩種模式使用相同的插值邏輯，只是查找表不同：

```python
def _find_world_coordinate_by_time(self, time_value: float):
    idx = bisect_left(self._time_values, time_value)
    
    # 邊界處理
    if idx <= 0: return self._time_lookup[0][1], self._time_lookup[0][2]
    if idx >= len(self._time_lookup): return self._time_lookup[-1][1], self._time_lookup[-1][2]
    
    # 線性插值
    prev_time, prev_x, prev_y = self._time_lookup[idx - 1]
    next_time, next_x, next_y = self._time_lookup[idx]
    
    ratio = (time_value - prev_time) / (next_time - prev_time)
    interp_x = prev_x + (next_x - prev_x) * ratio
    interp_y = prev_y + (next_y - prev_y) * ratio
    
    return interp_x, interp_y
```

### 2. **雙查找表管理**

- **距離查找表**：始終建立，用於距離軸模式
- **時間查找表**：僅當 JSON 包含 `time_seconds` 時建立
- **自動降級**：如果沒有時間數據，`set_time_axis_mode(True)` 返回 `False`

### 3. **標記清除策略**

切換時間軸模式時自動清除現有標記，避免：
- 距離值被誤用為時間值
- 時間值被誤用為距離值
- 標記位置錯亂

---

## 🧪 測試建議

### 單元測試

1. **時間數據載入測試**
   ```python
   # 測試有時間數據的 JSON
   widget.load_track_data(json_with_time)
   assert widget.is_time_axis_available() == True
   
   # 測試無時間數據的 JSON
   widget.load_track_data(json_without_time)
   assert widget.is_time_axis_available() == False
   ```

2. **模式切換測試**
   ```python
   # 有時間數據時可以切換
   assert widget.set_time_axis_mode(True) == True
   assert widget.is_time_axis_mode() == True
   
   # 無時間數據時無法切換
   assert widget.set_time_axis_mode(True) == False
   assert widget.is_time_axis_mode() == False  # 保持原狀態
   ```

3. **座標查找測試**
   ```python
   # 時間軸模式
   widget.set_time_axis_mode(True)
   pos = widget._find_world_coordinate_by_time(45.5)
   assert pos is not None
   
   # 距離軸模式
   widget.set_time_axis_mode(False)
   pos = widget._find_world_coordinate(5000.0)
   assert pos is not None
   ```

### 整合測試

1. **GUI 啟動 F1T → Track Analysis**
2. **載入 2025 Australia R 數據**
3. **開啟 Speed Analysis**
4. **勾選 "Use time axis"**
5. **移動滑鼠到圖表上**
6. **觀察 Track Map 標記是否同步移動** ✅
7. **取消勾選 "Use time axis"**
8. **再次移動滑鼠**
9. **觀察標記是否仍然同步（距離模式）** ✅

---

## 📝 相容性說明

### 向後相容

- ✅ 沒有時間數據的舊 JSON 仍然可用（僅距離軸模式）
- ✅ 未實作 `set_time_axis_mode()` 的模組不受影響
- ✅ LinkageManager 的現有 API 完全保留

### 混合模式支援

- ✅ Lap Analysis 模組可以各自切換時間軸
- ✅ Track Map 自動跟隨 LinkageManager 的全域設定
- ✅ 如果某個模組沒有時間數據，會自動保持距離軸模式

---

## 🔗 相關檔案

### 修改的檔案
1. `CLI_modules/cli/analyzer/track_position_analysis.py` - CLI 功能 2 加入時間戳
2. `modules/gui/track_analysis/track_map_widget.py` - Track Map 時間軸支援
3. `modules/gui/lap_analysis/linkage/linkage_manager.py` - LinkageManager 時間軸廣播

### 參考實現
1. `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py` - 時間軸切換範例
2. `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py` - 連動信號發送

---

## 🚀 下一步

1. **執行整合測試** - 驗證 GUI 中的時間軸切換功能
2. **性能測試** - 確保時間查找表的效率（50-500 個點）
3. **錯誤處理** - 測試邊界條件（無數據、單點數據、逆序數據）
4. **文檔更新** - 更新 copilot-instructions.md

---

**狀態**: ✅ 代碼實作完成，等待測試驗證
