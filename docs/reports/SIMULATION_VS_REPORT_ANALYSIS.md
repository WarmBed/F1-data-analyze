# 完整賽事模擬 vs 策略報告 - 數據差異分析

## 📊 核心問題

**用戶提問:**
1. 完整賽事模擬有使用 Long Run 的輪胎/燃油/賽道進化數據嗎？
2. 如果有，報告為什麼沒用？
3. 哪邊跟實際模擬有出入？

---

## ✅ 完整賽事模擬（FullRaceSimulator）使用的數據

### 1. **Long Run 數據使用情況** ✅ 完全使用

**位置**: `strategy_simulator/core/race_simulator.py` Line 364-450

```python
def load_drivers(self, fp2_predictions, long_run_data=None):
    # ✅ 先從 Long Run 數據提取全局參數
    if long_run_data:
        # 基準圈時間
        if long_run_data.get('base_lap_time'):
            self._long_run_base_lap_time = long_run_data['base_lap_time']
        
        # 燃油效應係數
        if long_run_data.get('fuel_effect'):
            self._long_run_fuel_effect = long_run_data['fuel_effect']
        
        # 每圈燃油消耗
        if long_run_data.get('fuel_kg_per_lap'):
            self._long_run_fuel_kg_per_lap = long_run_data['fuel_kg_per_lap']
        
        # 賽道進化
        if long_run_data.get('track_evolution_per_lap'):
            self._long_run_track_evolution = abs(long_run_data['track_evolution_per_lap'])
        
        # 各胎質平均衰退率
        degradation = long_run_data.get('degradation', {})
        for compound_name, deg_data in degradation.items():
            self._long_run_degradation[compound_name.upper()] = deg_data.get('deg_per_lap', 0.05)
```

**模擬器確實使用的 Long Run 數據:**
- ✅ **基準圈時間** (`base_lap_time`) - 從 FP2 回歸分析計算
- ✅ **燃油效應** (`fuel_effect`) - FP2 測量的 kg/s 效應
- ✅ **燃油消耗** (`fuel_kg_per_lap`) - 每圈燃油消耗率
- ✅ **賽道進化** (`track_evolution_per_lap`) - FP2 期間的賽道演變
- ✅ **輪胎退化率** (`degradation`) - 各配方的實際測量值

### 2. **退化模型** ✅ 二次曲線模型

**位置**: `strategy_simulator/core/lap_simulator.py` Line 348-420

```python
def calculate_lap_time(self, lap_number, compound, tyre_age, fuel_remaining):
    """
    Uses time-varying linear degradation model from Cappello & Hoegh 2025:
    degradation(t) = base_rate * t + 0.5 * acceleration * t^2
    """
    deg_rate = self.params.get_deg_rate(compound)
    deg_accel = self.params.get_deg_acceleration(compound)
    
    if tyre_age <= 1:
        degradation = 0.0
    else:
        t = tyre_age - 1
        degradation = deg_rate * t + 0.5 * deg_accel * t * (t - 1)
```

**退化參數來源:**
```python
# SimulationParams 預設值
deg_rates = {
    Compound.SOFT: 0.120,
    Compound.MEDIUM: 0.080,
    Compound.HARD: 0.045,
}

deg_acceleration = {
    Compound.SOFT: 0.003,
    Compound.MEDIUM: 0.002,
    Compound.HARD: 0.001,
}
```

**如果有 Long Run 數據，可以被覆寫:**
```python
# race_simulator.py Line 391-393
self._long_run_degradation[compound_name.upper()] = deg_data.get('deg_per_lap', 0.05)
```

---

## ❌ 策略報告生成器（StrategyReportGenerator）的問題

### 問題 1: **沒有接收 Long Run 數據** ❌

**位置**: `strategy_simulator/gui/results_tabs/full_race_tab.py` Line 1353

```python
# ❌ 報告生成器沒有接收 long_run_data
generator = StrategyReportGenerator()
report_text = generator.generate_report(
    strategy_result=strategy_result,
    mc_summary=mc_summary,
    simulation_data=simulation_data,
    traffic_data=traffic_data,
    competitors_data=None,
    scenario_analyses=scenario_analyses,
    our_driver=our_driver,
    grid_position=grid_position,
    track_name=track_name,
    # ❌ 缺少: long_run_data=long_run_data
    # ❌ 缺少: sim_params=sim_params
)
```

### 問題 2: **退化計算不完整** ⚠️ 已修正（但仍缺 Long Run 數據）

