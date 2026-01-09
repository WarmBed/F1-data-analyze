#!/usr/bin/env python3
"""
測試 Traffic Analysis 修復
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from strategy_simulator.core.race_simulator import RaceSimulator, SimulationParams

# 創建測試參數
params = SimulationParams(
    race_laps=58,
    base_lap_time=90.0,
    total_drivers=20,
    deg_soft=0.080,
    deg_medium=0.065,
    deg_hard=0.050,
    tire_delta_soft=0.0,
    tire_delta_medium=0.5,
    tire_delta_hard=1.0,
    pit_loss=22.0,
    fuel_effect=0.030,
    track_evolution=0.00,
    sc_probability=0.3
)

# 創建模擬器
simulator = RaceSimulator(params, simple_mode=True)

# 設置我們的車手和策略
simulator.set_our_driver_strategy(
    driver_code="NOR",
    strategy=[("MEDIUM", 30), ("HARD", 28)]
)

print("[TEST] 開始模擬...")
result = simulator.simulate_race(seed=42)

print(f"\n[TEST] 模擬完成!")
print(f"[TEST] Total pit stops: {result.total_pit_stops}")
print(f"[TEST] SC events: {len(result.sc_events)}")
print(f"[TEST] Lap states: {len(result.lap_states)}")
print(f"[TEST] Traffic data type: {type(result.traffic_data)}")

if result.traffic_data:
    print(f"[TEST] Traffic data keys: {list(result.traffic_data.keys())[:5]}...")
    
    # 檢查第一個車手的數據
    first_driver = list(result.traffic_data.keys())[0]
    first_data = result.traffic_data[first_driver]
    print(f"\n[TEST] {first_driver} traffic data:")
    print(f"  - total_blocked_laps: {first_data.get('total_blocked_laps', 'N/A')}")
    print(f"  - clean_laps: {first_data.get('clean_laps', 'N/A')}")
    print(f"  - sc_vsc_laps: {first_data.get('sc_vsc_laps', 'N/A')}")
    print(f"  - lap_details count: {len(first_data.get('lap_details', {}))}")
    
    print(f"\n[TEST] ✅ Traffic Analysis 正常運作！")
else:
    print(f"\n[TEST] ❌ Traffic data 為空！")
