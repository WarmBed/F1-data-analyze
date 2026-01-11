# Driver Strategy 模組 - Live Timing 演算法與邏輯說明

## 1. 模組概述

**Driver Strategy** 是 Live Timing 系統中的策略預測模組，用於即時顯示和預測車手的圈速表現。主要功能包括：

- 實際圈速曲線（青色實線 + 圓形標記）
- 預測圈速曲線（紫色虛線）
- 預測範圍填充區域（紫色半透明）
- SC/VSC 區域標記（黃色填充）
- 進站標記（黃色垂直線 + "PIT" 文字）
- 當前圈數指示器（青色虛線）
- **多車手即時追蹤**（同時追蹤 20 位車手，切換即時顯示完整歷史）

---

## 2. 核心架構

### 2.1 類別結構

```
DriverLapData          - 輕量級數據結構，儲存單一車手的圈速數據
DriverStrategyWidget   - PyQt5 原生繪圖 Widget，負責視覺化呈現
LiveTimingDriverStrategy (MDI) - MDI 子視窗包裝器，管理多車手數據
```

### 2.2 數據流

```
Snapshot 更新 → _on_snapshot_updated()
              ↓
     更新所有 20 位車手的 DriverLapData
              ↓
     _refresh_widget_from_driver_data() → 刷新當前選中車手的 Widget
              ↓
     _calculate_all_predictions() → 計算預測圈速
              ↓
     paintEvent() → 繪製圖表
```

---

## 3. 預測演算法

### 3.1 Stint-Based 圈速預測模型

預測圈速的核心公式：

```
predicted_lap_time = base_lap_time + tyre_degradation + fuel_effect + compound_advantage + correction_factor
```

#### 3.1.1 基準圈速計算 (`_calculate_base_lap_time`)

```python
# 從實際圈速中取第 5-25 百分位的平均值作為基準
sorted_times = sorted(valid_times)
n = len(sorted_times)
if n > 5:
    start_idx = max(1, n // 20)   # 第 5 百分位
    end_idx = max(2, n // 4)       # 第 25 百分位
    base_time = average(sorted_times[start_idx:end_idx])
elif n == 5:
    # 5 圈特殊處理：取中間 3 圈平均
    base_time = average(sorted_times[1:4])
else:
    base_time = min(sorted_times)
```

#### 3.1.2 輪胎衰退計算 (`_calculate_stint_prediction`)

使用**時變線性衰退模型**：

```python
degradation(t) = base_rate * t + 0.5 * acceleration * t²

# 其中：
# t = tyre_age (輪胎圈數，從 1 開始)
# base_rate = 配方基礎衰退率 (例如 SOFT=0.08, MEDIUM=0.05, HARD=0.03)
# acceleration = 衰退加速係數 (例如 SOFT=0.003, MEDIUM=0.002, HARD=0.001)
```

**衰退參數來源**：從 `tire_degradation` 資料庫獲取賽道特定值，若無則使用預設值。

#### 3.1.3 燃油效果計算 (`_get_fuel_effect`)

```python
fuel_effect = -fuel_effect_coefficient * fuel_consumed_kg

# 其中：
# fuel_consumed_kg = fuel_kg_per_lap * (lap_number - 1)
# fuel_effect_coefficient = 約 0.03 秒/kg (賽道特定)
# fuel_kg_per_lap = 約 1.8 kg/圈 (賽道特定)
```

**結果**：燃油減少 → 車更輕 → 更快（負值）

#### 3.1.4 配方抓地力優勢

```python
grip_advantage = {
    'SOFT': -0.5,       # 軟胎快 0.5 秒
    'MEDIUM': -0.25,    # 中性胎快 0.25 秒
    'HARD': 0.0,        # 硬胎為基準
    'INTERMEDIATE': -0.3,
    'WET': -0.2
}
```

#### 3.1.5 自我修正機制 (`_apply_self_correction`)

```python
# 計算實際與預測的平均誤差
errors = [actual - predicted for each lap]
avg_error = average(errors)

# 平滑更新修正因子 (70% 舊值 + 30% 新值)
correction_factor = correction_factor * 0.7 + avg_error * 0.3
```

---

### 3.2 進站預測演算法 (`_update_predicted_pit_lap`)

```python
# 1. 從資料庫獲取最佳 stint 長度
optimal_stint = database[circuit][compound]  # 例如 SOFT=18, MEDIUM=28, HARD=40

# 2. F87 省胎補償 (可延長 stint)
adjusted_stint = optimal_stint * (1 + tire_saving_adjustment)
# tire_saving_adjustment: NONE=0%, LIGHT=+8%, MODERATE=+15%, HEAVY=+25%

# 3. 計算預測進站圈數
predicted_pit_lap = stint_start_lap + adjusted_stint

# 4. 判斷是否需要進站
if predicted_pit_lap >= total_laps:
    # 可以用當前輪胎完成比賽，無需進站
else:
    # 記錄預測進站圈數
```

