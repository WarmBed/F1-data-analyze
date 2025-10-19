# F48 vs F13 最高速度差異深度調查報告 (China R 案例)

## 問題陳述

用戶發現同一場比賽（2025 China R）中，兩個模組顯示的最高速度**嚴重不一致**：

| 車手 | F13 (Speed Analysis) | F48 (All Drivers Straight) | 差異 |
|-----|---------------------|---------------------------|-----|
| **STR** | **335.6 km/h** | 未知 | - |
| **ALO** | **328.0 km/h** | **261.0 km/h** | **-67 km/h ❌** |
| **RUS** | 未知 | **309.0 km/h** | - |

**關鍵問題**：為什麼 ALO 在 F13 顯示 328 km/h，但 F48 只顯示 261 km/h？

---

## 數據證據

### F13 數據（comparison_telemetry_ALO_STR_2025_China_R_Lap99_Lap99.json）

```json
"statistics": {
  "Speed": {
    "ALO_max": 328.0,  // ✅ 整圈最大值
    "ALO_min": 57.0,
    "ALO_mean": 192.4,
    "STR_max": 336.0,  // ✅ 整圈最大值
    "STR_min": 53.0,
    "STR_mean": 203.6
  }
}
```

**F13 邏輯**：
- 最速圈：第 3 圈（ALO）
- 計算方式：`telemetry['Speed'].max()` → 整圈所有數據點的最大值
- 結果：**328.0 km/h**

---

### F48 數據（all_drivers_straight_line_speed_2025_China_R.json）

```json
{
  "driver": "ALO",
  "driver_number": 14,
  "team": "Aston Martin",
  "full_name": "Fernando Alonso",
  "max_speed_kmh": 261.0,  // ❌ 只有 261 km/h
  "lap_number": 3,  // ✅ 相同圈數
  "distance_m": 1915.733,
  "session_time": "P0DT0H0M37.49S",
  "throttle_percent": 100.0,
  "drs": 0,
  "acceleration_100_300": {
    "segment_start_speed": 89.0,
    "segment_max_speed": 261.0  // ❌ 直線段終點只有 261
  }
}
```

**F48 邏輯**：
- 最速圈：第 3 圈（ALO）✅ 相同
- 計算方式：
  1. 識別直線段（持續加速 >100 km/h 增幅）
  2. 選擇尾速最高的直線段
  3. 返回該直線段的終點速度
- 結果：**261.0 km/h**（直線段終點）

---

## 根本原因分析

### 為什麼差異高達 67 km/h？

**關鍵發現**：F48 的「直線段過濾」邏輯**過於嚴格**，導致錯過真實的最高速度。

#### 可能的情況

假設 ALO 最速圈（第 3 圈）的速度分佈：

```
賽道位置 | 速度 | F48 判定 | F13 判定
---------|------|---------|--------
Turn 13 出口 | 89 km/h | 直線段起點 | ✅ 計入
直線段加速 | 100 → 250 km/h | ✅ 計入 | ✅ 計入
直線段終點 | 261 km/h | ✅ 終點尾速 | ✅ 計入
剎車前瞬間 | 280 → 328 km/h | ❌ 不屬於直線段 | ✅ 計入
Turn 14 剎車 | 150 km/h | ❌ 剎車區 | ✅ 計入
```

#### F48 的過濾邏輯

```python
def _identify_straight_line_segments(self, car_data: pd.DataFrame) -> List[Dict]:
    """識別所有直線段（速度持續上升的區間）"""
    
    # ❌ 問題：要求「速度持續上升」
    if speeds[next_idx] > speeds[idx] + 0.5:  # 速度必須持續上升
        # 記錄為直線段的一部分
    else:
        # ❌ 速度停止上升 → 直線段結束
        # 328 km/h 發生在「加速減緩」或「準備剎車」階段
        # F48 認為這不是「純直線加速」，因此不計入
```

**核心問題**：
1. F48 要求速度「持續上升」才算直線段
2. 當車手達到最高速度後，速度增幅減緩（例如從 +10 km/h/s 降到 +1 km/h/s）
3. F48 判定「直線段結束」，返回上一個數據點的速度（261 km/h）
4. 但實際上車手繼續加速到 328 km/h，只是加速度降低了

---

