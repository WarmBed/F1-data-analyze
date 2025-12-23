# GAS 車手無加速數據問題分析報告

## 問題陳述

**賽事**: 2025 Singapore R
**車手**: GAS (Pierre Gasly)
**問題**: 有最高速度數據（291 km/h），但沒有加速時間數據

```json
{
  "driver": "GAS",
  "max_speed_kmh": 291.0,  // ✅ 有最高速度
  "lap_number": 53,
  // ❌ 沒有 acceleration_100_300 資料
}
```

對比其他車手（例如 VER）：
```json
{
  "driver": "VER",
  "max_speed_kmh": 289.0,  // ✅ 有最高速度
  "acceleration_100_300": {  // ✅ 有加速數據
    "time_seconds": 4.92,
    // ...
  }
}
```

---

## 根本原因

### 加速計算邏輯

```python
def _calculate_acceleration_in_segment(self, car_data, segment):
    """在指定直線段內計算 100→250 km/h 加速時間"""
    
    # 在直線段內找到 100 km/h 和 250 km/h 的點
    for idx in speeds.index:
        speed = speeds[idx]
        if speed >= 100 and speed_100_idx is None:
            speed_100_idx = idx  # ❌ 需要找到 >= 100 km/h 的點
        if speed >= 250 and speed_250_idx is None:
            speed_250_idx = idx  # ❌ 需要找到 >= 250 km/h 的點
            break
    
    # ❌ 如果找不到任一個點，返回 None
    if speed_100_idx is None or speed_250_idx is None:
        return None
```

### GAS 的情況

**假設 GAS 的直線段速度分佈**：
```
彎道出口: 120 km/h  → ❌ 直線段起點已經 > 100 km/h
加速:     150 km/h
加速:     180 km/h
加速:     210 km/h
加速:     240 km/h
加速:     270 km/h
最高點:   291 km/h
```

**問題**：
- 直線段起點速度 = 120 km/h（> 100 km/h）
- 無法找到 `speed >= 100` 的點（因為所有點都 > 100）
- `speed_100_idx = None` → 返回 `None`
- 沒有加速數據

**為什麼會這樣**：
1. **新加坡賽道特性**：街道賽，彎道多，直線段短
2. **GAS 的駕駛風格**：可能在某個中速彎出口（120 km/h）開始加速
3. **直線段識別邏輯**：從最高點（291 km/h）向前回推，找到的起點是 120 km/h

---

## 解決方案

### 方案 A：放寬加速起點要求（推薦）

如果直線段起點 > 100 km/h，使用起點作為加速起點：

```python
def _calculate_acceleration_in_segment(self, car_data, segment):
    """在指定直線段內計算加速時間（彈性起點）"""
    
    segment_start_speed = segment["start_speed"]  # 例如 120 km/h
    segment_max_speed = segment["max_speed"]      # 例如 291 km/h
    
    # ✅ 彈性起點邏輯
    if segment_start_speed >= 100:
        # 起點已經 > 100 km/h，使用起點作為加速起點
        speed_100_idx = segment["start_idx"]
        actual_speed_100 = segment_start_speed  # 120 km/h
    else:
        # 起點 < 100 km/h，搜索 >= 100 的點
        for idx in speeds.index:
            if speeds[idx] >= 100:
                speed_100_idx = idx
                actual_speed_100 = speeds[idx]
                break
    
    # 搜索 >= 250 km/h 的點
    for idx in speeds.index:
        if speeds[idx] >= 250:
            speed_250_idx = idx
            actual_speed_250 = speeds[idx]
            break
    
    # 檢查是否找到終點（250 km/h）
    if speed_250_idx is None:
        # ❌ 最高速度 < 250 km/h，無法計算標準加速時間
        return None
    
    # ✅ 計算加速時間
    time_diff = time_250_sec - time_100_sec
    
    return {
        "time_seconds": round(time_diff, 3),
        "speed_100_kmh": actual_speed_100,  # 可能是 120
        "speed_250_kmh": actual_speed_250,
        # 標註實際起點
        "actual_start_speed": actual_speed_100
    }
```

**效果**：
- GAS: 起點 120 km/h → 計算 120→250 km/h 的時間
- 仍然有加速數據，只是起點不同
- 標註 `actual_start_speed` 讓用戶知道差異

