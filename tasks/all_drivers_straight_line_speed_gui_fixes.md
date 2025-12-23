# 全車手直線速度分析 GUI 修復報告

## 修復日期
2025-10-14

## 問題描述

### 問題 1: 棒狀圖虛線延伸未顯示
- **現象**: 用戶報告棒狀圖沒有顯示虛線延伸
- **原因**: 
  1. JSON 鍵名不匹配：代碼使用 `"time"`, `"distance"`, `"avg_acceleration"`
  2. 實際 JSON 使用：`"time_seconds"`, `"distance_meters"`, `"avg_acceleration_ms2"`
  3. 導致 `time_to_max = 0.0`，不符合繪製條件 `if time_to_max < self.max_time`

### 問題 2: 缺少 X 軸刻度和標籤
- **現象**: 棒狀圖沒有時間軸刻度（0s, 2s, 4s, 6s, 8s, 10s）
- **原因**: QTableWidget Delegate 沒有實現 X 軸刻度繪製邏輯

## 修復方案

### 修復 1: JSON 鍵名映射（兩處）

#### 位置 1: `_calculate_max_time()` 方法
```python
# ✅ 修正鍵名：JSON 使用 "time_seconds" 不是 "time"
accel_100_300_time = accel_data.get("time_seconds", accel_data.get("time", 0))
```

#### 位置 2: `_populate_row()` 方法
```python
# ✅ 修正鍵名：JSON 格式使用不同的鍵名
accel_100_300_time = accel_data.get("time_seconds", accel_data.get("time", 0))
accel_distance = accel_data.get("distance_meters", accel_data.get("distance", 0))
accel_avg = accel_data.get("avg_acceleration_ms2", accel_data.get("avg_acceleration", 0))
```

### 修復 2: 虛線繪製增強

#### AccelerationBarDelegate.paint() 方法
```python
# ✅ 繪製虛線延伸（從棒狀圖終點到最大寬度）
if time_to_max < self.max_time:
    painter.setPen(QPen(QColor(150, 150, 150), 2, Qt.DashLine))  # 增加線寬到 2
    dash_y = option.rect.y() + 5 + bar_height // 2
    painter.drawLine(
        int(option.rect.x() + 5 + bar_width),
        dash_y,
        int(option.rect.x() + 5 + bar_max_width),
        dash_y
    )
```

### 修復 3: X 軸刻度實現

#### 新增刻度繪製邏輯（只在第一行顯示）
```python
# ✅ 繪製 X 軸刻度（只在第一行繪製）
if index.row() == 0:
    painter.setFont(QFont("Arial", 7))
    painter.setPen(QPen(QColor(100, 100, 100)))
    
    # X 軸基線
    axis_y = option.rect.y() + 5 + bar_height + 2
    painter.drawLine(
        int(option.rect.x() + 5),
        axis_y,
        int(option.rect.x() + 5 + bar_max_width),
        axis_y
    )
    
    # 刻度標記（0s, 2s, 4s, 6s, 8s, 10s）
    num_ticks = 6
    for i in range(num_ticks):
        tick_time = (self.max_time / (num_ticks - 1)) * i
        tick_x = int(option.rect.x() + 5 + (bar_max_width / (num_ticks - 1)) * i)
        
        # 刻度線
        painter.drawLine(tick_x, axis_y, tick_x, axis_y + 3)
        
        # 刻度文字
        painter.drawText(tick_x - 10, axis_y + 12, f"{tick_time:.1f}s")
```

### 修復 4: UI 調整

#### 增加行高以容納 X 軸
```python
# 1. 預設行高增加
table.verticalHeader().setDefaultSectionSize(40)  # 從 35 增加�� 40

# 2. 第一行更高（顯示 X 軸刻度）
if row_count > 0:
    self.table.setRowHeight(0, 55)  # 第一行 55 像素

# 3. 欄位寬度調整
table.setColumnWidth(4, 450)  # 從 400 增加到 450
```

## 測試驗證

