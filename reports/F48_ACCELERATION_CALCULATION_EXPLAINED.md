# F48 加速度計算邏輯完整說明

## 問題 3: STR 加速度計算錯誤深度分析

### 現狀總結

**China 2025 數據**：
- 統一速度範圍：**110→310 km/h** (Δv = 200 km/h = 55.56 m/s)
- STR 數據：
  - 加速時間：7.119s
  - JSON 加速度：2.93 m/s²
  - **正確加速度應為**：55.56 / 7.119 = **7.80 m/s²**
  - **誤差**：4.87 m/s² (66% 錯誤！)

**反推分析**：
```
已知：a = 2.93 m/s²，Δt = 7.119s
反推：Δv = a × Δt = 2.93 × 7.119 = 20.86 m/s = 75.1 km/h

結論：STR 實際計算使用的速度差只有 75.1 km/h，不是 200 km/h！
可能的速度範圍：110→185 km/h
```

---

## 📖 加速度計算邏輯說明

### 方法 1：舊方法（已棄用）

**方法名稱**：`_calculate_acceleration_in_segment`
**位置**：Line 944-1038
**速度範圍**：固定 **100→250 km/h**
**公式**：
```python
velocity_change = (250 - 100) / 3.6  # = 41.67 m/s
avg_acceleration = velocity_change / time_diff
```

**問題**：
- ❌ 使用固定速度範圍，無法適應不同賽道
- ❌ 不支援統一速度範圍
- ❌ 已被新方法取代

---

### 方法 2：新方法（正在使用）

**方法名稱**：`_calculate_acceleration_in_position_range`
**位置**：Line 1040-1238
**速度範圍**：動態統一範圍（例如 110→310 km/h）
**調用位置**：`_compute_driver_record_with_position` (Line 1356-1365)

**計算流程**：

#### 步驟 1: 獲取統一速度範圍

```python
# 從 reference_segment 獲取
unified_start_speed = reference_segment.get("unified_start_speed")  # 例如 110 km/h
unified_end_speed = reference_segment.get("unified_end_speed")      # 例如 310 km/h
```

#### 步驟 2: 計算搜索範圍

```python
# 基於賽道主直線長度（硬編碼）
TRACK_STRAIGHT_LENGTHS = {
    "China": 1200,
    "Azerbaijan": 2200,
    "Monaco": 400,
    # ...
}

# 計算搜索起點：從最高速度位置往前推
track_straight_length = 1200  # China
max_speed_distance = 4520.01  # STR 的最高速度位置
calculated_start = max_speed_distance - (track_straight_length - 100)
                 = 4520.01 - (1200 - 100)
                 = 4520.01 - 1100
                 = 3420.01m

search_distance_start = calculated_start
search_distance_end = max_speed_distance + 200 = 4720.01m
```

#### 步驟 3: 尋找起始速度點

**優先級 1**：找到最接近統一起始速度的點
```python
# 在搜索範圍內，找到速度 ≈ 110 km/h 的點
for idx in reversed(search_indices_before_max):
    speed = speeds[idx]
    if speed <= target_speed_low + 10:  # 110 + 10 = 120 km/h
        if abs(speed - target_speed_low) < 2:  # 誤差 < 2 km/h
            speed_start_idx = idx
            break
```

**優先級 2（強制全車手模式）**：如果找不到理想起點
```python
# 使用搜索範圍內最高速度點之前的最小速度
speed_start_idx = search_speeds_before_max.idxmin()
actual_start_speed = search_speeds_before_max[speed_start_idx]
target_speed_low = float(actual_start_speed)  # ✅ 動態調整起始速度！
```

**⚠️ 這是問題的關鍵！** 如果 STR 在搜索範圍內找不到 110 km/h 的點，它會使用**實際最小速度**（例如 110 km/h），但繼續使用較低的起始速度。

#### 步驟 4: 尋找終點速度點

**優先級 1**：找到 ≥ 統一終點速度的點
```python
# 從起始點向後找第一個 >= 310 km/h 的點
for idx in car_data.index:
    if idx >= speed_start_idx and idx <= max_speed_idx:
        speed = speeds[idx]
        if speed >= target_speed_high:  # >= 310 km/h
            speed_end_idx = idx
            break
```

**優先級 2（強制全車手模式）**：如果找不到理想終點
```python
# 使用最高速度點作為終點
speed_end_idx = max_speed_idx
target_speed_high = float(speeds[max_speed_idx])  # ✅ 動態調整終點速度！
```

**⚠️ 這是 STR 問題的根源！** 如果 STR 沒有達到 310 km/h，它會使用**實際最高速度**（例如 185 km/h），導致速度差變小！