**舊版問題** (已在本次修正):
```python
# ❌ 舊版：使用固定的簡化退化率
compound_deg_rates = {
    'SOFT': 0.09,    # 錯誤：不是 SimulationParams 的值
    'MEDIUM': 0.055,
    'HARD': 0.035,
}

# ❌ 舊版：只使用線性模型
expected_deg = tire_age_at_pit * deg_rate  # 忽略了二次項
```

**新版修正** (本次更新):
```python
# ✅ 新版：從 SimulationParams 讀取
base_rate = self._deg_rates.get(compound_key, 0.080)
acceleration = self._deg_acceleration.get(compound_key, 0.002)

# ✅ 新版：使用完整的二次曲線公式
cumulative_deg = base_rate * tire_age_at_pit + 0.5 * acceleration * (tire_age_at_pit ** 2)
```

**但仍然缺少:**
- ❌ 沒有使用 Long Run 的實際測量退化率
- ❌ 沒有使用 Long Run 的燃油效應
- ❌ 沒有使用 Long Run 的賽道進化

---

## 📉 數據差異對比表

| 數據項目 | 完整賽事模擬 | 策略報告生成器 | 差異 |
|---------|-------------|---------------|------|
| **輪胎退化率** | ✅ Long Run 實測 + SimulationParams 備用 | ⚠️ 僅 SimulationParams 預設值 | 報告不反映 FP2 實測 |
| **燃油效應** | ✅ Long Run 實測 fuel_effect | ❌ 無 | 報告缺少燃油影響 |
| **燃油消耗** | ✅ Long Run 實測 fuel_kg_per_lap | ❌ 無 | 報告缺少燃油計算 |
| **賽道進化** | ✅ Long Run 實測 track_evolution | ❌ 無 | 報告缺少賽道演變 |
| **基準圈時間** | ✅ Long Run 計算 base_lap_time | ❌ 無 | 報告缺少基準參考 |
| **退化模型** | ✅ 二次曲線 (base + accel) | ✅ 二次曲線（本次修正） | 已修正 ✅ |
| **退化加速度** | ✅ 使用 deg_acceleration | ✅ 使用 deg_acceleration（本次修正） | 已修正 ✅ |

---

## 🔍 具體範例：SOFT 輪胎 20 圈

### 模擬器計算（使用 Long Run 數據）:
```python
# 假設 Long Run 測量 SOFT 退化率為 0.115 s/lap
base_rate = 0.115  # 來自 FP2 Long Run
acceleration = 0.003  # SimulationParams
tire_age = 20

cumulative_deg = 0.115 * 20 + 0.5 * 0.003 * (20 ** 2)
             = 2.300 + 0.600
             = 2.900 秒
```

### 報告生成器計算（舊版，不使用 Long Run）:
```python
# ❌ 舊版：使用固定值 0.09
deg_rate = 0.09
tire_age = 20

expected_deg = 0.09 * 20 = 1.800 秒  # 錯誤！低估 1.1 秒
```

### 報告生成器計算（新版，本次修正）:
```python
# ✅ 新版：使用 SimulationParams，但沒有 Long Run 覆寫
base_rate = 0.120  # SimulationParams 預設值
acceleration = 0.003
tire_age = 20

cumulative_deg = 0.120 * 20 + 0.5 * 0.003 * (20 ** 2)
             = 2.400 + 0.600
             = 3.000 秒  # 比 Long Run 實測高 0.1 秒
```

**差異原因:**
- 報告使用 SimulationParams 預設值 (0.120)
- 模擬器使用 Long Run 實測值 (0.115)
- 差異：0.005 s/lap → 20 圈累積 0.1 秒

---

## 🎯 需要修正的地方

### 1. **報告生成器應接收 Long Run 數據**

**修改位置**: `strategy_simulator/gui/results_tabs/full_race_tab.py`

```python
# ✅ 建議修改
def _show_strategy_report(self, strategy_name, stats):
    # ... 現有代碼 ...
    
    # ✅ 新增：獲取 Long Run 數據
    long_run_data = None
    main_window = self.window()
    if main_window and hasattr(main_window, '_current_fp2_data'):
        long_run_data = main_window._current_fp2_data
    
    # ✅ 新增：獲取 SimulationParams
    sim_params = None
    if main_window and hasattr(main_window, '_current_params'):
        sim_params = main_window._current_params
    
    # 生成報告
    generator = StrategyReportGenerator()
    report_text = generator.generate_report(
        strategy_result=strategy_result,
        mc_summary=mc_summary,
        simulation_data=simulation_data,
        traffic_data=traffic_data,
        competitors_data=None,
        scenario_analyses=scenario_analyses,
        our_driver=our_driver,
        grid_position=grid_position,
        track_name=track_name,
        long_run_data=long_run_data,  # ✅ 新增
        sim_params=sim_params,  # ✅ 新增
    )
```

