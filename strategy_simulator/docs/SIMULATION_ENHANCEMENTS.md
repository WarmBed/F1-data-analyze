# F1T 賽車策略模擬器 - 增強功能實施計劃

## 文檔建立日期
2026-01-05

## 目的
記錄策略模擬器的現有功能、待實施增強功能及其優先級。

---

## ✅ 已實施功能檢查清單

### 1. **輪胎非線性衰減** ✅ 已完成
**狀態**: 已實施  
**位置**: 
- `strategy_simulator/core/lap_simulator.py` (第 320-420 行)
- `strategy_simulator/data/longrun_loader.py` (第 1085-1150 行)

**實施細節**:
```python
# 時變線性衰減模型 (Cappello & Hoegh 2025)
# degradation(t) = base_rate * t + 0.5 * acceleration * t^2

# 輪胎老化造成的圈速損失 (相比全新輪胎)
if tyre_age <= 1:
    degradation = 0.0  # 新輪胎無損失
else:
    t = tyre_age - 1  # 已完成的圈數
    degradation = deg_rate * t + 0.5 * deg_accel * t * (t - 1)
```

**數據來源**:
- FP2 Long Run 數據分段分析
- 計算前半段與後半段衰減率差異
- 自動計算加速係數 (acceleration coefficient)

**默認值** (當無 Long Run 數據時):
- SOFT: 0.0029 s/lap²
- MEDIUM: 0.0019 s/lap²
- HARD: 0.0012 s/lap²

**效果**:
- 輪胎老化越後期，每圈損失越大
- 符合真實 F1 輪胎「cliff」現象
- 準確反映軟胎早期優勢與後期衰退

---

### 2. **交通影響 (Traffic Loss)** ✅ 已實施
**狀態**: 已實施  
**位置**: 
- `strategy_simulator/core/lap_simulator.py` (第 409-418 行)
- `strategy_simulator/gui/input_panel.py` (第 437-447 行)

**實施細節**:
```python
# 基於起始位置的交通損失 (P1 無損失, P20 最大損失)
if self.params.enable_traffic_simulation:
    position = self.params.starting_position
    base_traffic = (position - 1) * self.params.traffic_loss_per_position
    
    # 隨圈數指數衰減 (車輛拉開距離)
    decay = max(0, 1 - self.params.traffic_decay_rate * (lap_number - 1))
    traffic_loss = base_traffic * decay
```

**參數**:
- `traffic_loss_per_position`: 每個位置的損失 (默認 0.15s)
- `traffic_decay_rate`: 每圈衰減率 (默認 0.05，即 5%/lap)

**效果**:
- P10 起步比 P1 起步第一圈慢約 1.35s
- 隨賽事進行，交通影響逐漸消失
- 反映真實賽車在起步階段的擁擠情況

---

### 3. **第一圈損失 (Formation Lap Loss)** ✅ 已實施
**狀態**: 已實施  
**位置**: 
- `strategy_simulator/core/lap_simulator.py` (第 405-408 行)
- `strategy_simulator/gui/input_panel.py` (第 670 行)

**實施細節**:
```python
# 第一圈特殊損失 (暖胎圈、起步混亂、髒空氣)
if self.params.enable_first_lap_loss and lap_number == 1:
    first_lap_loss = self.params.first_lap_loss
```

**典型值**:
- 約 3-5 秒 (取決於賽道)

**原因**:
- Formation Lap 暖胎不足
- 起步階段的混亂
- 前車髒空氣影響

---

## 🔄 需要增強的功能

### 1️⃣ **Out-lap / In-lap 損失** (最高優先)
**狀態**: ⚠️ 待實施  
**影響範圍**: 進站策略準確性

#### 當前實施狀態
- ✅ 固定 Pit Loss 值 (Green Flag: ~21s, SC: ~11s, VSC: ~14s)
- ❌ 未區分 In-lap (進 Pit 前一圈) 與 Out-lap (出 Pit 後一圈) 的性能損失