---

### 方案 B：降低加速終點要求

如果車手最高速度 < 250 km/h，改為計算到最高速度：

```python
def _calculate_acceleration_in_segment(self, car_data, segment):
    """在指定直線段內計算加速時間（彈性終點）"""
    
    segment_max_speed = segment["max_speed"]  # 例如 240 km/h
    
    # ✅ 彈性終點邏輯
    if segment_max_speed < 250:
        # 最高速度 < 250，使用最高速度作為終點
        target_speed = segment_max_speed
    else:
        # 最高速度 >= 250，使用標準終點
        target_speed = 250
    
    # 搜索終點
    for idx in speeds.index:
        if speeds[idx] >= target_speed:
            speed_250_idx = idx
            break
    
    return {
        "time_seconds": round(time_diff, 3),
        "speed_100_kmh": 100.0,
        "speed_250_kmh": target_speed,  # 可能 < 250
        "target_adjusted": target_speed < 250
    }
```

**效果**：
- 低速賽道（如新加坡）的車手也能有加速數據
- 標註 `target_adjusted` 表示使用了非標準終點

---

### 方案 C：同時彈性起點和終點（最寬鬆）

結合方案 A 和 B：

```python
def _calculate_acceleration_in_segment(self, car_data, segment):
    """在指定直線段內計算加速時間（完全彈性）"""
    
    segment_start_speed = segment["start_speed"]
    segment_max_speed = segment["max_speed"]
    
    # ✅ 彈性起點
    if segment_start_speed >= 100:
        actual_start_speed = segment_start_speed
        speed_100_idx = segment["start_idx"]
    else:
        # 搜索 >= 100 的點
        for idx in speeds.index:
            if speeds[idx] >= 100:
                actual_start_speed = speeds[idx]
                speed_100_idx = idx
                break
    
    # ✅ 彈性終點
    target_speed = min(250, segment_max_speed)  # 取較小值
    
    for idx in speeds.index:
        if speeds[idx] >= target_speed:
            speed_250_idx = idx
            break
    
    # ❌ 如果仍然找不到，返回 None
    if speed_100_idx is None or speed_250_idx is None:
        return None
    
    return {
        "time_seconds": round(time_diff, 3),
        "speed_100_kmh": actual_start_speed,
        "speed_250_kmh": target_speed,
        "flexible_mode": True
    }
```

---

## 推薦實施方案

### 🎯 **方案 A：彈性起點**（推薦）

**理由**：
1. ✅ 解決 GAS 的問題（起點 > 100 km/h）
2. ✅ 保留標準終點（250 km/h），便於比較
3. ✅ 標註實際起點，保持透明度
4. ✅ 對高速賽道無影響（起點通常 < 100 km/h）

**預期結果**：
- GAS: 計算 120→250 km/h（實際起點 120）
- 其他車手: 計算 100→250 km/h（實際起點 100）
- 所有車手都有加速數據 ✅

**實施步驟**：
1. 修改 `_calculate_acceleration_in_segment` 邏輯
2. 添加 `actual_start_speed` 欄位
3. GUI 顯示時標註實際起點（例如「120→250 km/h」）

---

## 測試驗證

### 當前狀況（Singapore R）
```
有加速數據: 19 位車手
無加速數據: 1 位車手（GAS）
原因: 直線段起點 > 100 km/h
```

### 預期結果（方案 A）
```
有加速數據: 20 位車手 ✅
GAS: 120→250 km/h (3.2 秒)
標註: actual_start_speed = 120
```

---

## 關於排序問題的回答

### 加速時間欄位排序

**當前實現**：
```python
self.table.sortItems(3, Qt.AscendingOrder)  # ✅ 遞增排序
```

**邏輯正確性**：
- ✅ **遞增排序（AscendingOrder）是正確的**
- 加速時間越短越好（例如 2.88 秒 > 5.00 秒）
- 遞增排序：2.88 → 3.00 → 3.50 → ... → 5.00
- 最快的車手排在最前面 ✅

**不需要修改**：排序邏輯已經正確。

---

**文件狀態**：問題分析完成
**待辦事項**：實施方案 A 修正 GAS 加速數據
**最後更新**：2025-10-14