### 測試案例
- **Demo 1**: `demo_japan_q.py` - 2024 Japan Q
- **數據來源**: `json/all_drivers_straight_line_speed_2024_Japan_Q.json`
- **車手數量**: 20

### 預期結果
✅ **棒狀圖顯示**:
- 綠色實心棒（< 7.0s）
- 黃色實心棒（7.0-8.0s）
- 橙色實心棒（> 8.0s）

✅ **虛線延伸**:
- 從實心棒終點延伸到最大寬度
- 灰色虛線（150, 150, 150）
- 線寬 2 像素

✅ **X 軸刻度**（只在第一行）:
- 0.0s, 2.0s, 4.0s, 6.0s, 8.0s, 10.0s
- 灰色文字（Arial 7pt）
- 刻度線 3 像素高

✅ **數值文字**:
- 格式："7.12s → 328.5 km/h"
- 黑色粗體（Arial 8pt Bold）
- 位置：棒狀圖右側

## 代碼清理

### 移除的調試輸出
1. `_calculate_max_time()` 中的 `[DEBUG_DATA]` 輸出
2. `AccelerationBarDelegate.paint()` 中的 `[DELEGATE_DEBUG]` 輸出
3. `_populate_row()` 中的 `[DEBUG]` 輸出（保留第一行用於驗證）

## 檔案變更清單

### 主要修改檔案
1. `all_drivers_straight_line_speed_table_widget.py`
   - AccelerationBarDelegate.paint() - 新增虛線和 X 軸繪製
   - _calculate_max_time() - 修正 JSON 鍵名
   - _populate_row() - 修正 JSON 鍵名
   - _populate_table() - 設置第一行行高
   - _create_table() - 調整欄位寬度和預設行高

### 未修改檔案
- `all_drivers_straight_line_speed_mdi.py` - 無需變更
- `all_drivers_straight_line_speed_data_loader.py` - 無需變更
- Demo 檔案（5 個）- 無需變更

## 後續建議

### 功能增強
1. **可選 X 軸顯示**: 添加 UI 選項控制是否顯示 X 軸（預設開啟）
2. **刻度間隔自適應**: 根據 max_time 動態調整刻度數量和間隔
3. **多行 X 軸**: 考慮在每 5 行顯示一次 X 軸，提高可讀性
4. **工具提示**: 添加 QToolTip 顯示詳細加速數據

### 性能優化
1. **委託緩存**: 緩存顏色和字體對象，避免重複創建
2. **條件繪製**: 只在可見區域繪製刻度，減少繪製開銷

### 國際化
1. **X 軸標籤**: 單位 "s" 應使用 `tr()` 函數
2. **數值格式**: 考慮不同語言的數字和單位格式

## 驗證檢查清單

測試完成前必須驗證：
- [x] ✅ JSON 鍵名映射正確（time_seconds, distance_meters, avg_acceleration_ms2）
- [x] ✅ 棒狀圖顯示實心顏色
- [ ] ⏳ 虛線延伸顯示（需用戶截圖確認）
- [ ] ⏳ X 軸刻度顯示（需用戶截圖確認）
- [ ] ⏳ 第一行行高正確（55px）
- [x] ✅ 其他行行高正確（40px）
- [x] ✅ 欄位寬度適當（450px）
- [x] ✅ 調試輸出已清理

## 備註

### JSON 數據格式（CLI Function 48 輸出）
```json
{
  "driver": "VER",
  "team": "Red Bull Racing",
  "max_speed_kmh": 328.0,
  "acceleration_100_300": {
    "time_seconds": 1.2,
    "distance_meters": 97.99,
    "avg_acceleration_ms2": 46.3
  }
}
```

### 計算公式
```python
# 線性加速假設
speed_range_100_300 = 200  # 300 - 100
speed_range_100_max = max_speed - 100
time_to_max = (speed_range_100_max / speed_range_100_300) * accel_100_300_time
```

---

**修復狀態**: ✅ 代碼修復完成，等待用戶視覺驗證
**下一步**: 等待用戶截圖確認虛線和 X 軸刻度是否正常顯示
