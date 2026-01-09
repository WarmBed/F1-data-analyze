#!/usr/bin/env python3
"""
測試差距改進 - 驗證修正後的差距是否合理
"""

import sys
sys.path.insert(0, "c:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze")

from strategy_simulator.core.race_simulator import RaceSimulator, SimulationParams, DriverRaceState, Stint, Compound

def test_gap_improvements():
    """測試差距改進"""
    print("=" * 60)
    print("測試差距改進效果")
    print("=" * 60)
    
    # 創建模擬器
    params = SimulationParams(
        race_laps=50,
        base_lap_time=90.0,
        pit_loss_green=24.0,
        pit_loss_sc=10.0,
        fuel_effect_coefficient=0.03
    )
    
    simulator = RaceSimulator(params, simple_mode=True)
    
    # 創建測試車手（只用 5 個來測試）
    test_drivers = [
        ("VER", "Red Bull", 1, 88.0),
        ("LEC", "Ferrari", 5, 88.5),
        ("HAM", "Mercedes", 10, 89.5),
        ("ALO", "Aston Martin", 15, 90.5),
        ("BOT", "Sauber", 20, 92.0),
    ]
    
    for code, team, grid_pos, base_pace in test_drivers:
        state = DriverRaceState(
            driver_code=code,
            team=team,
            position=grid_pos,
            grid_position=grid_pos,
            base_pace=base_pace,
            degradation_per_lap=0.05,
            current_tire=Compound.MEDIUM,
        )
        
        # 設置策略（1 stop）
        state.stints = [
            Stint(compound=Compound.MEDIUM, laps=30, start_lap=1),
            Stint(compound=Compound.HARD, laps=20, start_lap=31),
        ]
        
        simulator._drivers[code] = state
        simulator._strategies[code] = state.stints
    
    simulator._our_driver = "VER"
    
    # 執行 3 次模擬，檢查差距
    print("\n執行 3 次模擬測試...")
    
    for run in range(1, 4):
        print(f"\n{'=' * 60}")
        print(f"Run {run}")
        print(f"{'=' * 60}")
        
        result = simulator.simulate_race(seed=None)  # 無 seed，完全隨機
        
        print(f"\n最終結果：")
        for standing in result.final_standings:
            gap_str = f"+{standing.gap_to_winner:.3f}s" if standing.gap_to_winner > 0 else "WINNER"
            print(f"  P{standing.final_position:2d} {standing.driver_code:3s} - {gap_str:15s} "
                  f"(grid: P{standing.grid_position}, gained: {standing.positions_gained:+d})")
        
        # 驗證差距合理性
        if len(result.final_standings) >= 2:
            winner = result.final_standings[0]
            last = result.final_standings[-1]
            
            print(f"\n✅ 關鍵指標：")
            print(f"   - Winner: {winner.driver_code}")
            print(f"   - Last: {last.driver_code} (+{last.gap_to_winner:.1f}s)")
            
            # 期望：P1 vs P5 應該至少差 10-20 秒
            expected_min_gap = 8.0
            expected_max_gap = 60.0
            
            if expected_min_gap <= last.gap_to_winner <= expected_max_gap:
                print(f"   ✅ 差距合理 ({last.gap_to_winner:.1f}s 在 {expected_min_gap}-{expected_max_gap}s 範圍內)")
            elif last.gap_to_winner < expected_min_gap:
                print(f"   ⚠️  差距過小 ({last.gap_to_winner:.1f}s < {expected_min_gap}s)")
            else:
                print(f"   ⚠️  差距過大 ({last.gap_to_winner:.1f}s > {expected_max_gap}s)")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_gap_improvements()