#### 真實情況分析
**In-lap 損失來源**:
- 輪胎管理 (不再推進，保護輪胎進站)
- 燃油節省 (減少燃油消耗)
- 煞車冷卻準備
- **估計損失**: 0.5-1.5 秒/圈

**Out-lap 損失來源**:
- 新輪胎尚未達到工作溫度
- 煞車尚未達到工作溫度
- 輪胎表面橡膠未完全活化
- **估計損失**: 1.0-3.0 秒/圈

**賽道差異**:
| 賽道類型 | In-lap 損失 | Out-lap 損失 | 原因 |
|---------|------------|-------------|------|
| 高速賽道 (Monza) | 0.5-1.0s | 1.0-2.0s | 少彎角，易暖胎 |
| 街道賽道 (Monaco) | 1.0-1.5s | 2.0-3.0s | 多彎角，難暖胎 |
| 混合賽道 (Suzuka) | 0.7-1.2s | 1.5-2.5s | 中等難度 |

#### 實施計劃
**階段 1: 數據分析** (使用 Live Timing)
```python
# 分析工具: CLI_modules/cli/analyzer/live_timing_analyzer.py
# 提取真實 In-lap / Out-lap 時間

def analyze_pit_lap_times(session, driver):
    """分析進站前後的圈速損失"""
    pit_laps = driver.laps[driver.laps['PitInTime'].notna()]
    
    for pit_lap in pit_laps:
        # In-lap: 進站前一圈
        in_lap_time = pit_lap['LapTime']
        baseline = get_baseline_time(driver, pit_lap['LapNumber'] - 3)
        in_lap_loss = in_lap_time - baseline
        
        # Out-lap: 出站後一圈
        out_lap_time = pit_laps[pit_laps['LapNumber'] == pit_lap['LapNumber'] + 1]
        out_lap_loss = out_lap_time - baseline
    
    return {
        'in_lap_loss_avg': np.mean(in_lap_losses),
        'out_lap_loss_avg': np.mean(out_lap_losses)
    }
```

**階段 2: 資料庫建立**
- 收集 2024-2025 年所有賽事的 In-lap / Out-lap 數據
- 按賽道分類統計平均值與標準差
- 建立 JSON 資料庫: `strategy_simulator/data/pit_lap_losses.json`

**階段 3: 模擬器整合**
```python
# 在 LapSimulator.calculate_lap_time() 中新增
if is_in_lap:
    # 進站前一圈的損失
    in_lap_loss = self.params.get_in_lap_loss(track_name)
elif is_out_lap:
    # 出站後一圈的損失
    out_lap_loss = self.params.get_out_lap_loss(track_name, compound)
```

**預期效果**:
- Undercut 視窗計算更精準
- 進站時機決策更真實
- 多次進站策略評估更準確

---

### 2️⃣ **輪胎溫度管理** (高優先)
**狀態**: ⚠️ 待實施  
**影響範圍**: Out-lap 性能、SC 重啟、紅旗重啟

#### 當前實施狀態
- ❌ 無輪胎溫度追蹤
- ❌ Out-lap 僅有固定損失，未考慮溫度爬升
- ❌ SC/VSC 後重啟未考慮輪胎冷卻

#### 真實情況分析
**輪胎溫度影響因素**:
1. **工作溫度範圍**:
   - SOFT: 85-95°C (最佳)
   - MEDIUM: 90-100°C
   - HARD: 95-105°C

2. **溫度爬升速度**:
   - 高速賽道: 1-2 圈達到工作溫度
   - 街道賽道: 2-3 圈達到工作溫度

3. **溫度冷卻速度**:
   - SC 巡航: 每圈降溫 5-10°C
   - VSC 巡航: 每圈降溫 3-5°C
   - Pit Stop: 完全冷卻 (回到環境溫度)

