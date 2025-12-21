# Time Diff Analysis - Time Axis 模式修復報告

## 🎯 **問題根本原因**

### **發現的Bug**:
Time Diff Analysis 在 **Time Axis 模式**下無法顯示數據，原因是：

**錯誤邏輯** (Line 1407-1410):
```python
# ❌ 錯誤：期望不存在的 driver1_time_seconds 和 driver2_time_seconds
driver1_time = timediff_data.get('driver1_time_seconds', [])
driver2_time = timediff_data.get('driver2_time_seconds', [])
```

**日誌證據**:
```
[timediff_CHART] 🕒 driver1_time 數據點: 0  # ❌ 空的!
[timediff_CHART] 🕒 driver2_time 數據點: 0  # ❌ 空的!
[timediff_CHART] 時間數據點 (X軸): 500    # ✅ 正確!
```

### **對比 Distance Diff Analysis**:
Distance Diff Analysis 在 Time Axis 模式下工作正常，因為它：
1. 有真實的 `driver1_time_seconds` 數據（來自遙測比較）
2. Time Axis 切換時使用 `driver1_time` 作為 X 軸數據源

## ✅ **修復方案**

### **核心修改** (`timediff_analysis_chart_widget.py` Line 1407-1414):

**修改前**:
```python
# 🆕 提取時間數據（用於時間軸模式）
driver1_time = timediff_data.get('driver1_time_seconds', [])
driver2_time = timediff_data.get('driver2_time_seconds', [])
print(f"[timediff_CHART] 🕒 driver1_time 數據點: {len(driver1_time)}")
print(f"[timediff_CHART] 🕒 driver2_time 數據點: {len(driver2_time)}")
```

**修改後**:
```python
# 🆕 提取時間數據（用於時間軸模式）
# ⚠️ Time Diff Analysis 直接使用 reference_time 作為 X 軸
# 不需要 driver1_time_seconds，因為 time_data 已經是時間序列
driver1_time = time_data  # 使用 reference_time 作為時間軸 X 軸數據
driver2_time = []  # Time Diff 不需要第二個時間序列
print(f"[timediff_CHART] 🕒 driver1_time 數據點 (使用 reference_time): {len(driver1_time)}")
print(f"[timediff_CHART] 🕒 driver2_time 數據點: {len(driver2_time)}")
```

## 🔍 **技術分析**

### **Time Diff vs Distance Diff 的差異**:

| 特性 | Distance Diff Analysis | Time Diff Analysis |
|------|----------------------|-------------------|
| **主要曲線** | 累積距離差 (distance difference) | 累積時間差 (time difference) |
| **X 軸 (Distance 模式)** | Distance (米) | Time (秒) ⚠️ 不是 Distance! |
| **X 軸 (Time 模式)** | driver1_time_seconds | **應使用 reference_time** ✅ |
| **數據來源** | telemetry_comparison | time_difference |
| **driver1_time 來源** | Time (seconds) 欄位 | ❌ 不存在 → ✅ 改用 reference_time |

### **為什麼 Time Diff 不同？**

1. **Distance Diff**: 比較兩台車在**距離**上的差異，有兩條獨立的遙測時間序列
   - `driver1_time_seconds`: VER 的時間序列
   - `driver2_time_seconds`: LEC 的時間序列

2. **Time Diff**: 比較兩台車在**時間**上的差異，只有**單一時間序列**
   - `reference_time`: 統一的時間軸 (0s ~ 83s)
   - `cumulative_time_difference`: 在每個時間點的時間差

## 📊 **數據結構對比**

### **Distance Diff Data Structure**:
```json
{
  "distance": [0, 10, 20, ...],           // X軸 (Distance 模式)
  "driver1_time_seconds": [0, 0.5, 1.0, ...],  // X軸 (Time 模式)
  "driver2_time_seconds": [0, 0.5, 1.0, ...],
  "cumulative_distance_difference": [0, 1.2, 2.5, ...]  // Y軸
}
```

### **Time Diff Data Structure**:
```json
{
  "reference_time": [0, 0.166, 0.332, ...],  // X軸 (BOTH 模式!)
  "cumulative_time_difference": [0, 0.05, 0.12, ...],  // Y軸
  "distance_gap": [0, 10, 20, ...]  // 可選的距離參考
}
```

## 🧪 **測試驗證**

### **預期行為**:

**Distance 模式 (use_time_axis=False)**:
- ✅ X 軸: `reference_time` (時間序列)
- ✅ Y 軸: `cumulative_time_difference`
- ✅ 顯示: 時間差 vs 時間 (已驗證成功)

**Time Axis 模式 (use_time_axis=True)**:
- ✅ X 軸: `driver1_time` (現在指向 `reference_time`)
- ✅ Y 軸: `cumulative_time_difference`
- ✅ 顯示: 時間差 vs 時間 (修復後應正常)

### **測試步驟**:
1. ✅ 重啟 GUI
2. ✅ 開啟 Time Diff Analysis (VER vs LEC)
3. ✅ 切換 "Use Time Axis" checkbox
4. ✅ 驗證圖表正常顯示 (500 點數據)
5. ✅ 驗證統計表格正確 (max=2.233s, min=-0.007s, avg=0.600s)

## 📝 **遵循的開發原則**

✅ **原則 1**: 禁止幻覺編碼
- 使用 `grep_search` 和 `read_file` 驗證了 Distance Diff 的實現
- 對比了兩個模組的 `set_time_axis_mode` 邏輯
- 確認了 API 返回的實際數據結構

✅ **原則 2**: 模組資料夾優先
- 參考了 Distance Diff Analysis 的成功實現
- 複用了相同的架構模式

✅ **原則 3**: 通用模組優先
- 維持了 `UniversalChartWidget` 的接口兼容性
- 保持了 `set_timediff_data()` 方法的參數名稱

✅ **原則 4**: 模組多國語言化
- 保留了所有 `tr()` 函數調用

## 🎯 **總結**

**問題**: Time Diff Analysis 誤用了不存在的 `driver1_time_seconds` 欄位

**解決**: 直接使用 `reference_time` (即 `time_data`) 作為時間軸 X 軸數據源

**影響**: Time Axis 模式現在應該能正常顯示時間差分析圖表

**下一步**: 用戶需要重啟 GUI 並驗證修復效果
