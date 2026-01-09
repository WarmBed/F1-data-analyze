"""
2025 Abu Dhabi GP - Complete Mode 模擬 vs 實際結果比較

生成報告：說明模擬與實際賽果的差異
"""

import sys
from pathlib import Path
import random

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from strategy_simulator.core.race_simulator import FullRaceSimulator
from strategy_simulator.core.lap_simulator import SimulationParams, Compound, Stint

# =====================================================
# 2025 Abu Dhabi GP 實際賽果 (從 FastF1 獲取)
# =====================================================
REAL_RESULTS = {
    'VER': {'pos': 1, 'grid': 1, 'gap': 0.0, 'team': 'Red Bull Racing', 'total_time': 5167.5},
    'PIA': {'pos': 2, 'grid': 3, 'gap': 12.594, 'team': 'McLaren', 'total_time': 5180.1},
    'NOR': {'pos': 3, 'grid': 2, 'gap': 16.572, 'team': 'McLaren', 'total_time': 5184.0},
    'LEC': {'pos': 4, 'grid': 5, 'gap': 23.279, 'team': 'Ferrari', 'total_time': 5190.7},
    'RUS': {'pos': 5, 'grid': 4, 'gap': 48.563, 'team': 'Mercedes', 'total_time': 5216.0},
    'ALO': {'pos': 6, 'grid': 6, 'gap': 67.562, 'team': 'Aston Martin', 'total_time': 5235.1},
    'OCO': {'pos': 7, 'grid': 8, 'gap': 69.876, 'team': 'Haas F1 Team', 'total_time': 5237.4},
    'HAM': {'pos': 8, 'grid': 16, 'gap': 72.670, 'team': 'Ferrari', 'total_time': 5240.1},
}

# 實際使用的策略 (簡化版)
REAL_STRATEGIES = {
    'VER': 'M-H-H',  # 3-stop
    'PIA': 'M-H-H',
    'NOR': 'M-H-H', 
    'LEC': 'M-H-H',
    'RUS': 'H-H-S',
    'ALO': 'M-H-H',
    'OCO': 'M-H',
    'HAM': 'M-H-H',
}

