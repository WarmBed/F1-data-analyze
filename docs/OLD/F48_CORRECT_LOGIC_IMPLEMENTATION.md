# Function 48 - 正確邏輯實現方案

## 用戶需求確認 ✅

**正確的分析邏輯應該是：**

1. ✅ 找到最速圈（`LapTime` 最小）
2. ✅ 在最速圈中識別所有直線段
3. ✅ 找到尾速最高的直線段
4. ✅ 在該直線段內回推 100→300 km/h 的加速時間

**這樣可以確保：**
- 基於車手的最佳圈速表現
- 選擇最佳直線段（尾速最高 = 表現最好）
- 加速數據和尾速數據來自同一個直線段
- 避免跨越彎道的錯誤計算

---

## 實現方案

### 新增方法 1：`_find_fastest_lap()`
```python
def _find_fastest_lap(self, driver_laps: Any) -> Optional[Any]:
    """找到最速圈（LapTime 最小的圈）"""
    if driver_laps is None or getattr(driver_laps, "empty", False):
        return None
    
    # 轉換為 DataFrame 以便處理
    if hasattr(driver_laps, "to_pandas"):
        laps_df = driver_laps.to_pandas()
    elif isinstance(driver_laps, pd.DataFrame):
        laps_df = driver_laps
    else:
        return None
    
    # 過濾有效圈（有圈速且非 Pit Lap）
    valid_laps = laps_df[
        (laps_df["LapTime"].notna()) & 
        (~laps_df.get("IsPersonalBest", pd.Series([False]*len(laps_df))).isna())
    ].copy()
    
    if valid_laps.empty:
        # 回退：接受所有有圈速的圈
        valid_laps = laps_df[laps_df["LapTime"].notna()].copy()
    
    if valid_laps.empty:
        return None
    
    # 找到最速圈
    fastest_idx = valid_laps["LapTime"].idxmin()
    fastest_lap_num = int(valid_laps.loc[fastest_idx, "LapNumber"])
    
    # 從原始 driver_laps 中取得該圈
    for _, lap in self._iter_lap_rows(driver_laps):
        if self._extract_lap_number(lap) == fastest_lap_num:
            return lap
    
    return None
```

### 新增方法 2：`_identify_straight_line_segments()`
```python
def _identify_straight_line_segments(self, car_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """識別所有直線段（速度持續上升的區間）"""
    if car_data is None or car_data.empty or "Speed" not in car_data.columns:
        return []
    
    speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
    if speeds.empty:
        return []
    
    segments = []
    current_segment = None
    
    for i in range(len(speeds) - 1):
        idx = speeds.index[i]
        next_idx = speeds.index[i + 1]
        
        speed = speeds[idx]
        next_speed = speeds[next_idx]
        
        # 判斷是否在加速（速度上升且速度 > 80 km/h）
        if next_speed > speed and speed > 80:
            if current_segment is None:
                # 開始新的直線段
                current_segment = {
                    "start_idx": idx,
                    "end_idx": next_idx,
                    "start_speed": speed,
                    "max_speed": next_speed,
                    "max_speed_idx": next_idx
                }
            else:
                # 延續當前直線段
                current_segment["end_idx"] = next_idx
                if next_speed > current_segment["max_speed"]:
                    current_segment["max_speed"] = next_speed
                    current_segment["max_speed_idx"] = next_idx
        else:
            # 速度下降或低速，結束當前直線段
            if current_segment is not None:
                # 只保留長度足夠的直線段（速度增益 > 100 km/h）
                speed_gain = current_segment["max_speed"] - current_segment["start_speed"]
                if speed_gain > 100:
                    segments.append(current_segment)
                current_segment = None
    
    # 處理最後一個直線段
    if current_segment is not None:
        speed_gain = current_segment["max_speed"] - current_segment["start_speed"]
        if speed_gain > 100:
            segments.append(current_segment)
    
    return segments
```