#### 實施計劃
**階段 1: 溫度狀態機**
```python
@dataclass
class TireTemperatureState:
    """輪胎溫度狀態"""
    compound: Compound
    current_temp: float  # 當前溫度 (°C)
    optimal_temp: float  # 最佳工作溫度
    age: int  # 輪胎圈齡
    
    def is_in_optimal_window(self) -> bool:
        """是否在最佳工作溫度範圍"""
        return abs(self.current_temp - self.optimal_temp) < 5.0
    
    def get_temp_penalty(self) -> float:
        """計算溫度不足的圈速損失"""
        if self.is_in_optimal_window():
            return 0.0
        
        # 溫度偏離最佳值的損失
        delta = abs(self.current_temp - self.optimal_temp)
        return min(2.0, 0.05 * delta)  # 最大 2 秒損失
```

**階段 2: 溫度演化模型**
```python
def update_tire_temp(
    self,
    current_temp: float,
    lap_type: str,  # "racing", "sc", "vsc", "pit"
    compound: Compound
) -> float:
    """更新輪胎溫度"""
    
    if lap_type == "racing":
        # 正常比賽：溫度上升
        target_temp = compound.optimal_temp
        heating_rate = 15.0  # 每圈升溫 15°C (高速賽道)
        new_temp = min(target_temp, current_temp + heating_rate)
    
    elif lap_type == "sc":
        # SC 巡航：溫度下降
        cooling_rate = 7.5  # 每圈降溫 7.5°C
        new_temp = max(50.0, current_temp - cooling_rate)
    
    elif lap_type == "pit":
        # 進站：完全冷卻
        new_temp = 25.0  # 環境溫度
    
    return new_temp
```

**階段 3: GUI 顯示**
- 在圈速圖表中顯示溫度狀態
- 標示「溫度不足」的圈數
- 顯示 Out-lap 溫度爬升過程

**預期效果**:
- Out-lap 損失更真實 (前 1-2 圈慢，之後恢復)
- SC/VSC 重啟後的速度更準確
- 紅旗重啟策略更精準

---

### 3️⃣ **DRS 影響** (中優先)
**狀態**: ⚠️ 待實施  
**影響範圍**: 超車能力、策略選擇

#### 當前實施狀態
- ❌ 無 DRS 效果模擬
- ❌ 無前後車差距追蹤

#### 真實情況分析
**DRS 效果**:
- 直線速度提升: 10-15 km/h
- 圈速增益: 0.3-0.5 秒/圈 (視賽道而定)
- 超車成功率: +30-50%

**DRS 啟用條件**:
- 與前車差距 < 1.0 秒 (在偵測點)
- 非前三圈
- 非濕地條件

#### 實施計劃
**階段 1: 差距追蹤**
```python
def calculate_gap_to_leader(
    self,
    current_pos: int,
    track_positions: Dict[str, float]
) -> float:
    """計算與前車的秒數差距"""
    if current_pos == 1:
        return 0.0
    
    # 找到前一位的車手
    ahead_driver = find_driver_at_position(current_pos - 1)
    ahead_track_pos = track_positions[ahead_driver]
    my_track_pos = track_positions[self.driver_code]
    
    # 差距 (秒) = 賽道位置差
    gap = ahead_track_pos - my_track_pos
    return max(0.0, gap)
```

**階段 2: DRS 效果模型**
```python
def apply_drs_effect(
    self,
    lap_time: float,
    gap_to_ahead: float,
    track_config: TrackConfig
) -> float:
    """應用 DRS 效果"""
    
    # 檢查 DRS 啟用條件
    if gap_to_ahead > 1.0:
        return lap_time  # 差距過大，無 DRS
    
    # DRS 增益 (視賽道而定)
    drs_zones = track_config.drs_zones  # 數量
    drs_gain_per_zone = 0.15  # 每個 DRS 區 0.15 秒
    total_gain = drs_zones * drs_gain_per_zone
    
    return lap_time - total_gain
```

**預期效果**:
- 後車追擊速度更真實
- Undercut 成功率計算更準確
- 防守策略選擇更合理