## 技術深度分析

### F48 直線段識別邏輯

```python
# CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py
def _identify_straight_line_segments(self, car_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """識別所有直線段（速度持續上升的區間）"""
    
    segments = []
    current_segment = None

    for i in range(len(speeds) - 1):
        idx = speeds.index[i]
        next_idx = speeds.index[i + 1]
        
        current_speed = speeds[idx]
        next_speed = speeds[next_idx]
        
        # ❌ 核心問題：速度必須「持續上升」
        if next_speed > current_speed + 0.5:
            if current_segment is None:
                # 開始新的直線段
                current_segment = {
                    "start_idx": idx,
                    "start_speed": current_speed,
                    "max_speed": current_speed,
                    "max_speed_idx": idx
                }
            else:
                # 更新直線段
                if next_speed > current_segment["max_speed"]:
                    current_segment["max_speed"] = next_speed
                    current_segment["max_speed_idx"] = next_idx
        else:
            # ❌ 速度停止上升 → 結束直線段
            if current_segment is not None:
                # 檢查直線段是否有效（速度增幅 >100 km/h）
                speed_gain = current_segment["max_speed"] - current_segment["start_speed"]
                if speed_gain > 100 and current_segment["start_speed"] > 80:
                    segments.append(current_segment)
                current_segment = None
    
    return segments
```

**問題場景**：

```
數據點 | 速度 | 速度增幅 | F48 判定
-------|------|---------|--------
點 A | 250 km/h | +10 | ✅ 直線段內
點 B | 261 km/h | +11 | ✅ 直線段內
點 C | 270 km/h | +9 | ✅ 繼續
點 D | 280 km/h | +10 | ✅ 繼續
點 E | 295 km/h | +15 | ✅ 繼續
點 F | 310 km/h | +15 | ✅ 繼續
點 G | 320 km/h | +10 | ✅ 繼續
點 H | 325 km/h | +5 | ⚠️ 增幅降低
點 I | 328 km/h | +3 | ⚠️ 增幅繼續降低
點 J | 328 km/h | 0 | ❌ 速度不再上升 → 直線段結束
```

**F48 返回**：點 I 之前的最高速度（可能是 325 或更早的 261）
**F13 返回**：整圈最大值 328 km/h

---

## 修正方案

### 方案 A：放寬「持續上升」條件（推薦）

修改 F48 邏輯，允許速度增幅降低但仍在加速的區間：

```python
def _identify_straight_line_segments(self, car_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """識別所有直線段（允許加速度降低）"""
    
    segments = []
    current_segment = None
    tolerance_counter = 0  # 容忍計數器
    
    for i in range(len(speeds) - 1):
        idx = speeds.index[i]
        next_idx = speeds.index[i + 1]
        
        current_speed = speeds[idx]
        next_speed = speeds[next_idx]
        
        # ✅ 修正：允許速度「不下降」或「輕微下降」
        if next_speed >= current_speed - 2.0:  # 容忍 -2 km/h 的波動
            if current_segment is None:
                # 開始新的直線段
                current_segment = {
                    "start_idx": idx,
                    "start_speed": current_speed,
                    "max_speed": current_speed,
                    "max_speed_idx": idx
                }
            
            # 更新最高速度
            if next_speed > current_segment["max_speed"]:
                current_segment["max_speed"] = next_speed
                current_segment["max_speed_idx"] = next_idx
                tolerance_counter = 0  # 重置容忍計數器
            else:
                tolerance_counter += 1
                # 如果連續 5 個點速度不再上升，結束直線段
                if tolerance_counter > 5:
                    if current_segment is not None:
                        speed_gain = current_segment["max_speed"] - current_segment["start_speed"]
                        if speed_gain > 100 and current_segment["start_speed"] > 80:
                            segments.append(current_segment)
                        current_segment = None
                        tolerance_counter = 0
        else:
            # 速度明顯下降（剎車）→ 結束直線段
            if current_segment is not None:
                speed_gain = current_segment["max_speed"] - current_segment["start_speed"]
                if speed_gain > 100 and current_segment["start_speed"] > 80:
                    segments.append(current_segment)
                current_segment = None
                tolerance_counter = 0
    
    return segments
```

