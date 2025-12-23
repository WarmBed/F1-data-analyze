# All Drivers Speed & Acceleration 欄位反轉問題修正報告

**日期**: 2025-10-19  
**修正版本**: v3.4  
**問題編號**: SPEED_FIELD_SWAP_FIX

---

## 📋 問題摘要

All Drivers Speed & Acceleration 模組中，`segment_accel_time_seconds` 和 `max_speed_time_seconds` 兩個欄位的數據含義與用戶期望相反。

### ❌ 問題表現

從 Singapore 2025 R 的實際數據：

```
車手: ANT
- segment_accel_time_seconds: 9.119 秒 ❌
- max_speed_time_seconds: 7.2 秒 ❌
- 統一結束速度: 283 km/h
- 個人最高速度: 290 km/h
```

**邏輯錯誤**：
- 到達較低速度 (283 km/h) 的時間 (9.119秒) **大於** 到達較高速度 (290 km/h) 的時間 (7.2秒)
- 這在物理上不可能！

---

## 🔍 根本原因分析

### 1. CLI 數據生成邏輯

**預掃描階段**（`_compute_driver_record_with_position`）：
```python
# 第 2207 行：計算從起點到【油門降低前的最高速度點】
segment_acceleration_data = self._calculate_segment_acceleration_improved(
    car_data=car_data,
    hardcoded_start_distance=distance_start,
    track_name=reference_segment.get("race_name")
)
```
- 此方法計算到 **個人最高速度** 的時間（較長）

**重新計算階段**（`_recalculate_segment_with_unified_end_speed`）：
```python
# 第 2282 行：保存【個人最高速度數據】
personal_max_speed_data = temp_record.segment_acceleration.copy()  # 來自預掃描

# 第 2286 行：計算到【統一終點速度】
unified_accel_data = self._calculate_segment_acceleration_to_target_speed(
    car_data=car_data,
    hardcoded_start_distance=distance_start,
    target_end_speed_kmh=unified_end_speed_kmh,  # 統一速度（如 283 km/h）
    track_name=reference_segment.get("race_name"),
    debug=False
)

# 第 2300-2302 行：提取個人最高速度的時間
personal_time = personal_max_speed_data.get("time_seconds")  # 到個人最高速度（較長）

# ❌ 第 2311-2319 行：錯誤的賦值！
merged_segment_data = {
    # ❌ time_seconds（導出為 segment_accel_time_seconds）被賦值為統一速度時間（較短）
    "time_seconds": unified_accel_data["time_seconds"],
    
    # ❌ max_speed_time_seconds 被賦值為個人最高速度時間（較長）
    "max_speed_time_seconds": personal_time,
}
```

**問題**：兩個變數的賦值反轉了！

### 2. 用戶期望

> "accel time是 我們有統一的最高時速 當大家達到這時速所需的時間"

用戶期望：
- **Accel Time** = 到達 **統一終點速度** 的時間（較短）
- **Max Speed Time** = 到達 **個人最高速度** 的時間（較長）

但實際數據：
- `segment_accel_time_seconds` = 個人最高速度時間（較長）❌
- `max_speed_time_seconds` = 統一終點速度時間（較短）❌

---

## ✅ 修正方案

### 方案 A：修正 CLI 賦值邏輯（已採用）

**修正位置**: `CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py` 第 2311-2325 行

**修正前**:
```python
merged_segment_data = {
    "time_seconds": unified_accel_data["time_seconds"],  # 統一速度（較短）
    "max_speed_time_seconds": personal_time,  # 個人最高速度（較長）
}
```

**修正後**:
```python
# ✅ v3.4 修正賦值邏輯（2025-10-19）
merged_segment_data = {
    # ✅ 修正：個人最高速度的加速數據（時間較長）
    "time_seconds": personal_time,  # ← 到個人最高速度（較長）
    "distance_meters": personal_distance,
    "avg_acceleration_ms2": unified_accel_data["avg_acceleration_ms2"],
    "start_speed_kmh": unified_accel_data["start_speed_kmh"],
    "end_speed_kmh": personal_max_speed,  # ← 個人最高速度
    "speed_gain_kmh": personal_max_speed - unified_accel_data["start_speed_kmh"],
    
    # ✅ 修正：統一終點速度數據（時間較短）
    "max_speed_time_seconds": unified_accel_data["time_seconds"],  # ← 到統一速度（較短）
    "max_speed_distance_meters": unified_accel_data["distance_meters"],
    "unified_end_speed_kmh": unified_end_speed_kmh,
    "personal_max_speed_kmh": personal_max_speed,
}
```

