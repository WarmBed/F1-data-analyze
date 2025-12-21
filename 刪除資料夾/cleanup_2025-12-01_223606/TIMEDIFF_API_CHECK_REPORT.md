# 🔍 Time Diff API 功能檢查報告

**檢查時間**：2025-11-14 16:20  
**目標**：確認 API 是否實現 Time Diff 跨賽事比較功能

---

## ✅ 檢查結果總結

### 1. CLI 實現：✅ 完整

**檔案**：`CLI_modules/cli/analyzer/two_driver_telemetry_comparison_fixed.py`  
**方法**：`_calculate_time_difference()` (Line 641-721)

**功能**：
- ✅ 計算兩位車手在相同時間點的距離差
- ✅ 根據距離差和速度估算時間差
- ✅ 支援時間數據插值
- ✅ 包含完整統計資訊

**輸出格式**：
```python
{
    'reference_time': common_time.tolist(),  # 共同時間數組（500點）
    'distance_gap': distance_gap.tolist(),  # 距離差（m）
    'cumulative_time_difference': cumulative_time_diff.tolist(),  # 時間差（秒）
    'driver1_distance_at_time': distance1_interp.tolist(),  # 車手1的距離
    'driver2_distance_at_time': distance2_interp.tolist(),  # 車手2的距離
    'distance_gap_stats': {...},
    'time_diff_stats': {...}
}
```

---

### 2. GUI 實現：✅ 存在

**檔案**：`modules/gui/lap_analysis/timediff_analysis/timediff_analysis_mdi.py`

**模組名稱**：`timediffAnalysisModule`

**現有功能**：
- ✅ 標準圈速時間差分析
- ✅ 數據載入器（`timediffAnalysisDataLoader`）
- ✅ 圖表組件（`timediffAnalysisChartWidget`）
- ✅ 數據管理器（`timediffDataManager`）

**檢查結果**：
- ❌ **沒有** `_on_cross_event_data_loaded()` 方法
- ❌ **沒有** `update_cross_event_comparison()` 方法
- ❌ **不支援跨賽事比較**

---

### 3. API 實現：❌ 不存在

**檔案**：`api/routers/analysis.py`

**檢查結果**：
- ❌ **沒有** `Timediff` 參數計算
- ❌ **沒有** `time_difference` 合併邏輯
- ✅ 有 `Speeddiff` 計算（已實現）
- ✅ 有 `Distancediff` 計算（剛修復）

**目前 API 輸出**：
```json
{
  "telemetry_comparison": {
    "Speed": {...},
    "RPM": {...},
    "Brake": {...},
    "nGear": {...},
    "Throttle": {...},
    "Acceleration": {...},
    "Speeddiff": {...},       // ✅ 已有
    "Distancediff": {...}     // ✅ 剛加
    // ❌ 缺少 Timediff
  }
}
```

---

## 🎯 需要實現的功能

### 階段 1：API 端添加 Timediff 計算 ⚠️

**位置**：`api/routers/analysis.py` 的 `_merge_cross_event_telemetry()` 函數

**需要添加**：

#### 1. Time Difference 計算邏輯
```python
# ========== ✅ 計算 Time Difference（參考 CLI Function 13）==========
print(f"[MERGE] 🔄 開始計算跨賽事時間差異...")
merged_time_difference = {}

if "Speed" in telemetry_comp1 and "Speed" in telemetry_comp2:
    try:
        # 提取距離和時間數據
        distance1 = np.array(telemetry_comp1["Speed"].get("distance", []))
        distance2 = np.array(telemetry_comp2["Speed"].get("distance", []))
        time1 = telemetry_comp1["Speed"].get("driver1_time_seconds", None)
        time2 = telemetry_comp2["Speed"].get("driver1_time_seconds", None)
        
        if time1 and time2:
            time1_array = np.array(time1)
            time2_array = np.array(time2)
            
            # 找出共同的時間範圍
            common_time_min = max(time1_array.min(), time2_array.min())
            common_time_max = min(time1_array.max(), time2_array.max())
            
            if common_time_min < common_time_max:
                # 創建共同的時間數組（500個採樣點）
                common_time = np.linspace(common_time_min, common_time_max, 500)
                
                # 插值距離到共同時間
                distance1_interp = np.interp(common_time, time1_array, distance1)
                distance2_interp = np.interp(common_time, time2_array, distance2)
                
                # 計算距離差（driver1 - driver2）
                distance_gap = distance1_interp - distance2_interp
                
                # 計算時間差（使用速度估算）
                driver1_speed = np.array(telemetry_comp1["Speed"].get("driver1_data", []))
                driver2_speed = np.array(telemetry_comp2["Speed"].get("driver1_data", []))
                
                # 插值速度到共同時間
                speed1_interp = np.interp(common_time, time1_array, driver1_speed)
                speed2_interp = np.interp(common_time, time2_array, driver2_speed)
                
                # 轉換速度 km/h → m/s
                speed1_ms = speed1_interp / 3.6
                speed2_ms = speed2_interp / 3.6
                
                # 計算時間差：距離差 / 平均速度
                avg_speed_ms = (speed1_ms + speed2_ms) / 2
                avg_speed_ms = np.where(avg_speed_ms > 0.1, avg_speed_ms, 0.1)  # 避免除以零
                cumulative_time_diff = distance_gap / avg_speed_ms
                
                merged_time_difference = {
                    'time': common_time.tolist(),  # 時間軸（秒）
                    'distance_gap': distance_gap.tolist(),  # 距離差（米）
                    'time_difference': cumulative_time_diff.tolist(),  # 時間差（秒）
                    'driver1_distance': distance1_interp.tolist(),
                    'driver2_distance': distance2_interp.tolist(),
                    'max_time_diff': float(np.max(cumulative_time_diff)),
                    'min_time_diff': float(np.min(cumulative_time_diff)),
                    'mean_time_diff': float(np.mean(cumulative_time_diff)),
                    'reference': f"{driver1} - {driver2}"
                }
                
                print(f"[MERGE] ✅ 時間差計算完成：{len(cumulative_time_diff)} 點，範圍 {merged_time_difference['min_time_diff']:.2f} ~ {merged_time_difference['max_time_diff']:.2f} s")
```