---

### 3.3 F87 省胎評估系統

#### 3.3.1 省胎分數計算 (`calculate_tire_saving_for_driver_data`)

省胎評估基於 **Throttle Baseline Database**，比較車手實際油門使用率與賽道基準值：

```python
# 1. 獲取賽道的 Throttle 基準值
baseline_ratio = database[circuit].full_throttle_ratio.mean  # 例如 Monza = 0.42
baseline_std = database[circuit].full_throttle_ratio.std     # 例如 0.03

# 2. 計算車手最近 5 圈的平均 full_throttle_ratio
recent_throttle = [lap_throttle_ratios[lap] for lap in recent_laps]
current_ratio = average(recent_throttle)

# 3. 計算省胎分數 (SF%)
threshold = baseline_ratio - baseline_std
if current_ratio >= threshold:
    SF% = 0  # 正常推進，無省胎
else:
    SF% = (baseline_ratio - current_ratio) / baseline_ratio * 100
    SF% = min(50, SF%)  # 限制最大 50%

# 4. 判斷省胎等級
if SF% < 5:    level = "NONE"
elif SF% < 15: level = "LIGHT"
elif SF% < 30: level = "MODERATE"
else:          level = "HEAVY"
```

#### 3.3.2 Throttle 樣本累積

每次 snapshot 更新時累積 throttle 樣本：

```python
# 每次 snapshot
if current_lap != last_lap:
    # 圈數變化：計算上一圈的 full_throttle_ratio
    samples = current_lap_throttle_samples
    full_throttle_count = count(s >= 95 for s in samples)
    ratio = full_throttle_count / len(samples)
    lap_throttle_ratios[last_lap] = ratio
    
    # 重置為新圈
    current_lap_throttle_samples = [new_throttle_value]
else:
    # 同一圈：累積樣本
    current_lap_throttle_samples.append(throttle_value)
```

---

## 4. 多車手追蹤架構

### 4.1 設計原則

系統**同時追蹤所有 20 位車手**，切換車手時無需重新載入，可即時顯示完整歷史數據。

```python
# MDI 層級
_all_drivers_lap_data: Dict[str, DriverLapData]  # 所有車手的數據

# 每位車手的 DriverLapData 包含:
- actual_lap_times: Dict[int, float]       # {圈數: 圈速}
- lap_compounds: Dict[int, str]            # {圈數: 配方}
- pit_laps: List[int]                      # 進站圈數列表
- pit_out_laps: set                        # 出站圈集合
- lap_throttle_ratios: Dict[int, float]    # {圈數: full_throttle_ratio}
- lap_tire_saving_scores: Dict[int, float] # {圈數: SF%}
```

### 4.2 性能優化

```python
# 只在圈數變化時更新
if current_max_lap == self._last_max_lap:
    return  # 跳過更新
```

---

## 5. 數據排除規則

以下圈數會從預測和顯示中排除：

| 類型 | 說明 | 處理方式 |
|------|------|----------|
| **SC 圈** | 安全車出動期間 | 不記錄圈速，不繪製數據點 |
| **SC Restart 圈** | SC 結束後第一圈 | 不用於預測計算 |
| **PIT 圈** | 進站當圈 | 記錄進站，不計入預測基準 |
| **PIT Out 圈** | 出站後第一圈 | 不用於預測計算 |

---

## 6. 三配方預測線

在預測進站點之後，系統會繪製三條配方的預測曲線（SOFT/MEDIUM/HARD），供策略比較：

```python
# 只在 PIT Est 之後顯示三條配方線
if lap >= current_predicted_pit:
    # 計算換胎後的輪胎圈數 (從進站後重新計算)
    alt_tyre_age = lap - current_predicted_pit + 1
    
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        predicted = calculate_stint_prediction(lap, alt_tyre_age, compound, ...)
        multi_compound_predictions[compound][lap] = predicted
```

---

## 7. 歷史回放模擬

當載入歷史數據時，系統會**逐圈模擬即時修正過程**，確保歷史回放產生與即時觀看相同的預測結果：

```python
def _simulate_realtime_corrections(full_lap_times, pit_laps):
    correction_factor = 0.0
    simulated_lap_times = {}
    
    for lap_num in sorted(full_lap_times.keys()):
        if lap_num in excluded_laps:
            continue
        
        # 模擬即時數據到達
        simulated_lap_times[lap_num] = full_lap_times[lap_num]
        
        if len(simulated_lap_times) >= 3:
            # 計算預測
            calculate_predictions_with_data(simulated_lap_times)
            # 應用修正
            apply_correction_with_data(simulated_lap_times)
```