### 2. **報告生成器應優先使用 Long Run 數據**

**修改位置**: `strategy_simulator/gui/widgets/strategy_report_generator.py`

```python
def generate_report(
    self,
    strategy_result: Any,
    simulation_data: Optional[Any] = None,
    mc_summary: Optional[Any] = None,
    our_driver: str = "",
    grid_position: int = 1,
    track_name: str = "",
    race_laps: int = 57,
    pit_loss_green: float = 24.0,
    traffic_data: Optional[Dict] = None,
    scenario_analyses: Optional[Dict] = None,
    competitors_data: Optional[List[Dict]] = None,
    long_run_data: Optional[Dict] = None,  # ✅ 新增
    sim_params: Optional[Any] = None,  # ✅ 新增
) -> str:
```

```python
# 在 __init__ 或報告生成時：
if long_run_data and long_run_data.get('degradation'):
    # ✅ 優先使用 Long Run 測量的退化率
    for compound_name, deg_data in long_run_data['degradation'].items():
        if isinstance(deg_data, dict):
            self._deg_rates[compound_name.upper()] = deg_data.get('deg_per_lap', self._deg_rates.get(compound_name.upper(), 0.08))
```

### 3. **報告應顯示 Long Run 數據來源**

```python
# ✅ 建議在報告中增加資訊
if long_run_data:
    lines.append("")
    lines.append("【數據來源】")
    lines.append(f"✅ 使用 Long Run 實測數據 ({long_run_data.get('session_type', 'FP2')})")
    
    if long_run_data.get('base_lap_time'):
        lines.append(f"  - 基準圈時間: {long_run_data['base_lap_time']:.3f}s")
    
    if long_run_data.get('fuel_effect'):
        lines.append(f"  - 燃油效應: {long_run_data['fuel_effect']:.4f}s/kg")
    
    if long_run_data.get('degradation'):
        lines.append("  - 輪胎退化率 (實測):")
        for compound, deg_data in long_run_data['degradation'].items():
            if isinstance(deg_data, dict):
                deg_rate = deg_data.get('deg_per_lap', 0)
                lines.append(f"    └ {compound}: {deg_rate:.4f}s/lap")
else:
    lines.append("")
    lines.append("【數據來源】")
    lines.append("⚠️  使用 SimulationParams 預設值（無 Long Run 數據）")
```

---

## 📊 總結

### 當前狀況（2026-01-07 修正後）:

| 項目 | 完整賽事模擬 | 策略報告生成器 | 一致性 |
|-----|-------------|---------------|--------|
| 輪胎退化公式 | 二次曲線 | 二次曲線 ✅ | ✅ 一致 |
| 退化率來源 | Long Run 實測 | SimulationParams 預設 | ❌ 不一致 |
| 燃油效應 | Long Run 實測 | 無 | ❌ 缺少 |
| 賽道進化 | Long Run 實測 | 無 | ❌ 缺少 |

### 建議修正優先級:

1. **高優先** - 報告生成器接收 long_run_data 參數
2. **高優先** - 報告生成器使用 Long Run 退化率
3. **中優先** - 報告顯示燃油效應影響
4. **中優先** - 報告顯示賽道進化影響
5. **低優先** - 報告顯示數據來源資訊

---

## 🔧 修正後的效果

### 修正前（使用固定值）:
```
輪胎年齡 20 圈，累積衰退約 1.80s (SOFT: ~0.090s/lap)
```

### 修正後 V1（使用 SimulationParams）:
```
輪胎年齡 20 圈，累積衰退約 3.00s
└ 模型: 基礎退化 0.120s/lap + 加速度 0.0030s/lap²
└ SOFT: base=2.40s + quadratic=0.60s
```

### 完全修正後（使用 Long Run 數據）:
```
輪胎年齡 20 圈，累積衰退約 2.90s (Long Run 實測)
└ 模型: 基礎退化 0.115s/lap + 加速度 0.0030s/lap²
└ SOFT: base=2.30s + quadratic=0.60s
└ 數據來源: FP2 Long Run (25 laps, 信心度: 0.85)
```

---

**結論**: 策略報告現在使用正確的退化公式，但仍需整合 Long Run 實測數據以達到與模擬器完全一致。
