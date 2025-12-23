"""
快速比較: F92 vs 二次方程 - Japan 2025
"""
import sys
import fastf1
import numpy as np

sys.path.insert(0, 'CLI_modules/cli/prediction')
sys.path.insert(0, 'CLI_modules/cli/strategy')
from f92_hybrid_predictor import F92HybridPredictor
from driver_strategy import DriverStrategy
from smart_base_time_extractor import extract_base_time_robust

fastf1.Cache.enable_cache('f1_analysis_cache/')

print("="*80)
print("Japan 2025 VER - F92 vs 二次方程")
print("="*80)

# 提取 base_time
base_time, info = extract_base_time_robust(2025, "Japan", "VER")
skip_laps = info.get('sc_laps', [])
stints = [(1, 21, "MEDIUM"), (22, 53, "HARD")]

print(f"\nBase Time: {base_time:.3f}s")
print(f"SC Laps: {skip_laps}")

# F92 預測
print("\n" + "-"*80)
print("F92 混合模型")
print("-"*80)
f92 = F92HybridPredictor()
f92_result = f92.predict(
    year=2025, race="Japan", driver="VER",
    base_time=base_time,
    stints=stints,
    skip_laps=skip_laps,
    use_ml=True
)

if f92_result:
    f92_mae = f92_result.get('mae', 0)
    f92_bias = f92_result.get('mean_error', 0)
    print(f"F92 MAE:  {f92_mae:.3f}s")
    print(f"F92 Bias: {f92_bias:+.3f}s")
else:
    print("❌ F92 失敗")
    f92_mae = 999
    f92_bias = 0

# 二次方程預測
print("\n" + "-"*80)
print("二次方程模型")
print("-"*80)

session = fastf1.get_session(2025, "Japan", 'R')
session.load()
driver_laps = session.laps.pick_driver("VER")
driver_laps = driver_laps[driver_laps['LapTime'].notna()]
driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()

strategy = DriverStrategy()
errors = []

for lap in range(3, 54):
    if lap in skip_laps:
        continue
    
    # 找當前 stint
    if 1 <= lap <= 21:
        tyre_age = lap
        compound = "MEDIUM"
    elif 22 <= lap <= 53:
        tyre_age = lap - 21
        compound = "HARD"
    else:
        continue
    
    # 二次方程降解
    degradation = strategy.calculate_tire_degradation(
        circuit_name="Suzuka",
        compound=compound,
        tyre_age=tyre_age
    )
    
    predicted_time = base_time + degradation
    
    # 實際圈速
    actual_lap = driver_laps[driver_laps['LapNumber'] == lap]
    if actual_lap.empty:
        continue
    
    actual_time = actual_lap['LapTimeSeconds'].iloc[0]
    
    if actual_time > 120:
        continue
    
    error = predicted_time - actual_time
    errors.append(error)

quad_mae = np.mean([abs(e) for e in errors])
quad_bias = np.mean(errors)

print(f"二次方程 MAE:  {quad_mae:.3f}s")
print(f"二次方程 Bias: {quad_bias:+.3f}s")

# 比較
print("\n" + "="*80)
print("比較結果")
print("="*80)
print(f"F92 MAE:      {f92_mae:.3f}s")
print(f"二次方程 MAE: {quad_mae:.3f}s")
print(f"差距:         {f92_mae - quad_mae:+.3f}s")

if f92_mae < quad_mae:
    advantage = ((quad_mae - f92_mae) / quad_mae) * 100
    print(f"\n✅ F92 勝出！優勢 {advantage:.1f}%")
elif quad_mae < f92_mae:
    advantage = ((f92_mae - quad_mae) / f92_mae) * 100
    print(f"\n✅ 二次方程勝出！優勢 {advantage:.1f}%")
else:
    print(f"\n⚖️ 平手")

print("="*80)