#### 2. 構建 Timediff 遙測參數
```python
# ========== 構建 Timediff 遙測參數（用於 Time Diff Analysis）==========
if merged_time_difference:
    merged_telemetry["Timediff"] = {
        "name": "Time Difference",
        "time": merged_time_difference["time"],  # X軸：時間（秒）
        "time_difference": merged_time_difference["time_difference"],  # Y軸：時間差（秒）
        "distance_gap": merged_time_difference.get("distance_gap", []),  # 額外資訊
        "driver1_distance": merged_time_difference.get("driver1_distance", []),
        "driver2_distance": merged_time_difference.get("driver2_distance", [])
    }
    print(f"[MERGE] ✅ Timediff 遙測參數已添加")
```

---

### 階段 2：GUI 端添加跨賽事支援 ⚠️

**檔案**：`modules/gui/lap_analysis/timediff_analysis/timediff_analysis_mdi.py`

**需要添加的方法**：

#### 1. `update_cross_event_comparison()`
參考 `speeddiff_analysis_mdi.py` Line 1554-1614

#### 2. `_on_cross_event_data_loaded()`
參考 `speeddiff_analysis_mdi.py` Line 1615-1708

#### 3. `_on_cross_event_load_error()`
參考 `speeddiff_analysis_mdi.py` Line 1708-1710

#### 4. `get_module_type()`
```python
def get_module_type(self) -> str:
    """返回模組類型"""
    return "telemetry_timediff"
```

---

## 📊 Time Diff 數據格式

### GUI 期望的數據結構
```python
{
    "timediff_data": {
        "time": [0.0, 0.5, 1.0, ...],  # X軸：時間（秒）
        "time_difference": [0.0, -0.1, -0.2, ...],  # Y軸：時間差（秒）
        "distance_gap": [0.0, -2.5, -5.0, ...],  # 距離差（米）
        "driver1_distance": [0.0, 50.0, 100.0, ...],  # 車手1距離
        "driver2_distance": [0.0, 52.5, 105.0, ...]   # 車手2距離
    },
    "comparison_info": {...},
    "use_time_axis": False  # Time Diff 固定使用時間軸
}
```

### 物理意義
- **time**：從圈開始的時間（秒）
- **time_difference**：在相同時間點，車手1領先/落後車手2的時間（秒）
  - 正值：車手1領先
  - 負值：車手1落後
- **distance_gap**：在相同時間點的距離差（米）

---

## ✅ 實現優先級

### 高優先級（建議立即實現）
1. ✅ Distancediff API 計算（已完成）
2. ⏳ Timediff API 計算（待實現）
3. ⏳ Time Diff GUI 跨賽事支援（待實現）

### 中優先級（可稍後實現）
4. 其他遙測參數的 Diff 計算（Brake Diff, Throttle Diff 等）

---

## 🎯 下一步建議

### 選項 1：立即實現 Timediff API ✅ 推薦
**工作量**：約 30 分鐘
**好處**：
- 與 Speeddiff/Distancediff 架構一致
- Time Diff GUI 也能支援跨賽事比較
- 完整的三 Diff 功能（Speed/Distance/Time）

### 選項 2：稍後實現 ⏳
**理由**：
- Time Diff 使用頻率可能較低
- 可以先測試 Distance Diff 是否穩定

---

## 📝 技術細節

### Time Diff vs Speed/Distance Diff 的差異

| 特性 | Speed Diff | Distance Diff | Time Diff |
|------|-----------|--------------|-----------|
| X軸 | 距離 (m) | 距離 (m) | **時間 (s)** |
| Y軸 | 速度差 (km/h) | 距離差 (m) | **時間差 (s)** |
| 插值基準 | 距離 | 距離 | **時間** |
| 計算複雜度 | 低 | 中 | 中 |
| 應用場景 | 速度優勢分析 | 位置差異 | 圈速時間分析 |

### CLI 實現參考
- 檔案：`two_driver_telemetry_comparison_fixed.py`
- 方法：`_calculate_time_difference()` (Line 641-721)
- 關鍵邏輯：
  1. 創建共同時間範圍
  2. 插值距離到時間
  3. 計算距離差
  4. 使用速度估算時間差

---

**結論**：Time Diff API 功能**尚未實現**，但有完整的 CLI 參考可以快速移植。建議按照 Distancediff 的模式添加 Timediff 計算。

**待確認**：是否需要立即實現 Time Diff API 功能？