#### 步驟 5: 計算加速度

```python
# 計算時間差
time_diff = time_end_sec - time_start_sec  # 7.119s

# 計算速度變化（使用動態調整後的速度範圍）
velocity_change = (target_speed_high - target_speed_low) / 3.6
                = (185 - 110) / 3.6  # ❌ STR 使用了錯誤的範圍！
                = 75 / 3.6
                = 20.83 m/s

# 計算加速度
avg_acceleration = velocity_change / time_diff
                 = 20.83 / 7.119
                 = 2.93 m/s²  # ✅ 符合 JSON 值！
```

#### 步驟 6: 返回數據

```python
return {
    "time_seconds": 7.119,
    "distance_meters": 557.51,
    "avg_acceleration_ms2": 2.93,  # ❌ 使用了錯誤的速度範圍計算
    "speed_start_kmh": 110.0,      # 目標起始速度
    "speed_end_kmh": 185.0,        # ❌ 實際終點速度（不是 310）
    "actual_speed_start_kmh": 110.0,
    "actual_speed_end_kmh": 185.0,
    # ... 其他欄位
}
```

**⚠️ 問題：** Line 61 的 `to_dict()` 方法**沒有提取** `speed_end_kmh` 和 `actual_speed_end_kmh`，所以 JSON 中看不到實際速度範圍！

---

## 🔍 問題根因分析

### 根因 1: 強制全車手模式的副作用

**設計目的**：確保所有車手都有加速度數據，即使沒有達到統一終點速度

**副作用**：
```python
# Line 1183-1188
if speed_end_idx is None:
    speed_end_idx = max_speed_idx
    target_speed_high = float(speeds[max_speed_idx])  # ❌ 動態調整終點速度
```

這導致：
- STR 沒有達到 310 km/h
- 系統自動使用 STR 的最高速度（約 185 km/h）作為終點
- 速度差從 200 km/h 變成 75 km/h
- 加速度從 7.80 m/s² 變成 2.93 m/s²

### 根因 2: JSON 數據不完整

**Line 59-62 的問題**：
```python
result["acceleration_time_100_300_seconds"] = self.acceleration_100_300.get("time_seconds", 0.0)
result["acceleration_distance_100_300_meters"] = self.acceleration_100_300.get("distance_meters", 0.0)
result["avg_acceleration_100_300_ms2"] = self.acceleration_100_300.get("avg_acceleration_ms2", 0.0)
```

**缺少的欄位**：
- ❌ `speed_start_kmh` - 目標起始速度
- ❌ `speed_end_kmh` - 目標終點速度
- ❌ `actual_speed_start_kmh` - 實際測量起始速度
- ❌ `actual_speed_end_kmh` - 實際測量終點速度

**結果**：
- 無法從 JSON 判斷實際使用的速度範圍
- 誤以為所有車手都使用統一速度範圍（110→310）
- 實際上 STR 使用了 110→185（或類似範圍）

### 根因 3: key 命名不一致

**問題**：
- JSON key: `acceleration_time_100_300_seconds`
- 實際範圍: 110→310 km/h（或更小）

**誤導**：
- 用戶以為計算使用 100→300 km/h
- 實際上使用動態範圍（110→185）

---

## 🛠️ 解決方案

### 方案 A: 禁用強制全車手模式（推薦）

**修改位置**：Line 1183-1188

**原始代碼**：
```python
# ✅ 強制全車手模式：如果找不到理想終點，使用最高速度點作為終點
if speed_end_idx is None:
    speed_end_idx = max_speed_idx
    target_speed_high = float(speeds[max_speed_idx])  # ❌ 動態調整
```

**修正代碼**：
```python
# ✅ 嚴格模式：只計算達到統一終點速度的車手
if speed_end_idx is None:
    # 沒有達到統一終點速度，返回 None（不計算加速度）
    return None
```

**優點**：
- ✅ 確保所有車手使用相同的速度範圍
- ✅ 加速度數據可比較
- ✅ 符合用戶預期

**缺點**：
- ❌ 某些車手可能沒有加速度數據（例如 STR）
- ❌ 無法滿足「100% 車手覆蓋率」的需求

---

### 方案 B: 導出實際速度範圍（推薦）

**修改位置**：Line 59-62

**原始代碼**：
```python
result["acceleration_time_100_300_seconds"] = self.acceleration_100_300.get("time_seconds", 0.0)
result["acceleration_distance_100_300_meters"] = self.acceleration_100_300.get("distance_meters", 0.0)
result["avg_acceleration_100_300_ms2"] = self.acceleration_100_300.get("avg_acceleration_ms2", 0.0)
```

