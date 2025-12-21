# Function 48 Segment 加速功能改進提案

## 📌 問題現況

### 當前實現（2025-10-18）
```
參考範圍模式：
├─ 起點：參考車手的 segment_distance_start (5654m)
├─ 終點：參考車手的 segment_distance_end (6291m)
└─ 問題：只有在此範圍內達到最高速度的車手才有數據

結果：
├─ Japan 賽事：90% 車手 (18/20) 的 Segment 數據為 NULL
├─ 只有 PIA 和 STR 有數據（最高速度較低，恰好在範圍內）
└─ 數據利用率極低
```

---

## 🎯 改進方案：硬編碼起點 + 動態終點模式

### 核心概念
```
每位車手的 Segment 數據計算：
├─ 起點：固定的硬編碼距離（例如 5000m，代表直線段開始）
├─ 終點：該車手在這圈達到的最高速度點
└─ 計算：從起點加速到最高速度的性能

優勢：
├─ ✅ 100% 車手都有 Segment 數據（0% NULL）
├─ ✅ 起點相同，數據具有可比性
├─ ✅ 終點動態，反映每位車手的真實最高速度
└─ ✅ 真實反映加速能力差異
```

---

## 📊 實現邏輯

### 步驟 1：確定硬編碼起點
```python
# 選項 A：使用賽道特定位置（推薦）
HARDCODED_START_DISTANCE = 5000.0  # 米，代表某個關鍵點

# 選項 B：使用參考車手的起點（保持當前邏輯）
if reference_segment:
    HARDCODED_START_DISTANCE = reference_segment["segment_distance_start"]
else:
    HARDCODED_START_DISTANCE = 5000.0  # 預設值
```

### 步驟 2：為每位車手計算動態終點
```python
def _calculate_segment_acceleration_improved(
    self,
    car_data: pd.DataFrame,
    hardcoded_start_distance: float,
    max_speed_distance: float  # ← 新增：該車手的最高速度測量點
) -> Optional[Dict[str, Any]]:
    """
    改進版 Segment 加速計算
    
    Args:
        car_data: 車手遙測數據
        hardcoded_start_distance: 硬編碼起點距離（固定）
        max_speed_distance: 該車手最高速度測量點（動態終點）
    
    Returns:
        包含加速性能的字典，保證不為 None（除非數據無效）
    """
    try:
        # 確保終點在起點之後
        if max_speed_distance <= hardcoded_start_distance:
            # 如果最高速度點在起點之前，向後搜尋 200m
            max_speed_distance = hardcoded_start_distance + 200.0
        
        # 找到起點和終點的實際測量點
        start_idx = self._find_closest_distance_index(
            car_data, hardcoded_start_distance
        )
        end_idx = self._find_closest_distance_index(
            car_data, max_speed_distance
        )
        
        # 確保索引有效
        if start_idx is None or end_idx is None or start_idx >= end_idx:
            return None
        
        # 獲取速度和時間數據
        start_speed = car_data.loc[start_idx, "Speed"]
        end_speed = car_data.loc[end_idx, "Speed"]
        start_time = car_data.loc[start_idx, "Time"]
        end_time = car_data.loc[end_idx, "Time"]
        start_distance_actual = car_data.loc[start_idx, "Distance"]
        end_distance_actual = car_data.loc[end_idx, "Distance"]
        
        # 計算加速性能
        time_diff = self._calculate_time_diff(start_time, end_time)
        if time_diff <= 0:
            return None
        
        speed_change_kmh = float(end_speed - start_speed)
        speed_change_ms = speed_change_kmh / 3.6
        avg_acceleration = speed_change_ms / time_diff
        segment_length = float(end_distance_actual - start_distance_actual)
        
        return {
            "time_seconds": round(time_diff, 3),
            "distance_meters": round(segment_length, 2),
            "avg_acceleration_ms2": round(avg_acceleration, 2),
            "start_speed_kmh": round(float(start_speed), 1),
            "end_speed_kmh": round(float(end_speed), 1),
            "speed_gain_kmh": round(speed_change_kmh, 1),
            "actual_distance_start": round(float(start_distance_actual), 1),
            "actual_distance_end": round(float(end_distance_actual), 1),
            "mode": "hardcoded_start_dynamic_end"  # 標記計算模式
        }
        
    except Exception as e:
        print(f"[WARNING] Segment 加速計算失敗: {e}")
        return None
```