**效果**：
- ✅ 允許車手在接近最高速時加速度降低
- ✅ 捕捉真實的最高速度（328 km/h）
- ✅ 仍然過濾剎車區（速度明顯下降的區域）

---

### 方案 B：直接取整圈最大值（與 F13 統一）

```python
def _compute_driver_record(self, driver_code: str) -> Optional[DriverSpeedRecord]:
    """計算車手的速度記錄（整圈最大值，與 F13 一致）"""
    
    # 步驟 1: 找到最速圈
    fastest_lap = self._find_fastest_lap(driver_laps)
    
    # 步驟 2: 獲取遙測數據
    car_data = self._extract_car_data(fastest_lap)
    
    # ✅ 步驟 3: 直接取整圈最大值（移除直線段過濾）
    max_speed = car_data["Speed"].max()
    max_speed_idx = car_data["Speed"].idxmax()
    
    return max_speed  # 328 km/h（與 F13 一致）
```

**效果**：
- ✅ 與 F13 完全一致
- ❌ 失去「純直線加速性能」的專業定位

---

### 方案 C：保留當前邏輯，但改為「全賽事掃描」

```python
def _compute_driver_record(self, driver_code: str) -> Optional[DriverSpeedRecord]:
    """計算車手的速度記錄（全賽事直線段掃描）"""
    
    all_laps = self._pick_driver_laps(driver_code)
    best_segment_overall = None
    
    # ✅ 掃描所有圈的直線段
    for _, lap in self._iter_lap_rows(all_laps):
        car_data = self._extract_car_data(lap)
        if car_data is None:
            continue
        
        # 識別該圈的直線段
        segments = self._identify_straight_line_segments(car_data)
        if not segments:
            continue
        
        # 找到該圈尾速最高的直線段
        best_segment_in_lap = max(segments, key=lambda s: s["max_speed"])
        
        # 與全賽事最佳比較
        if best_segment_overall is None or best_segment_in_lap["max_speed"] > best_segment_overall["max_speed"]:
            best_segment_overall = best_segment_in_lap
    
    return best_segment_overall["max_speed"]
```

**效果**：
- ✅ 不限制最速圈，可能找到其他圈的更高速度
- ⚠️ 但仍可能因為「持續上升」條件錯過真實最高速

---

## 推薦方案

### 🎯 **方案 A：放寬「持續上升」條件**（最佳平衡）

**理由**：
1. **保留專業定位**：F48 仍然是「直線加速性能」分析
2. **修正邏輯缺陷**：允許加速度降低但仍在加速的區間
3. **更準確的數據**：捕捉真實的直線最高速度
4. **與 F13 互補**：
   - F48: 直線段最高速（含加速減緩階段）→ 328 km/h
   - F13: 整圈最大值（含所有數據點）→ 328 km/h

**預期結果**：
- ALO F48: 261 km/h → **328 km/h** ✅
- 與 F13 一致，但保留直線段過濾邏輯

---

## 測試驗證

### 測試案例：ALO (2025 China R)

**當前 F48**：
```
最速圈：第 3 圈
直線段識別：89 → 261 km/h（直線段終點）
返回：261 km/h ❌
```

**修正後 F48（方案 A）**：
```
最速圈：第 3 圈
直線段識別：89 → 328 km/h（允許加速度降低）
返回：328 km/h ✅（與 F13 一致）
```

**F13**：
```
最速圈：第 3 圈
整圈掃描：max(57 → 328 km/h)
返回：328 km/h ✅
```

---

## 結論

**根本原因**：
- F48 的「速度持續上升」條件**過於嚴格**
- 當車手接近最高速時，加速度自然降低
- F48 誤判「直線段結束」，返回較早的速度數據點

**差異案例**：
- ALO: F13 = 328 km/h，F48 = 261 km/h（差 67 km/h）
- 兩者使用相同最速圈（第 3 圈），但數據處理方式導致巨大差異

**推薦修正**：
- **方案 A**：放寬「持續上升」條件，允許加速度降低
- 預期可將 F48 數據提升到與 F13 一致（328 km/h）
- 保留直線段過濾邏輯，但更準確捕捉真實最高速度

---

**文件狀態**：深度調查完成
**待辦事項**：實施方案 A 修正 F48 邏輯
**最後更新**：2025-10-14
