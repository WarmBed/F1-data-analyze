# 🔍 Distance Diff 跨賽事比較問題診斷報告

**診斷時間**：2025-11-14 16:00  
**問題現象**：Distance Diff 呼叫 API 成功，但圖表沒有更新

---

## ✅ 診斷結果

### 問題根源：API 缺少 Distancediff 計算邏輯

**API 測試結果**：
```
telemetry_comparison keys: ['Speed', 'RPM', 'Brake', 'nGear', 'Throttle', 'Acceleration', 'Speeddiff']
```

**關鍵發現**：
- ✅ API 有計算 `Speeddiff`（速度差）
- ❌ API **沒有** `Distancediff`（距離差）
- ❌ Distance Diff GUI 期望 `Distancediff` 參數，但 API 沒有提供

---

## 📋 Distance Diff GUI 的期望數據格式

根據 `distancediff_analysis_mdi.py` Line 1661-1669：

```python
# Distance Diff 優先檢查 "Distancediff"，其次 "Distance"
distancediff_key = None
if "Distancediff" in telemetry_comp:
    distancediff_key = "Distancediff"
    print(f"[DISTDIFF-CROSS-EVENT] ✅ 使用 Distancediff 參數（跨賽事計算的距離差）")
elif "Distance" in telemetry_comp:
    distancediff_key = "Distance"
    print(f"[DISTDIFF-CROSS-EVENT] ⚠️ 使用 Distance 參數（原始距離，非距離差）")
```

**期望的數據結構**：
```json
{
  "telemetry_comparison": {
    "Distancediff": {
      "name": "Distance Difference",
      "distance": [0.09, 10.57, ...],  // X軸：賽道距離
      "distance_difference": [-5.2, -4.8, ...],  // Y軸：距離差（driver1 - driver2）
      "driver1_time_seconds": [0.0, 0.5, ...],
      "driver2_time_seconds": [0.0, 0.5, ...],
      "time_reference": "seconds_from_lap_start"
    }
  }
}
```

---

## 🔧 API 當前實現（只有 Speeddiff）

**檔案**：`api/routers/analysis.py` Line 124-193

**Speed Difference 計算邏輯**：
```python
# 提取速度數據
driver1_speed = np.array(telemetry_comp1["Speed"].get("driver1_data", []))
driver2_speed = np.array(telemetry_comp2["Speed"].get("driver1_data", []))
distance1 = np.array(telemetry_comp1["Speed"].get("distance", []))
distance2 = np.array(telemetry_comp2["Speed"].get("distance", []))

# 找出共同的距離範圍
common_min = max(distance1.min(), distance2.min())
common_max = min(distance1.max(), distance2.max())

# 創建共同的距離數組（500個採樣點）
common_distance = np.linspace(common_min, common_max, 500)

# 插值速度數據到共同距離
speed1_interp = np.interp(common_distance, distance1, driver1_speed)
speed2_interp = np.interp(common_distance, distance2, driver2_speed)

# 計算速度差（driver1 - driver2）
speed_diff = speed1_interp - speed2_interp

# 構建 Speeddiff 遙測參數
merged_telemetry["Speeddiff"] = {
    "name": "Speed Difference",
    "distance": common_distance.tolist(),
    "speed_difference": speed_diff.tolist(),
    "driver1_time_seconds": time1_interp.tolist(),
    "driver2_time_seconds": time2_interp.tolist(),
    "time_reference": "seconds_from_lap_start"
}
```

---

## 💡 解決方案選項

### 選項 1：API 端添加 Distancediff 計算（建議）✅

**優點**：
- 與 Speeddiff 一致的架構
- 所有 GUI 模組都能使用
- 遵循「API-ONLY」模式

**實現步驟**：
1. 在 `_merge_cross_event_telemetry()` 中添加距離差計算邏輯
2. 參考 CLI Function 13 的 `_calculate_distance_difference()` 方法
3. 構建 `Distancediff` 遙測參數

**簡化版實現**（不需要 X/Y 坐標）：
```python
# ========== 計算 Distance Difference ==========
print(f"[MERGE] 🔄 開始計算跨賽事距離差異...")
merged_distance_difference = {}

if "Distance" in telemetry_comp1 and "Distance" in telemetry_comp2:
    try:
        # 提取距離數據（實際上是賽道累積距離）
        driver1_distance = np.array(telemetry_comp1["Distance"].get("driver1_data", []))
        driver2_distance = np.array(telemetry_comp2["Distance"].get("driver1_data", []))
        reference_distance1 = np.array(telemetry_comp1["Distance"].get("distance", []))
        reference_distance2 = np.array(telemetry_comp2["Distance"].get("distance", []))
        
        # 找出共同的距離範圍
        common_min = max(reference_distance1.min(), reference_distance2.min())
        common_max = min(reference_distance1.max(), reference_distance2.max())
        
        if common_min < common_max:
            # 創建共同的距離數組（500個採樣點）
            common_distance = np.linspace(common_min, common_max, 500)
            
            # 插值距離數據到共同距離
            distance1_interp = np.interp(common_distance, reference_distance1, driver1_distance)
            distance2_interp = np.interp(common_distance, reference_distance2, driver2_distance)
            
            # 計算距離差（driver1 - driver2）
            distance_diff = distance1_interp - distance2_interp
            
            merged_distance_difference = {
                'distance': common_distance.tolist(),
                'distance_difference': distance_diff.tolist(),
                'max_diff': float(np.max(distance_diff)),
                'min_diff': float(np.min(distance_diff)),
                'mean_diff': float(np.mean(distance_diff)),
                'reference': f"{driver1} - {driver2}"
            }
            
            # 構建 Distancediff 遙測參數
            merged_telemetry["Distancediff"] = {
                "name": "Distance Difference",
                "distance": common_distance.tolist(),
                "distance_difference": distance_diff.tolist(),
                "driver1_time_seconds": merged_distance_difference.get("driver1_time_seconds", []),
                "driver2_time_seconds": merged_distance_difference.get("driver2_time_seconds", []),
                "time_reference": "seconds_from_lap_start"
            }
            print(f"[MERGE] ✅ Distancediff 遙測參數已添加")
```

### 選項 2：GUI 端回退到 Distance 參數（臨時方案）❌

**缺點**：
- 不符合跨賽事比較的設計
- 會顯示兩條原始距離曲線，而不是距離差異
- 用戶體驗不佳

---

## 🎯 建議執行步驟

1. **立即修復 API**：在 `api/routers/analysis.py` 的 `_merge_cross_event_telemetry()` 中添加 `Distancediff` 計算
2. **重啟 API 服務器**：讓修改生效
3. **測試 Distance Diff GUI**：確認圖表正確顯示
4. **驗證數據格式**：確認 API 返回的 `Distancediff` 符合 GUI 期望

---

## 📝 待確認問題

1. **Distance 參數的含義**：
   - 是否就是賽道累積距離？
   - `driver1_data` 和 `driver2_data` 的單位是什麼？

2. **是否需要 X/Y 坐標**：
   - CLI Function 13 使用 `_interpolate_position_to_common_distance()` 需要 X/Y
   - API 的簡化版本是否可以直接計算距離差？

---

**建議**：請確認是否需要我立即實現 API 端的 `Distancediff` 計算邏輯？