### 步驟 3：調用新邏輯
```python
# 在 _analyse_driver_max_speed_telemetry 方法中
def _analyse_driver_max_speed_telemetry(...):
    # ... 現有代碼 ...
    
    # 獲取該車手的最高速度測量點
    max_speed_distance = self._safe_float(car_data, max_speed_idx, "Distance")
    
    # ⭐ 使用改進版 Segment 計算
    segment_acceleration_data = self._calculate_segment_acceleration_improved(
        car_data=car_data,
        hardcoded_start_distance=HARDCODED_START_DISTANCE,  # 固定起點
        max_speed_distance=max_speed_distance  # 動態終點
    )
    
    # ... 其他代碼 ...
```

---

## 📈 預期效果

### Japan 賽事改進前後對比

| 項目 | 改進前 | 改進後 |
|------|--------|--------|
| **有 Segment 數據的車手** | 2/20 (10%) | 20/20 (100%) ✅ |
| **NULL 值比例** | 90% | 0% ✅ |
| **數據可比性** | 低（只有 2 個樣本） | 高（所有車手相同起點） ✅ |
| **反映真實性能** | 僅限低速車手 | 所有車手的完整加速過程 ✅ |

### 範例輸出

**改進後的 JSON 數據**：
```json
{
  "driver": "VER",
  "max_speed_kmh": 314.0,
  "distance_m": 6328.2,
  "segment_accel_time_seconds": 2.15,        // ← 保證有數據
  "segment_accel_distance_meters": 1328.2,   // 從 5000m 到 6328.2m
  "segment_avg_acceleration_ms2": 3.85,
  "segment_start_speed_kmh": 180.0,          // 在 5000m 的速度
  "segment_end_speed_kmh": 314.0,            // 最高速度
  "segment_speed_gain_kmh": 134.0
}
```

**所有 20 位車手都會有類似數據**，只是終點距離和最高速度不同。

---

## 🔧 實現步驟

### 階段 1：修改核心邏輯（優先）
- [ ] 1. 定義硬編碼起點常數 `HARDCODED_START_DISTANCE`
- [ ] 2. 創建 `_calculate_segment_acceleration_improved()` 方法
- [ ] 3. 添加 `_find_closest_distance_index()` 輔助方法
- [ ] 4. 修改 `_analyse_driver_max_speed_telemetry()` 調用邏輯

### 階段 2：測試驗證
- [ ] 5. 測試 Japan 2025 R：確保 20/20 車手都有數據
- [ ] 6. 測試 Australia 2025 R：驗證不同賽道
- [ ] 7. 測試 China 2025 R：確認邏輯穩定性

### 階段 3：優化和文檔
- [ ] 8. 添加賽道特定的硬編碼起點配置
- [ ] 9. 更新 JSON 輸出格式說明
- [ ] 10. 更新 GUI 顯示邏輯（如果需要）

---

## 💡 額外優化建議

### 賽道特定配置
```python
# 不同賽道的最佳起點配置
TRACK_SEGMENT_START_POINTS = {
    "Japan": 5000.0,      # 日本：直線段起點
    "Australia": 4500.0,  # 澳洲：不同的直線段
    "Monaco": 3000.0,     # 摩納哥：較短的直線
    # ... 其他賽道
}

def _get_hardcoded_start_distance(self, race_name: str) -> float:
    """獲取賽道特定的硬編碼起點"""
    return TRACK_SEGMENT_START_POINTS.get(race_name, 5000.0)  # 預設 5000m
```

### 智能起點檢測
```python
def _detect_straight_section_start(self, telemetry_data) -> float:
    """
    智能檢測直線段起點
    - 找到油門 > 90% 且持續超過 3 秒的位置
    - 找到速度開始快速增加的點
    """
    # 實現自動檢測邏輯
    pass
```

---

## ✅ 總結

### 核心改變
1. **起點**：從「參考範圍」改為「硬編碼固定值」
2. **終點**：從「參考範圍」改為「該車手最高速度點」
3. **結果**：從「90% NULL」改為「100% 有數據」

### 優勢
- ✅ 保證所有車手都有 Segment 數據
- ✅ 起點相同，數據具有可比性
- ✅ 終點動態，反映真實性能差異
- ✅ 符合用戶需求：「一定要生成數據」

### 保持不變
- ✅ 仍然記錄每位車手的最高速度（功能 2）
- ✅ 仍然記錄 100-300 km/h 加速數據（通用指標）
- ✅ JSON 結構保持兼容

---

**是否要我開始實現這個改進方案？** 🚀
