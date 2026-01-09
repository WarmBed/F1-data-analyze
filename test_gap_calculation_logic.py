"""
最小化測試：驗證 gap_to_leader 是否使用 total_time

不需要 Long Run 數據，只驗證計算邏輯是否正確
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from strategy_simulator.core.race_simulator import FullRaceSimulator, SimulationParams
from strategy_simulator.core.lap_simulator import Compound

def main():
    print("=" * 80)
    print("最小化測試：gap_to_leader 計算邏輯驗證")
    print("=" * 80)
    print("")
    
    # 簡單的模擬參數
    params = SimulationParams(
        race_laps=10,  # 短賽事
        base_lap_time=90.0,
        fuel_effect_coefficient=0.035,
        pit_loss_green=22.0
    )
    
    # 簡單的 2 車手策略
    drivers_strategies = {
        'VER': [
            {'compound': Compound.MEDIUM, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 5}  # Lap 5 進站
        ],
        'HAM': [
            {'compound': Compound.MEDIUM, 'target_lap': 0},
            {'compound': Compound.HARD, 'target_lap': 6}  # Lap 6 進站 (晚 1 圈)
        ],
    }
    
    grid_positions = {
        'VER': 1,
        'HAM': 2,
    }
    
    print("模擬設定:")
    print(f"  總圈數: {params.race_laps}")
    print(f"  基準圈時: {params.base_lap_time:.1f}s")
    print(f"  進站時間: {params.pit_loss_green:.1f}s")
    print("")
    print("策略:")
    print("  VER: MEDIUM (L1-4) → 進站 L5 → HARD (L6-10)")
    print("  HAM: MEDIUM (L1-5) → 進站 L6 → HARD (L7-10)")
    print("")
    
    print("執行模擬...")
    simulator = FullRaceSimulator(
        sim_params=params,
        drivers_strategies=drivers_strategies,
        grid_positions=grid_positions,
        use_position_tracker=False,  # Simple Mode
        longrun_data=None  # 不使用 Long Run 數據
    )
    
    result = simulator.run()
    
    print("")
    print("=" * 80)
    print("每圈狀態 (檢查 gap 計算)")
    print("=" * 80)
    print("")
    
    for lap_state in result.lap_states:
        print(f"Lap {lap_state.lap}:")
        
        # 排序車手
        sorted_drivers = sorted(lap_state.gaps.items(), key=lambda x: x[1])
        
        for driver, gap in sorted_drivers:
            if gap == 0.0:
                print(f"  P1 {driver:3s} - Leader (gap = 0.0s)")
            else:
                print(f"  P2 {driver:3s} - +{gap:.3f}s")
        
        # 顯示進站
        if lap_state.pit_stops:
            for pit in lap_state.pit_stops:
                print(f"    → {pit.driver_code} 進站 (新胎: {pit.new_compound})")
        
        print("")
    
    print("=" * 80)
    print("驗證結果:")
    print("=" * 80)
    print("")
    
    # 關鍵測試點：進站後的 gap
    lap_5_state = result.lap_states[4]  # L5 (VER 進站)
    lap_6_state = result.lap_states[5]  # L6 (HAM 進站)
    
    ham_gap_after_ver_pit = lap_5_state.gaps.get('HAM', 0.0)
    ver_gap_after_ham_pit = lap_6_state.gaps.get('VER', 0.0)
    
    print(f"關鍵檢查點:")
    print(f"  L5 後 (VER 進站): HAM 差距 = +{ham_gap_after_ver_pit:.3f}s")
    print(f"    預期: HAM 應該暫時領先 (VER 進站損失 ~22s)")
    print("")
    print(f"  L6 後 (HAM 進站): VER 差距 = +{ver_gap_after_ham_pit:.3f}s")
    print(f"    預期: VER 應該重新領先 (HAM 進站後)")
    print("")
    
    # 驗證邏輯
    if ham_gap_after_ver_pit < 0:  # HAM 領先，gap 為負
        print("✅ gap 計算邏輯正確: HAM 在 VER 進站後暫時領先 (負 gap)")
    else:
        print("❌ gap 計算錯誤: HAM 應該在 VER 進站後領先")
    
    if ver_gap_after_ham_pit >= 0:  # VER 領先或持平
        print("✅ gap 計算邏輯正確: VER 在 HAM 進站後重新領先")
    else:
        print("❌ gap 計算錯誤: VER 應該在 HAM 進站後領先")
    
    print("")
    print("=" * 80)

if __name__ == "__main__":
    main()
