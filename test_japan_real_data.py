"""測試 Japan 真實數據的差距計算"""
import sys
sys.path.insert(0, '.')
import random
random.seed(42)
import json

from strategy_simulator.core.race_simulator import FullRaceSimulator
from strategy_simulator.core.lap_simulator import SimulationParams, Stint, Compound

# 使用真實 Japan 2025 數據
with open('json/fp2_qualifying_prediction_2025_Japan.json') as f:
    data = json.load(f)

predictions = data['predictions']  # 使用所有車手（20位）

print('=== 輸入數據 ===')
for p in predictions:
    print(f"{p['rank']:2d} | {p['driver']:5s} | predicted_time={p['predicted_time']:.3f}s")

sim_params = SimulationParams(race_laps=53, pit_loss_green=22.0, pit_loss_sc=15.0)

print('\n=== Japan Complete Mode (53圈, 禁用 SC) ===')
sim = FullRaceSimulator(
    sim_params=sim_params, 
    track_name='Japan', 
    simple_mode=False,
    sc_probability=0,  # 禁用 SC 便於觀察純差距
    vsc_probability=0
)

print('\n=== Japan Simple Mode (53圈) ===')
sim_simple = FullRaceSimulator(
    sim_params=sim_params, 
    track_name='Japan', 
    simple_mode=True,
    sc_probability=0,
    vsc_probability=0
)
sim.load_drivers(predictions)

# 手動設置策略
for p in predictions:
    code = p['driver']
    sim.set_our_strategy(code, [
        Stint(compound=Compound.MEDIUM, laps=20, start_lap=1),
        Stint(compound=Compound.HARD, laps=33, start_lap=21)
    ])

result = sim.simulate_race()

print(f'\n係數: {sim._track_pace_coefficient}')
print(f'\n=== Complete Mode 最終結果 ===')
for r in sorted(result.final_standings, key=lambda x: x.final_position):
    print(f'{r.driver_code}: P{r.final_position} (Grid P{r.grid_position}), Gap: +{r.gap_to_winner:.1f}s, Total: {r.total_time:.1f}s')

# 測試 Simple Mode
sim_simple.load_drivers(predictions)
for p in predictions:
    code = p['driver']
    sim_simple.set_our_strategy(code, [
        Stint(compound=Compound.MEDIUM, laps=20, start_lap=1),
        Stint(compound=Compound.HARD, laps=33, start_lap=21)
    ])
result_simple = sim_simple.simulate_race()

print(f'\n=== Simple Mode 最終結果 ===')
for r in sorted(result_simple.final_standings, key=lambda x: x.final_position):
    print(f'{r.driver_code}: P{r.final_position} (Grid P{r.grid_position}), Gap: +{r.gap_to_winner:.1f}s, Total: {r.total_time:.1f}s')

# 檢查各車手總時間
print('\n=== 各車手總時間檢查 ===')
standings_sorted = sorted(result.final_standings, key=lambda x: x.final_position)
winner_time = standings_sorted[0].total_time
for r in standings_sorted:
    diff = r.total_time - winner_time
    print(f'{r.driver_code}: total_time={r.total_time:.1f}s, gap_from_winner={diff:.1f}s, reported_gap={r.gap_to_winner:.1f}s')

# 計算理論差距
print('\n=== 理論差距分析 ===')
first = predictions[0]
for p in predictions:
    base_diff = p['predicted_time'] - first['predicted_time']
    rank_diff = (p['rank'] - first['rank']) * 0.10  # Japan 係數
    total_per_lap = base_diff + rank_diff
    total_53 = total_per_lap * 53
    print(f"{p['driver']}: predicted_time 差={base_diff:.3f}s, rank 差距={rank_diff:.2f}s/圈, 53圈理論={total_53:.1f}s")
