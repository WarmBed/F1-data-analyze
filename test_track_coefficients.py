"""
測試賽道專屬 race_pace_delta 係數系統
"""
import sys
sys.path.insert(0, ".")

from strategy_simulator.core.race_simulator import FullRaceSimulator
from strategy_simulator.core.lap_simulator import SimulationParams

def test_track_coefficients():
    """測試不同賽道的係數差異"""
    
    # 基本參數
    sim_params = SimulationParams(
        race_laps=56,
        pit_loss_green=22.0,
        pit_loss_sc=15.0
    )
    
    # 測試不同賽道
    test_tracks = [
        ("Singapore", "街道賽道，低差距"),
        ("Monaco", "街道賽道，低差距"),
        ("Japan", "標準賽道"),
        ("Italy", "標準賽道"),
        ("Australia", "高變異賽道"),
        ("Mexico", "高變異賽道"),
        ("Unknown Track", "未知賽道，使用預設"),
    ]
    
    print("=" * 60)
    print("賽道專屬 race_pace_delta 係數測試")
    print("=" * 60)
    
    for track_name, description in test_tracks:
        print(f"\n--- {track_name} ({description}) ---")
        
        simulator = FullRaceSimulator(
            sim_params=sim_params,
            track_name=track_name
        )
        
        # 檢查係數
        coef = simulator._track_pace_coefficient
        print(f"  係數: {coef:.3f}")
        
        # 計算 P10 預期差距 (56 圈)
        p10_gap = coef * 10 * 56
        print(f"  P10 預期總差距: {p10_gap:.1f}s")
    
    print("\n" + "=" * 60)
    print("完成!")

if __name__ == "__main__":
    test_track_coefficients()