def main():
    print("=" * 90)
    print("2025 Abu Dhabi GP - Complete Mode 模擬 vs 實際結果比較報告")
    print("=" * 90)
    print("")
    
    # =====================================================
    # 設定模擬參數
    # =====================================================
    params = SimulationParams(
        race_laps=58,  # Abu Dhabi GP
        base_lap_time=88.5,  # 基於實際平均圈時
        fuel_kg_per_lap=1.70,
        fuel_effect_coefficient=0.030,
        pit_loss_green=22.0,
    )
    
    # 準備車手策略 (使用 Stint 對象)
    drivers_strategies = {}
    for driver in REAL_RESULTS.keys():
        strategy_str = REAL_STRATEGIES.get(driver, 'M-H')
        stints = []
        compounds_map = {'M': Compound.MEDIUM, 'H': Compound.HARD, 'S': Compound.SOFT}
        
        parts = strategy_str.split('-')
        
        # 計算每段的圈數
        if len(parts) == 3:
            stint_laps = [20, 20, 18]  # 3-stop
        elif len(parts) == 2:
            stint_laps = [25, 33]  # 1-stop
        else:
            stint_laps = [58]  # No stop
        
        current_lap = 1
        for i, compound_char in enumerate(parts):
            compound = compounds_map.get(compound_char, Compound.MEDIUM)
            laps = stint_laps[i] if i < len(stint_laps) else 15
            stints.append(Stint(compound=compound, laps=laps, start_lap=current_lap))
            current_lap += laps
        
        drivers_strategies[driver] = stints
    
    # 設定起跑排位
    grid_positions = {driver: data['grid'] for driver, data in REAL_RESULTS.items()}
    
    print("模擬設定:")
    print(f"  賽道: Abu Dhabi (Yas Marina)")
    print(f"  總圈數: {params.race_laps}")
    print(f"  基準圈時: {params.base_lap_time:.1f}s")
    print(f"  進站損失: {params.pit_loss_green:.1f}s")
    print(f"  車手數: {len(drivers_strategies)}")
    print("")
    
    # =====================================================
    # 執行 Complete Mode 模擬
    # =====================================================
    print("執行 Complete Mode 模擬...")
    print("")
    
    random.seed(2025)  # 固定種子以便重現
    
    simulator = FullRaceSimulator(
        sim_params=params,
        sc_probability=0.3,
        vsc_probability=0.2,
        overtaking_difficulty=0.65,
        simple_mode=False,  # Complete Mode
        track_name="Abu Dhabi",
        year=2025
    )
    
    # 準備 fp2_predictions 格式
    fp2_predictions = []
    for driver, data in REAL_RESULTS.items():
        # 模擬 FP2 預測數據
        fp2_predictions.append({
            'driver': driver,
            'rank': data['grid'],  # 使用 grid position 作為排名
            'predicted_time': 88.5 + (data['grid'] - 1) * 0.1,  # 基於排位估算圈時
            'team': data['team'],
        })
    
    # 載入車手 (使用 fp2_predictions 格式)
    simulator.load_drivers(fp2_predictions=fp2_predictions)
    
    # 手動設定策略
    for driver, data in REAL_RESULTS.items():
        stints = drivers_strategies[driver]
        if driver in simulator._drivers:
            simulator._strategies[driver] = stints
            simulator._drivers[driver].grid_position = data['grid']
    
    # 執行模擬
    result = simulator.simulate_race(seed=2025)
    
    # =====================================================
    # 比較結果
    # =====================================================
    print("")
    print("=" * 90)
    print("結果比較")
    print("=" * 90)
    print("")
    
    print(f"{'車手':^6} | {'實際排名':^8} | {'模擬排名':^8} | {'排名差':^6} | {'實際Gap':^12} | {'模擬Gap':^12} | {'Gap差異':^10}")
    print("-" * 90)
    
    sim_results = {s.driver_code: s for s in result.final_standings}
    
    position_errors = []
    gap_errors = []
    
    for driver, real_data in REAL_RESULTS.items():
        real_pos = real_data['pos']
        real_gap = real_data['gap']
        
        sim_standing = sim_results.get(driver)
        if sim_standing:
            sim_pos = sim_standing.final_position
            sim_gap = sim_standing.gap_to_winner
        else:
            sim_pos = 20
            sim_gap = 999.0
        
        pos_diff = sim_pos - real_pos
        gap_diff = sim_gap - real_gap
        
        position_errors.append(abs(pos_diff))
        gap_errors.append(abs(gap_diff))
        
        real_gap_str = "Winner" if real_pos == 1 else f"+{real_gap:.3f}s"
        sim_gap_str = "Winner" if sim_pos == 1 else f"+{sim_gap:.3f}s"
        pos_diff_str = "=" if pos_diff == 0 else f"{pos_diff:+d}"
        gap_diff_str = "-" if real_pos == 1 else f"{gap_diff:+.1f}s"
        
        print(f"  {driver:3s}   |    P{real_pos:<2d}    |    P{sim_pos:<2d}    |   {pos_diff_str:^3s}  | {real_gap_str:^12s} | {sim_gap_str:^12s} | {gap_diff_str:^10s}")
    
    print("-" * 90)
    print("")
    
    # =====================================================
    # 統計分析
    # =====================================================
    avg_pos_error = sum(position_errors) / len(position_errors)
    avg_gap_error = sum(gap_errors) / len(gap_errors)
    max_pos_error = max(position_errors)
    max_gap_error = max(gap_errors)
    
    print("=" * 90)
    print("統計分析")
    print("=" * 90)
    print("")
    print(f"排名誤差:")
    print(f"  平均: {avg_pos_error:.2f} 位")
    print(f"  最大: {max_pos_error} 位")
    print("")
    print(f"差距誤差:")
    print(f"  平均: {avg_gap_error:.1f}s")
    print(f"  最大: {max_gap_error:.1f}s")
    print("")
    
    # =====================================================
    # 差異分析
    # =====================================================
    print("=" * 90)
    print("差異分析")
    print("=" * 90)
    print("")
    
    # 分析原因
    print("可能的差異原因:")
    print("")
    print("1. 起跑順序變化")
    print("   - 實際: NOR (P2) 被 PIA (P3) 在起跑時超越")
    print("   - 模擬: 可能未完全反映起跑事件")
    print("")
    print("2. 進站策略時機")
    print("   - 實際進站圈數與模擬假設可能不同")
    print("   - SC/VSC 時機影響策略效果")
    print("")
    print("3. 車隊性能模型")
    print("   - Red Bull 在 Abu Dhabi 的實際優勢可能更大")
    print("   - McLaren 雙車接近但 PIA > NOR (策略差異)")
    print("")
    print("4. 超車難度")
    print("   - Abu Dhabi 有 DRS 區域，超車相對容易")
    print("   - HAM 從 P16 追到 P8 顯示超車可行性")
    print("")
    print("5. 輪胎衰退模型")
    print("   - 實際衰退可能與模型假設不同")
    print("   - 需要 Long Run 數據校準")
    print("")
    
    # =====================================================
    # 建議改進
    # =====================================================
    print("=" * 90)
    print("建議改進")
    print("=" * 90)
    print("")
    
    if avg_gap_error > 20:
        print("❌ Gap 誤差過大 (>20s):")
        print("   - 檢查 PositionTracker 的圈時計算")
        print("   - 校準車隊性能係數")
        print("   - 調整進站時間損失")
    elif avg_gap_error > 10:
        print("⚠️ Gap 誤差中等 (10-20s):")
        print("   - 使用實際 Long Run 數據校準")
        print("   - 調整輪胎衰退模型")
    else:
        print("✅ Gap 誤差在可接受範圍 (<10s)")
    
    print("")
    
    if avg_pos_error > 2:
        print("❌ 排名誤差過大 (>2位):")
        print("   - 檢查超車模型")
        print("   - 調整車隊相對性能")
    elif avg_pos_error > 1:
        print("⚠️ 排名誤差中等 (1-2位):")
        print("   - 微調超車難度係數")
    else:
        print("✅ 排名誤差在可接受範圍 (<1位)")
    
    print("")
    print("=" * 90)
    print("報告完成")
    print("=" * 90)
    
    return result

if __name__ == "__main__":
    main()