---

## 8. 資料庫配置

系統依賴三個主要資料庫（從 API 獲取）：

| 資料庫 | 用途 | 內容 |
|--------|------|------|
| `track_features` | 賽道特性 | 賽道類型、進站窗口 |
| `tire_degradation` | 輪胎衰退 | 各配方基礎衰退率、衰退加速係數、最佳 stint 長度 |
| `fuel_coefficients` | 燃油係數 | 每圈燃油消耗、燃油效果係數 |
| `throttle_baseline` | 油門基準 | 各賽道 full_throttle_ratio 統計值 |

---

## 9. 顏色配置

```python
COLOR_ACTUAL = '#4ECDC4'          # 青色 - 實際圈速
COLOR_PREDICTED = '#BB86FC'       # 淺紫色 - 預測圈速
COLOR_SC_ZONE = '#FFD700'         # 黃色 - SC/VSC 區域
COLOR_PIT_MARKER = '#FFD700'      # 黃色 - 進站標記
COLOR_FUEL_SAVING = '#00CC00'     # 綠色 - 省油區域

# 輪胎顏色
COLOR_TYRE_SOFT = '#FF3333'       # 紅色
COLOR_TYRE_MEDIUM = '#FFCC00'     # 黃色
COLOR_TYRE_HARD = '#FFFFFF'       # 白色
COLOR_TYRE_INTERMEDIATE = '#00CC00' # 綠色
COLOR_TYRE_WET = '#0066FF'        # 藍色
```

---

## 10. 滑鼠懸停視窗

當滑鼠移動到圖表上時，會顯示該圈的詳細資訊：

| 項目 | 說明 | 顏色 |
|------|------|------|
| **Actual** | 實際圈速 (M:SS.mmm 格式) | 青色 (#4ECDC4) |
| **Predicted** | 預測圈速 (M:SS.mmm 格式) | 紫色 (#BB86FC) |
| **Delta** | 實際與預測的差異 (±X.XXX 秒) | 綠色 (較快) / 紅色 (較慢) |
| **Tyre** | 輪胎配方 | 灰色 |

### Delta 顏色規則
- **綠色 (#00FF00)**：實際圈速 < 預測 = 比預測快
- **紅色 (#FF4444)**：實際圈速 > 預測 = 比預測慢

---

## 11. 即時賽道演進計算 (Phase 3)

### 11.1 概念

**賽道演進 (Track Evolution)** = 比賽過程中賽道逐漸變快的現象
- 原因：輪胎橡膠堆積在賽道上、賽道溫度變化
- 效果：通常是**負值**（例如 -0.015 s/lap = 每圈快 0.015 秒）

### 11.2 計算邏輯

使用**全場 20 車手中位數統計法**：

```python
# Step 1: 收集所有車手的有效圈速（排除異常圈）
for each driver in all_20_drivers:
    for each lap in driver.actual_lap_times:
        if lap is NOT (SC / VSC / PIT / PIT OUT / SC Restart):
            lap_times_by_number[lap].append(lap_time)

# Step 2: 計算每圈的中位數（至少 5 位車手）
for lap_num, times in lap_times_by_number.items():
    if len(times) >= 5:
        lap_medians[lap_num] = median(times)

# Step 3: 計算賽道演進（相對於第一圈）
baseline = lap_medians[first_valid_lap]
for lap_num, median in lap_medians.items():
    track_evolution[lap_num] = median - baseline
    # 負值 = 賽道變快, 正值 = 賽道變慢
```

### 11.3 應用到預測公式

```python
# 原公式
predicted = base_time + tyre_degradation + fuel_effect + compound_advantage

# 新公式（加入賽道演進）
track_evo_effect = track_evolution.get(lap, 0)
predicted = base_time + tyre_degradation + fuel_effect + compound_advantage + track_evo_effect
```

### 11.4 排除規則

| 圈類型 | 排除原因 |
|--------|----------|
| SC 圈 | 速度異常慢，不代表賽道狀態 |
| VSC 圈 | 速度異常慢 |
| PIT 圈 | 包含進站時間 |
| PIT OUT 圈 | 出站後暖胎，速度不穩定 |
| SC Restart 圈 | 重啟混亂，不穩定 |

---

## 12. 待改進項目

- [x] 整合 Long-Run 的賽道演進 (Track Evolution) 效果 - Phase 3 即時統計法
- [x] 滑鼠懸停視窗顯示預估值、實際值、差異值