**修正代碼**：
```python
result["acceleration_time_100_300_seconds"] = self.acceleration_100_300.get("time_seconds", 0.0)
result["acceleration_distance_100_300_meters"] = self.acceleration_100_300.get("distance_meters", 0.0)
result["avg_acceleration_100_300_ms2"] = self.acceleration_100_300.get("avg_acceleration_ms2", 0.0)

# ✅ 新增：導出實際速度範圍
result["speed_start_kmh"] = self.acceleration_100_300.get("speed_start_kmh", None)
result["speed_end_kmh"] = self.acceleration_100_300.get("speed_end_kmh", None)
result["actual_speed_start_kmh"] = self.acceleration_100_300.get("actual_speed_start_kmh", None)
result["actual_speed_end_kmh"] = self.acceleration_100_300.get("actual_speed_end_kmh", None)
```

**優點**：
- ✅ 透明化實際速度範圍
- ✅ 用戶可以判斷數據是否可比較
- ✅ 保留 100% 覆蓋率
- ✅ 不破壞現有邏輯

**缺點**：
- ❌ JSON 檔案變大（4 個額外欄位）

---

### 方案 C: 修正 key 命名（建議）

**修改位置**：Line 59-62

**原始代碼**：
```python
result["acceleration_time_100_300_seconds"] = ...
result["avg_acceleration_100_300_ms2"] = ...
```

**修正代碼**：
```python
# 動態命名（反映實際速度���圍）
start_speed = int(self.acceleration_100_300.get("speed_start_kmh", 100))
end_speed = int(self.acceleration_100_300.get("speed_end_kmh", 300))
result[f"acceleration_time_{start_speed}_{end_speed}_seconds"] = ...
result[f"avg_acceleration_{start_speed}_{end_speed}_ms2"] = ...
```

**優點**：
- ✅ 命名反映實際速度範圍
- ✅ 避免誤解

**缺點**：
- ❌ 破壞 GUI 兼容性（GUI 期望固定 key 名稱）
- ❌ 需要修改 GUI 代碼

---

### 方案 D: 組合方案（最佳）

**步驟 1**：實施方案 A（禁用強制全車手模式）
**步驟 2**：實施方案 B（導出實際速度範圍）
**步驟 3**：在 GUI 中添加速度範圍顯示

**結果**：
- ✅ 數據準確且可比較
- ✅ 用戶可以看到實際速度範圍
- ✅ 可選擇是否顯示不完整數據的車手

---

## 📊 測試案例

### 案例 1: STR (China 2025)

**統一速度範圍**：110→310 km/h

**當前行為（強制全車手模式）**：
- 起始速度：110 km/h
- 終點速度：185 km/h（實際最高速度，未達到 310）
- 速度差：75 km/h
- 加速度：2.93 m/s² ❌ 錯誤

**修正後（嚴格模式）**：
- 起始速度：110 km/h
- 終點速度：找不到 ≥ 310 km/h 的點
- 結果：返回 None（不計算加速度）✅ 正確

**修正後（導出實際範圍）**：
- 起始速度：110 km/h
- 終點速度：185 km/h
- JSON 顯示：`speed_end_kmh: 185`
- 用戶理解：STR 只加速到 185 km/h，數據不可比較 ✅ 透明

### 案例 2: OCO (China 2025)

**統一速度範圍**：110→310 km/h

**當前行為**：
- 起始速度：110 km/h
- 終點速度：310 km/h（達到統一終點）
- 速度差：200 km/h
- 加速度：4.40 m/s² ✅ 正確

**修正後（不變）**：
- 行為完全相同 ✅

---

## 🎯 推薦實施順序

1. **立即實施**：方案 B（導出實際速度範圍）
   - 修改 Line 59-62
   - 添加 4 個新欄位
   - 重新生成 China JSON
   - 驗證 STR 的 `speed_end_kmh` 是否為 185 km/h

2. **短期實施**：方案 A（禁用強制全車手模式）
   - 修改 Line 1183-1188
   - 返回 None 而非動態調整
   - 重新生成所有賽事數據
   - 統計有多少車手受影響

3. **中期實施**：GUI 顯示實際速度範圍
   - 在表格中添加「實際速度範圍」欄位
   - 標記不完整數據的車手
   - 提供過濾選項

4. **長期實施**：統計分析不同模式的影響
   - 對比嚴格模式 vs 強制模式的覆蓋率
   - 用戶調查：哪種模式更符合預期

---

**報告生成時間**: 2025-10-15
**相關檔案**:
- `CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py`
- Line 944-1038: 舊方法
- Line 1040-1238: 新方法
- Line 59-62: to_dict() 方法
- Line 1183-1188: 強制全車手模式邏輯