### 新增方法 3：`_calculate_acceleration_in_segment()`
```python
def _calculate_acceleration_in_segment(
    self, 
    car_data: pd.DataFrame, 
    segment: Dict[str, Any]
) -> Optional[Dict[str, float]]:
    """在指定直線段內計算 100→300 km/h 加速時間"""
    try:
        # 只在該直線段的範圍內搜索
        segment_start = segment["start_idx"]
        segment_end = segment["end_idx"]
        
        # 獲取該段的速度數據
        segment_data = car_data.loc[segment_start:segment_end].copy()
        speeds = pd.to_numeric(segment_data["Speed"], errors="coerce").dropna()
        
        if speeds.empty or "Time" not in segment_data.columns:
            return None
        
        # 在該段內找到 100 km/h 和 300 km/h 的點
        speed_100_idx = None
        speed_300_idx = None
        
        for idx in speeds.index:
            speed = speeds[idx]
            if speed >= 100 and speed_100_idx is None:
                speed_100_idx = idx
            if speed >= 300 and speed_300_idx is None:
                speed_300_idx = idx
                break
        
        # 檢查是否找到兩個速度點
        if speed_100_idx is None or speed_300_idx is None:
            return None
        
        # 計算時間差
        time_100 = segment_data.loc[speed_100_idx, "Time"]
        time_300 = segment_data.loc[speed_300_idx, "Time"]
        
        if hasattr(time_100, "total_seconds"):
            time_100_sec = time_100.total_seconds()
        else:
            time_100_sec = float(time_100)
        
        if hasattr(time_300, "total_seconds"):
            time_300_sec = time_300.total_seconds()
        else:
            time_300_sec = float(time_300)
        
        time_diff = time_300_sec - time_100_sec
        
        # 驗證時間差合理性
        if time_diff <= 0 or time_diff > 15:
            return None
        
        # 計算距離差
        distance_diff = None
        if "Distance" in segment_data.columns:
            try:
                dist_100 = segment_data.loc[speed_100_idx, "Distance"]
                dist_300 = segment_data.loc[speed_300_idx, "Distance"]
                distance_diff = float(dist_300) - float(dist_100)
            except (KeyError, TypeError, ValueError):
                distance_diff = None
        
        # 計算平均加速度
        velocity_change = (300 - 100) / 3.6  # m/s
        avg_acceleration = velocity_change / time_diff
        
        return {
            "time_seconds": round(time_diff, 3),
            "distance_meters": round(distance_diff, 2) if distance_diff else None,
            "avg_acceleration_ms2": round(avg_acceleration, 2),
            "speed_100_index": int(speed_100_idx),
            "speed_300_index": int(speed_300_idx),
            "segment_start_speed": segment["start_speed"],
            "segment_max_speed": segment["max_speed"]
        }
        
    except Exception as e:
        print(f"[DEBUG] 直線段加速計算失敗: {e}")
        return None
```

### 修改核心方法：`_compute_driver_record()`
```python
def _compute_driver_record(self, driver_code: str) -> Optional[DriverSpeedRecord]:
    """計算車手的速度記錄（基於最速圈的最佳直線段）"""
    driver_laps = self._pick_driver_laps(driver_code)
    if driver_laps is None or getattr(driver_laps, "empty", False):
        return None
    
    # ✅ 步驟 1: 找到最速圈
    fastest_lap = self._find_fastest_lap(driver_laps)
    if fastest_lap is None:
        return None
    
    lap_number = self._extract_lap_number(fastest_lap)
    if lap_number is None:
        return None
    
    # ✅ 步驟 2: 獲取最速圈的遙測數據
    car_data = self._extract_car_data(fastest_lap)
    if car_data is None or "Speed" not in car_data.columns:
        return None
    
    # ✅ 步驟 3: 識別所有直線段
    straight_segments = self._identify_straight_line_segments(car_data)
    if not straight_segments:
        return None
    
    # ✅ 步驟 4: 找到尾速最高的直線段
    best_segment = max(straight_segments, key=lambda s: s["max_speed"])
    
    # ✅ 步驟 5: 在該直線段內計算加速性能
    acceleration_data = self._calculate_acceleration_in_segment(car_data, best_segment)
    
    # ✅ 步驟 6: 獲取該直線段尾速點的其他數據
    max_speed_idx = best_segment["max_speed_idx"]
    max_speed = best_segment["max_speed"]
    
    distance_m = self._safe_float(car_data, max_speed_idx, "Distance")
    throttle = self._safe_float(car_data, max_speed_idx, "Throttle")
    drs = self._safe_int(car_data, max_speed_idx, "DRS")
    session_time = self._format_time(car_data, max_speed_idx, "Time")
    
    # ✅ 創建記錄
    record = DriverSpeedRecord(
        driver=driver_code,
        driver_number=self._lookup_driver_number(driver_code),
        team=self._lookup_driver_team(driver_code),
        full_name=self._lookup_driver_name(driver_code),
        max_speed_kmh=max_speed,
        lap_number=lap_number,
        distance_m=distance_m,
        session_time=session_time,
        throttle=throttle,
        drs=drs,
        acceleration_100_300=acceleration_data,
    )
    
    return record
```

---

## 修正效果預期

### 修正前 ❌
- 遍歷所有圈，選擇最高速度的圈
- 在該圈的整個範圍內找第一個 100→300 km/h 點
- 可能跨越彎道，導致時間異常（73s, 91s 等）

### 修正後 ✅
- 只分析最速圈（最佳表現）
- 在最速圈中找到尾速最高的直線段
- 在該直線段內計算 100→300 km/h 加速時間
- 預期時間：**3-8 秒**（正常範圍）

---

## 數據一致性保證

| 數據項目 | 來源 |
|---------|------|
| **max_speed_kmh** | 尾速最高直線段的尾速 |
| **acceleration_100_300** | 同一直線段內的加速時間 |
| **lap_number** | 最速圈編號 |
| **distance_m** | 尾速點的賽道位置 |
| **throttle** | 尾速點的油門開度 |
| **drs** | 尾速點的 DRS 狀態 |

**所有數據來自：最速圈 → 尾速最高直線段 → 該段的特定點**

---

## 下一步實施

1. ✅ 添加三個新方法到 `all_drivers_straight_line_speed.py`
2. ✅ 修改 `_compute_driver_record()` 方法
3. ✅ 移除舊的 `_calculate_acceleration_100_300()` 方法
4. ✅ 測試驗證（預期加速時間 3-8 秒）

---

**方案設計時間**: 2025-10-14
**邏輯來源**: 用戶需求確認
**預期效果**: 加速時間從 73-91 秒修正為 3-8 秒