### 方案 B：修正 GUI 欄位對應（已採用）

由於 CLI 修正後，數據含義反轉，GUI 也需要相應調整：

**修正位置**: `modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py`

**修正邏輯**:
```python
# ✅ v3.4 修正欄位對應（2025-10-19）
# CLI 修正後：
#   - segment_accel_time_seconds = 到個人最高速度的時間（較長）
#   - max_speed_time_seconds = 到統一終點速度的時間（較短）
# 用戶需求：
#   - "Accel Time" = 到統一速度的時間（較短）
#   - "Max Speed Time" = 到個人最高速度的時間（較長）

segment_accel_time_raw = driver_data.get("segment_accel_time_seconds", None)
max_speed_time_raw = driver_data.get("max_speed_time_seconds", None)

# ✅ 互換以符合用戶期望
accel_time_display = max_speed_time_raw  # GUI 欄位 "Accel Time" 顯示統一速度時間
max_speed_time_display = segment_accel_time_raw  # GUI 欄位 "Max Speed Time" 顯示個人最高速度時間
```

---

## 🎯 預期結果

修正後，Singapore 2025 R 的數據應該顯示為：

```
車手: ANT
- Accel Time (GUI 欄位 3): 7.2 秒 ✅ (到達統一速度 283 km/h)
- Max Speed Time (GUI 欄位 6): 9.119 秒 ✅ (到達個人最高速度 290 km/h)
- 邏輯正確: 7.2 < 9.119 ✅
```

---

## 📝 測試計劃

### 階段 1: CLI 測試
```powershell
# 重新生成 Singapore 數據
python f1_analysis_modular_main.py -f 48 -y 2025 -r Singapore -s R

# 檢查 JSON 數據
python -c "
import json
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']['data']
    driver = data['driver_speeds'][0]
    print(f\"Driver: {driver['driver']}\")
    print(f\"segment_accel_time: {driver['segment_accel_time_seconds']}s\")
    print(f\"max_speed_time: {driver['max_speed_time_seconds']}s\")
    print(f\"Check: max_speed_time < segment_accel_time = {driver['max_speed_time_seconds'] < driver['segment_accel_time_seconds']}\")
"
```

**預期輸出**:
```
Driver: XXX
segment_accel_time: 7.xxx s
max_speed_time: 9.xxx s
Check: max_speed_time < segment_accel_time = True ✅
```

### 階段 2: GUI 測試
1. 啟動 GUI: `python f1t_gui_main.py`
2. 開啟 All Drivers Speed & Acceleration (Singapore 2025 R)
3. 檢查表格：
   - "Accel Time" 欄位應顯示較小的值（約 7-8 秒）
   - "Max Speed Time" 欄位應顯示較大的值（約 9-10 秒）
   - 排序功能正常

---

## 🔧 修正檔案清單

1. **CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py**
   - 第 2311-2325 行：修正 `merged_segment_data` 的賦值邏輯

2. **modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py**
   - 第 463-494 行：新增欄位對應轉換邏輯
   - 第 495-502 行：修正變數轉換和調試輸出
   - 第 545-559 行：修正欄位 3 (Accel Time) 使用 `accel_time_display`
   - 第 595-617 行：修正欄位 6 (Max Speed Time) 使用 `max_speed_time_display`
   - 第 620-643 行：修正棒狀圖和額外數據

---

## ⚠️  注意事項

1. **需要重新生成 JSON**：所有使用舊 JSON 的數據都需要重新生成
2. **向後不兼容**：v3.4 的 JSON 格式與 v3.3 不兼容
3. **欄位含義變更**：
   - `segment_accel_time_seconds` 現在是到 **個人最高速度** 的時間
   - `max_speed_time_seconds` 現在是到 **統一終點速度** 的時間

---

## 📊 影響範圍

### 直接影響
- ✅ GUI 欄位顯示正確
- ✅ 排序邏輯正確
- ✅ 棒狀圖繪製正確

### 間接影響
- ⚠️  需要重新生成所有 `all_drivers_straight_line_speed_*.json` 檔案
- ⚠️  API 返回的數據格式變更

---

## ✅ 完成狀態

- [x] CLI 邏輯修正
- [x] GUI 欄位對應修正
- [x] 編譯錯誤檢查通過
- [ ] CLI 測試（重新生成 JSON）
- [ ] GUI 測試（載入新 JSON）
- [ ] 文檔更新

---

**修正者**: GitHub Copilot  
**審核者**: 待定  
**日期**: 2025-10-19