---

### 4️⃣ **Lapping (藍旗影響)** (中優先)
**狀態**: ⚠️ 待實施  
**影響範圍**: 領先圈車手的圈速損失

#### 當前實施狀態
- ❌ 無套圈車影響模擬

#### 真實情況分析
**套圈影響**:
- 每超越 1 台慢車: 0.2-0.5 秒損失
- 藍旗不配合: 額外 0.5-1.0 秒損失
- 平均每場比賽: 領先者套圈 3-5 次

#### 實施計劃
```python
def calculate_lapping_loss(
    self,
    lap_number: int,
    my_position: int,
    field_positions: List[DriverRaceState]
) -> float:
    """計算套圈造成的損失"""
    
    if my_position > 3:
        return 0.0  # 僅影響前三名
    
    # 找出落後 1 圈以上的車手
    lapped_cars = [d for d in field_positions 
                   if d.laps_behind >= 1 and d.in_my_path(my_position)]
    
    # 每台慢車造成 0.3 秒損失
    loss_per_car = 0.3
    return len(lapped_cars) * loss_per_car
```

---

## 🎯 數據來源增強

### 當前數據來源
- ✅ FP2 Long Run 數據 → 輪胎衰減率
- ✅ FP2→Q 預測 → 車手相對速度
- ✅ Track Features JSON → 賽道特性

### 待整合數據
1. **Live Timing 模組**:
   - In-lap / Out-lap 真實時間
   - SC/VSC 巡航速度
   - DRS 效果統計

2. **Corner Analysis**:
   - 彎角速度數據 → 輪胎溫度影響
   - 煞車點數據 → 煞車溫度管理

3. **Straight Line Speed**:
   - 最高速度 → DRS 效果模擬
   - 加速度 → Out-lap 性能

---

## 📊 效益評估

### 模擬精度提升預期
| 功能 | 當前精度 | 預期精度 | 影響範圍 |
|------|---------|---------|---------|
| 基礎策略比較 | 85% | 85% | 無變化 |
| Undercut 視窗 | 70% | 90% | +20% (In/Out-lap) |
| SC 進站決策 | 65% | 88% | +23% (溫度管理) |
| 後車追擊 | 60% | 85% | +25% (DRS + Traffic) |
| 套圈影響 | 50% | 75% | +25% (Lapping) |
| **整體平均** | **66%** | **85%** | **+19%** |

---

## 📅 實施時程

### Phase 1: 數據收集 (2 週)
- [ ] 建立 Live Timing In-lap/Out-lap 分析腳本
- [ ] 收集 2024-2025 年所有賽事數據
- [ ] 建立賽道分類資料庫

### Phase 2: 核心功能 (2 週)
- [ ] 實施 In-lap / Out-lap 損失模型
- [ ] 實施輪胎溫度狀態機
- [ ] 整合至現有 LapSimulator

### Phase 3: 進階功能 (2 週)
- [ ] 實施 DRS 效果模型
- [ ] 實施 Lapping 損失計算
- [ ] 完整測試與驗證

### Phase 4: GUI 整合 (1 週)
- [ ] 更新輸入面板
- [ ] 更新圖表顯示
- [ ] 更新說明文檔

**預計完成時間**: 7 週

---

## 🔬 驗證方法

### 真實賽事對比
- 選擇 5 場代表性賽事 (2024-2025)
- 輸入實際策略與參數
- 比較模擬結果與實際結果
- 計算誤差率

### 目標準確度
- 總時間誤差: < 5 秒
- 進站時機誤差: < 2 圈
- Undercut 成功率: > 85%

---

## 📝 文檔更新清單
- [ ] 更新 README.md
- [ ] 更新 API 文檔
- [ ] 新增範例腳本
- [ ] 建立使用者指南

---

**文檔版本**: 1.0  
**最後更新**: 2026-01-05  
**負責人**: F1T Development Team
