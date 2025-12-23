# 煞車性能分析 - JSON 鍵值對照表

## 問題分析

GUI 顯示所有數據為 9999,原因是 **JSON 鍵值不匹配**!

複製 `all_drivers_straight_line_speed` 時,保留了加速度相關的鍵值,
但 CLI `brake_performance_analyzer.py` 輸出的是完全不同的鍵值結構。

---

## CLI 實際輸出的 JSON 結構

```json
{
  "success": true,
  "function_id": "34",
  "data": {
    "metadata": {
      "year": 2025,
      "race": "Australia",
      "session": "R",
      "analysis_type": "brake_performance"
    },
    "total_drivers": 17,
    "reference_brake_zone": {  // ← 不是 reference_segment!
      "driver": "NOR",
      "lap_number": 43,
      "brake_start_distance": 3995.57,
      "brake_end_distance": 4072.81,
      "brake_distance": 77.24,
      "brake_start_speed": 278.0,
      "brake_end_speed": 128.0,
      "speed_reduction": 150.0
    },
    "driver_brakes": [  // ← 不是 driver_speeds!
      {
        "driver": "NOR",
        "driver_number": 4,
        "team": "McLaren",
        "max_deceleration_ms2": 26.74,      // ← 不是 max_deceleration_kmh!
        "max_deceleration_g": 2.73,         // ← G力單位
        "brake_start_speed_kmh": 278.0,     // ← 不是 segment_start_speed_kmh!
        "brake_end_speed_kmh": 128.0,       // ← 不是 segment_end_speed_kmh!
        "speed_reduction_kmh": 150.0,       // ← 不是 segment_speed_gain_kmh!
        "brake_distance_m": 77.2,           // ← 不是 brake_distance_meters!
        "brake_time_s": 1.558,              // ← 不是 brake_time_seconds!
        "brake_start_position": 3995.6,
        "brake_end_position": 4072.8,
        "lap_number": 43,
        "in_core_range": true
      }
    ]
  }
}
```

---

## GUI 錯誤期望的鍵值 (當前問題)

### 1. **頂層數據源** (第 360 行)
```python
# ❌ 錯誤
self.driver_speeds_data = data.get("driver_speeds", [])

# ✅ 應該改為
self.driver_speeds_data = data.get("driver_brakes", [])
```

### 2. **參考區段** (第 346 行)
```python
# ❌ 錯誤
reference_segment = data.get("reference_segment", {})

# ✅ 應該改為
reference_brake_zone = data.get("reference_brake_zone", {})
```

並且參考區段的欄位也需要對應:
```python
# ❌ 錯誤
self.segment_distance_start = reference_segment.get("segment_distance_start")
self.segment_distance_end = reference_segment.get("segment_distance_end")
self.segment_length = reference_segment.get("segment_length")

# ✅ 應該改為
self.brake_start_distance = reference_brake_zone.get("brake_start_distance")
self.brake_end_distance = reference_brake_zone.get("brake_end_distance")
self.brake_distance = reference_brake_zone.get("brake_distance")
```

### 3. **車手數據欄位** (第 452-460 行)

| GUI 當前期望 (❌ 錯誤) | CLI 實際輸出 (✅ 正確) |
|----------------------|---------------------|
| `max_deceleration_kmh` | `max_deceleration_g` 或 `max_deceleration_ms2` |
| `brake_time_seconds` | `brake_time_s` |
| `brake_distance_meters` | `brake_distance_m` |
| `segment_start_speed_kmh` | `brake_start_speed_kmh` |
| `segment_end_speed_kmh` | `brake_end_speed_kmh` |
| `segment_speed_gain_kmh` | `speed_reduction_kmh` |
| `segment_avg_acceleration_ms2` | *(不存在,煞車是負加速度)* |

---

## 完整修正清單

### 修正 1: update_data() 方法 (第 335-360 行)
```python
# 修正數據源鍵值
metadata = data.get("metadata", {})
reference_brake_zone = data.get("reference_brake_zone", {})  # 改名
self.driver_speeds_data = data.get("driver_brakes", [])      # 改名

# 修正參考區段欄位
if reference_brake_zone:
    self.brake_start_distance = reference_brake_zone.get("brake_start_distance")
    self.brake_end_distance = reference_brake_zone.get("brake_end_distance")
    self.brake_distance = reference_brake_zone.get("brake_distance")
    self.reference_driver = reference_brake_zone.get("driver", "")
```

### 修正 2: _create_table_row() 方法 (第 450-460 行)
```python
driver = driver_data.get("driver", "")
team = driver_data.get("team", "")

# 修正所有欄位鍵值
max_deceleration_g = driver_data.get("max_deceleration_g", 0)
brake_start_speed = driver_data.get("brake_start_speed_kmh", None)
brake_end_speed = driver_data.get("brake_end_speed_kmh", None)
speed_reduction = driver_data.get("speed_reduction_kmh", None)
brake_distance = driver_data.get("brake_distance_m", None)
brake_time = driver_data.get("brake_time_s", None)
brake_start_pos = driver_data.get("brake_start_position", None)
```

### 修正 3: 表格欄位定義
需要重新定義表格的欄位,因為煞車分析和加速度分析是完全不同的概念:

**加速度分析欄位** (原始):
- 最高速度 (max_speed)
- 加速時間 (accel_time)
- 平均加速度 (avg_accel)
- 起始速度 (start_speed)
- 終點速度 (end_speed)

**煞車分析欄位** (應該):
- 最大減速度 (G) (max_deceleration_g)
- 煞車起始速度 (brake_start_speed_kmh)
- 煞車結束速度 (brake_end_speed_kmh)
- 速度降低 (speed_reduction_kmh)
- 煞車距離 (brake_distance_m)
- 煞車時間 (brake_time_s)
- 煞車開始位置 (brake_start_position)

---

## 建議修正策略

### 方案 A: 快速修正 (只改鍵值對應)
優點: 快速,風險小
缺點: 欄位名稱仍然是加速度相關

### 方案 B: 完整重構 (重新設計表格)
優點: 正確反映煞車性能概念
缺點: 需要較多修改

---

## 推薦: 方案 A + 欄位重命名

1. 先修正 JSON 鍵值對應 (解決 9999 問題)
2. 再修正表格欄位名稱和顯示邏輯
3. 保留表格結構和委派繪製邏輯

這樣可以:
- ✅ 立即解決 9999 顯示問題
- ✅ 保持表格視覺一致性
- ✅ 正確顯示煞車性能數據

---

**下一步**: 我可以幫你修正這些鍵值對應,你要我先修正哪一部分?
