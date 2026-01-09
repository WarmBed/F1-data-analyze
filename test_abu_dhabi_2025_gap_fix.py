"""
2025 Abu Dhabi GP 差距計算修正驗證
驗證 Simple Mode 的 gap_to_leader 是否正確使用 total_time

實際賽果 (2025-12-08):
1. VER - Winner
2. PIA - +12.594s
3. NOR - +16.572s
4. LEC - +23.279s
5. RUS - +48.563s
"""

import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from strategy_simulator.core.race_simulator import FullRaceSimulator, SimulationParams
from strategy_simulator.data.longrun_loader import LongRunLoader, LongRunData
from strategy_simulator.core.lap_simulator import Compound

def main():
    print("=" * 80)
    print("2025 Abu Dhabi GP - Simple Mode Gap 計算驗證")
    print("=" * 80)
    print("")
    
    # 實際賽果
    real_results = {
        'VER': {'position': 1, 'gap': 0.0},
        'PIA': {'position': 2, 'gap': 12.594},
        'NOR': {'position': 3, 'gap': 16.572},
        'LEC': {'position': 4, 'gap': 23.279},
        'RUS': {'position': 5, 'gap': 48.563},
    }
    
    print("實際賽果:")
    for driver, data in real_results.items():
        if data['position'] == 1:
            print(f"  P{data['position']} {driver:3s} - Winner")
        else:
            print(f"  P{data['position']} {driver:3s} - +{data['gap']:.2f}s")
    print("")
    
    # 載入 Long Run 數據
    print("載入 Long Run 數據...")
    
    loader = LongRunLoader()
    longrun_data = loader.load_fp2_data(2025, "Abu Dhabi")
    
    if not longrun_data:
        print("❌ 無法載入 Long Run 數據")
        return
    
    print(f"✅ Long Run 數據載入成功")
    print(f"   基準圈時: {longrun_data.base_lap_time:.3f}s")
    print(f"   燃油效應: {longrun_data.fuel_effect:.3f}")
    print(f"   賽道進化: {longrun_data.track_evolution:.3f}s/lap")
    print("")
    
    # 準備車手策略 (簡化版，假設 2-stop 策略)
    drivers_strategies = {
        'VER': [
            {'compound': Compound.MEDIUM, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 20},
            {'compound': Compound.HARD, 'target_lap': 40}
        ],
        'PIA': [
            {'compound': Compound.MEDIUM, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 18},
            {'compound': Compound.HARD, 'target_lap': 38}
        ],
        'NOR': [
            {'compound': Compound.MEDIUM, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 19},
            {'compound': Compound.HARD, 'target_lap': 39}
        ],
        'LEC': [
            {'compound': Compound.MEDIUM, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 21},
            {'compound': Compound.HARD, 'target_lap': 41}
        ],
        'RUS': [
            {'compound': Compound.HARD, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 22},
            {'compound': Compound.SOFT, 'target_lap': 44}
        ],
    }
    
    # 設定起跑排位 (使用實際 2025 Abu Dhabi 排位)
    grid_positions = {
        'VER': 1,  # 杆位
        'NOR': 2,
        'PIA': 3,
        'LEC': 4,
        'RUS': 5,
    }
    
    # 建立模擬參數
    params = SimulationParams(
        race_laps=58,  # Abu Dhabi GP
        base_lap_time=87.0,
        fuel_effect_coefficient=0.035,
        avg_pit_time=22.0,
        sc_probability=0.20,
        overtaking_difficulty=0.65,
        enable_reactive_strategy=True
    )
    
    print("執行 Simple Mode 模擬...")
    simulator = FullRaceSimulator(
        sim_params=params,
        drivers_strategies=drivers_strategies,
        grid_positions=grid_positions,
        use_position_tracker=False,  # Simple Mode
        longrun_data=longrun_data
    )
    
    result = simulator.run()
    
    print("")
    print("=" * 80)
    print("模擬結果:")
    print("=" * 80)
    print("")
    
    # 顯示模擬結果
    print(f"{'排名':^6} {'車手':^6} {'模擬 Gap':^12} {'實際 Gap':^12} {'差異':^12}")
    print("-" * 80)
    
    for standing in result.final_standings[:5]:
        driver = standing.driver_code
        sim_gap = standing.gap_to_leader
        
        if driver in real_results:
            real_gap = real_results[driver]['gap']
            diff = sim_gap - real_gap
            
            if standing.position == 1:
                print(f"  P{standing.position}    {driver:3s}     Winner       Winner         -")
            else:
                print(f"  P{standing.position}    {driver:3s}    +{sim_gap:6.2f}s     +{real_gap:6.2f}s     {diff:+6.2f}s")
        else:
            print(f"  P{standing.position}    {driver:3s}    +{sim_gap:6.2f}s     (未追蹤)        -")
    
    print("")
    print("=" * 80)
    print("驗證結果分析:")
    print("=" * 80)
    print("")
    
    # 計算平均誤差
    total_error = 0.0
    count = 0
    
    for standing in result.final_standings[:5]:
        driver = standing.driver_code
        if driver in real_results and standing.position > 1:
            sim_gap = standing.gap_to_leader
            real_gap = real_results[driver]['gap']
            total_error += abs(sim_gap - real_gap)
            count += 1
    
    if count > 0:
        avg_error = total_error / count
        print(f"平均誤差: {avg_error:.2f}s")
        
        if avg_error < 5.0:
            print("✅ 差距計算精度良好 (誤差 < 5s)")
        elif avg_error < 10.0:
            print("⚠️ 差距計算精度尚可 (誤差 5-10s)")
        else:
            print("❌ 差距計算需要改進 (誤差 > 10s)")
    
    print("")
    print("檢查 total_time 是否正確使用:")
    
    # 驗證 gap_to_leader 是否基於 total_time
    if result.lap_states:
        final_lap = result.lap_states[-1]
        print(f"  最後一圈 (Lap {final_lap.lap}) 差距:")
        
        for standing in result.final_standings[:5]:
            driver = standing.driver_code
            gap = final_lap.gaps.get(driver, 0.0)
            
            if standing.position == 1:
                print(f"    {driver:3s}: Leader (gap = 0.0s)")
            else:
                print(f"    {driver:3s}: +{gap:.3f}s (應為累積時間差)")
    
    print("")
    print("=" * 80)

if __name__ == "__main__":
    main()
