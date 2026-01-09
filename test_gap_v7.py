"""測試 gap 計算 v7"""
import sys
sys.path.insert(0, '.')

from strategy_simulator.core.race_simulator import FullRaceSimulator
from strategy_simulator.core.lap_simulator import SimulationParams

print("=" * 60)
print("測試 Complete Mode Gap 計算 v7")
print("=" * 60)

# 創建模擬參數
sim_params = SimulationParams(
    race_laps=58,
    base_lap_time=85.0,
    pit_loss_green=24.0
)

# 創建模擬器
sim = FullRaceSimulator(
    sim_params=sim_params,
    track_name='Abu Dhabi',
    year=2025,
    simple_mode=False  # Complete mode
)

# 設置預設車手數據
fp2_predictions = [
    {'driver': 'NOR', 'team': 'McLaren', 'predicted_gap': 0.0, 'grid_position': 1},
    {'driver': 'VER', 'team': 'Red Bull', 'predicted_gap': 0.3, 'grid_position': 2},
    {'driver': 'LEC', 'team': 'Ferrari', 'predicted_gap': 0.5, 'grid_position': 3},
    {'driver': 'HAM', 'team': 'Mercedes', 'predicted_gap': 0.6, 'grid_position': 4},
    {'driver': 'SAI', 'team': 'Ferrari', 'predicted_gap': 0.7, 'grid_position': 5},
    {'driver': 'RUS', 'team': 'Mercedes', 'predicted_gap': 0.8, 'grid_position': 6},
    {'driver': 'PER', 'team': 'Red Bull', 'predicted_gap': 0.9, 'grid_position': 7},
    {'driver': 'PIA', 'team': 'McLaren', 'predicted_gap': 1.0, 'grid_position': 8},
    {'driver': 'ALO', 'team': 'Aston Martin', 'predicted_gap': 1.2, 'grid_position': 9},
    {'driver': 'GAS', 'team': 'Alpine', 'predicted_gap': 1.5, 'grid_position': 10},
    {'driver': 'STR', 'team': 'Aston Martin', 'predicted_gap': 1.6, 'grid_position': 11},
    {'driver': 'OCO', 'team': 'Alpine', 'predicted_gap': 1.7, 'grid_position': 12},
    {'driver': 'TSU', 'team': 'RB', 'predicted_gap': 1.8, 'grid_position': 13},
    {'driver': 'LAW', 'team': 'RB', 'predicted_gap': 1.9, 'grid_position': 14},
    {'driver': 'HUL', 'team': 'Haas', 'predicted_gap': 2.0, 'grid_position': 15},
    {'driver': 'MAG', 'team': 'Haas', 'predicted_gap': 2.1, 'grid_position': 16},
    {'driver': 'ZHO', 'team': 'Sauber', 'predicted_gap': 2.3, 'grid_position': 17},
    {'driver': 'BOT', 'team': 'Sauber', 'predicted_gap': 2.5, 'grid_position': 18},
    {'driver': 'ALB', 'team': 'Williams', 'predicted_gap': 2.6, 'grid_position': 19},
    {'driver': 'COL', 'team': 'Williams', 'predicted_gap': 2.7, 'grid_position': 20},
]

sim.load_drivers(fp2_predictions)

# 設置對手策略（簡單的 M-H）
opponent_strategies = {}
for driver in ['VER', 'LEC', 'HAM', 'SAI', 'RUS', 'PER', 'PIA', 'ALO', 'GAS', 'STR', 
               'OCO', 'TSU', 'LAW', 'HUL', 'MAG', 'ZHO', 'BOT', 'ALB', 'COL']:
    opponent_strategies[driver] = {'tire_sequence': ['M', 'H'], 'pit_laps': [30]}
sim.set_opponent_strategies(opponent_strategies)

# 不設置我們的策略 (使用默認)

# 執行模擬（使用固定種子確保結果一致）
print("\n執行模擬中...\n")
results = sim.simulate_race(seed=42)

print("\n" + "=" * 60)
print("最終結果 (前 10 名)")
print("=" * 60)

for r in results.final_standings[:10]:
    print(f"P{r.final_position:2d} {r.driver_code}: gap={r.gap_to_winner:+7.1f}s, total_time={r.total_time:.1f}s")

print("\n" + "=" * 60)
print("NOR vs VER 比較")
print("=" * 60)

nor_result = next((r for r in results.final_standings if r.driver_code == "NOR"), None)
ver_result = next((r for r in results.final_standings if r.driver_code == "VER"), None)

if nor_result and ver_result:
    print(f"NOR: P{nor_result.final_position}, total={nor_result.total_time:.1f}s, gap={nor_result.gap_to_winner:+.1f}s")
    print(f"VER: P{ver_result.final_position}, total={ver_result.total_time:.1f}s, gap={ver_result.gap_to_winner:+.1f}s")
    print(f"差距: {abs(ver_result.total_time - nor_result.total_time):.1f}s")
