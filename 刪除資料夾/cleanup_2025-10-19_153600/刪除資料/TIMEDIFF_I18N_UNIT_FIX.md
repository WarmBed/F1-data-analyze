# Time Diff Analysis - 多國語言化與單位修復報告

## 🎯 **修復問題清單**

### **問題 1**: Y 軸標題未多國語言化且單位錯誤
- **位置**: `timediff_analysis_chart_widget.py` Line 59
- **錯誤**: `tr('time_diff_m', '時間差距 (m)')`
- **修正**: `tr('cumulative_time_diff_s', 'Cumulative Time Difference (s)')`
- **原因**: Time Diff 是時間差，單位應該是秒 (s)，不是米 (m)

### **問題 2**: 固定垂直線標籤單位錯誤
- **位置**: `timediff_analysis_chart_widget.py` Line 637
- **錯誤**: `f"{tr('time_diff_label', '時間差')}: {timediff:.1f} m"`
- **修正**: `f"{tr('time_diff_label', 'Time Diff')}: {timediff:.3f} s"`
- **改進**: 
  - 單位從 `m` 改為 `s`
  - 精度從 `.1f` 提升到 `.3f`（顯示毫秒級）
  - 多國語言化英文 fallback

### **問題 3**: 連動垂直線標籤單位錯誤
- **位置**: `timediff_analysis_chart_widget.py` Line 707
- **錯誤**: `f"{tr('time_diff_label', '時間差')}: {value1:.1f} {data_label}"`
- **修正**: `f"{tr('time_diff_label', 'Time Diff')}: {value1:.3f} s"`
- **改進**: 同問題 2

### **問題 4**: Y 軸範圍固定 ±100
- **位置**: `timediff_analysis_chart_widget.py` Line 201-212
- **錯誤**: 強制 Y 軸範圍至少 -100 到 +100
- **修正**: 動態範圍，最小跨度 0.5 秒
- **改進**:
  ```python
  # ❌ 舊邏輯
  self.min_timediff = min(self.min_timediff, -100)
  self.max_timediff = max(self.max_timediff, 100)
  
  # ✅ 新邏輯
  if (self.max_timediff - self.min_timediff) < 0.5:
      center = (self.max_timediff + self.min_timediff) / 2
      self.min_timediff = center - 0.25
      self.max_timediff = center + 0.25
  ```

### **問題 5**: X 軸標題在未勾選 Use Time Axis 時顯示錯誤
- **位置**: `timediff_analysis_chart_widget.py` Line 737-748
- **錯誤**: 未勾選時顯示 `self.x_axis_title`（距離 (m)）
- **修正**: 永遠顯示 `tr('time_s', 'Time (s)')`
- **原因**: Time Diff Analysis 的 X 軸**永遠是時間**，不像 Distance Diff 有距離/時間切換

## 📊 **Time Diff vs Distance Diff 的根本差異**

### **Distance Diff Analysis**:
```
未勾選 Use Time Axis:
- X 軸: Distance (m) - 賽道距離
- Y 軸: Cumulative Distance Difference (m)
- 數據源: distance 欄位

勾選 Use Time Axis:
- X 軸: Time (s) - 車手時間序列
- Y 軸: Cumulative Distance Difference (m)
- 數據源: driver1_time_seconds / driver2_time_seconds
```

### **Time Diff Analysis**:
```
未勾選 Use Time Axis:
- X 軸: Time (s) - reference_time ← 時間!
- Y 軸: Cumulative Time Difference (s)
- 數據源: reference_time 欄位

勾選 Use Time Axis:
- X 軸: Time (s) - reference_time ← 還是時間!
- Y 軸: Cumulative Time Difference (s)
- 數據源: reference_time 欄位（同上）

⚠️ 結論: Time Diff 的 X 軸永遠是時間，不需要切換!
```

## 🔧 **修復後的行為**

### **Y 軸標題**:
- ✅ 顯示: `Cumulative Time Difference (s)`
- ✅ 多國語言化: `tr('cumulative_time_diff_s', ...)`
- ✅ 單位正確: `(s)` 秒

### **X 軸標題**:
- ✅ 永遠顯示: `Time (s)`
- ✅ 無論是否勾選 Use Time Axis
- ✅ 多國語言化: `tr('time_s', ...)`

### **垂直線標籤**:
- ✅ 固定線: `Time Diff: 2.123 s`
- ✅ 連動線: `Time Diff: 0.456 s`
- ✅ 精度提升: `.3f`（毫秒級）
- ✅ 單位正確: `s`

### **Y 軸動態範圍**:
- ✅ 根據實際數據自動調整
- ✅ 最小跨度: 0.5 秒
- ✅ 不再強制 ±100
- ✅ 範例: VER vs LEC 數據範圍 -0.007s ~ 2.233s → 顯示約 -0.25s ~ 2.5s

## 📝 **測試驗證**

### **測試步驟**:
1. ✅ 重啟 GUI
2. ✅ 開啟 Time Diff Analysis (VER vs LEC, Lap 99)
3. ✅ 檢查 Y 軸標題: 應顯示 `Cumulative Time Difference (s)`
4. ✅ 檢查 X 軸標題: 應顯示 `Time (s)`
5. ✅ 檢查 Y 軸範圍: 應該是動態的，不是 ±100
6. ✅ 切換 Use Time Axis checkbox
7. ✅ 確認 X 軸標題不變（還是 `Time (s)`）
8. ✅ 滑鼠懸停檢查垂直線標籤: 應顯示 `Time Diff: x.xxx s`

### **預期結果**:
- Y 軸: `-0.25s ~ 2.5s` (動態範圍)
- X 軸: `0s ~ 83s` (時間範圍)
- 標籤: `Time Diff: 0.600 s` (三位小數)
- 無論是否勾選 Use Time Axis，顯示應該一致

## 🎯 **遵循的開發原則**

✅ **原則 1**: 禁止幻覺編碼
- 使用 `grep_search` 驗證了所有標籤位置
- 使用 `read_file` 檢查了實際實現

✅ **原則 2**: 模組資料夾優先
- 參考了 Distance Diff Analysis 的邏輯
- 理解了兩者的根本差異

✅ **原則 3**: 通用模組優先
- 維持了 `tr()` 函數的使用模式

✅ **原則 4**: 模組多國語言化
- 所有用戶可見字串都使用 `tr()` 包裹
- 提供了英文 fallback 值

## 📋 **修改文件清單**

1. `modules/gui/lap_analysis/timediff_analysis/timediff_analysis_chart_widget.py`
   - Line 59: Y 軸標題單位修正
   - Line 201-212: Y 軸動態範圍
   - Line 637: 固定線標籤單位修正
   - Line 707: 連動線標籤單位修正
   - Line 737-748: X 軸標題永遠顯示時間

## 🚀 **總結**

**Time Diff Analysis 的特殊性**:
- X 軸永遠是時間 (reference_time)
- Y 軸永遠是時間差 (s)
- 不需要距離/時間切換（因為 X 軸本來就是時間）
- Use Time Axis checkbox 在 Time Diff 中實際上沒有意義

**建議**: 
考慮在 Time Diff Analysis 中隱藏或禁用 "Use Time Axis" checkbox，因為它不會改變任何顯示行為。
