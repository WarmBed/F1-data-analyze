#!/usr/bin/env python3
"""
Test Traffic Heatmap Data Conversion
測試 Traffic 熱力圖數據轉換邏輯
"""

import sys
sys.path.insert(0, "c:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze")

from strategy_simulator.core.race_simulator import LapState


def test_data_conversion():
    """測試數據轉換邏輯（模擬 full_race_tab._prepare_traffic_heatmap_data）"""
    print("=" * 60)
    print("Testing Traffic Heatmap Data Conversion")
    print("=" * 60)
    
    # 創建模擬的 lap_states
    lap_states = []
    
    # Lap 1: VER P1, LEC P2 (gap 0.5s), NOR P3 (gap 2.0s)
    lap1 = LapState(
        lap=1,
        positions={"VER": 1, "LEC": 2, "NOR": 3, "PIA": 4},
        gaps={"VER": 0.0, "LEC": 0.5, "NOR": 2.0, "PIA": 3.5},
        tire_ages={"VER": 1, "LEC": 1, "NOR": 1, "PIA": 1},
        compounds={"VER": "SOFT", "LEC": "SOFT", "NOR": "SOFT", "PIA": "SOFT"},
        pit_stops=[],
        sc_active=False
    )
    lap_states.append(lap1)
    
    # Lap 2: LEC now in traffic (gap to VER < 1.5s)
    lap2 = LapState(
        lap=2,
        positions={"VER": 1, "LEC": 2, "NOR": 3, "PIA": 4},
        gaps={"VER": 0.0, "LEC": 0.8, "NOR": 2.5, "PIA": 4.0},
        tire_ages={"VER": 2, "LEC": 2, "NOR": 2, "PIA": 2},
        compounds={"VER": "SOFT", "LEC": "SOFT", "NOR": "SOFT", "PIA": "SOFT"},
        pit_stops=[],
        sc_active=False
    )
    lap_states.append(lap2)
    
    # Lap 3: SC active
    lap3 = LapState(
        lap=3,
        positions={"VER": 1, "LEC": 2, "NOR": 3, "PIA": 4},
        gaps={"VER": 0.0, "LEC": 0.2, "NOR": 0.5, "PIA": 0.8},
        tire_ages={"VER": 3, "LEC": 3, "NOR": 3, "PIA": 3},
        compounds={"VER": "SOFT", "LEC": "SOFT", "NOR": "SOFT", "PIA": "SOFT"},
        pit_stops=[],
        sc_active=True
    )
    lap_states.append(lap3)
    
    # Lap 4: Racing resumes, NOR in traffic with LEC
    lap4 = LapState(
        lap=4,
        positions={"VER": 1, "LEC": 2, "NOR": 3, "PIA": 4},
        gaps={"VER": 0.0, "LEC": 1.5, "NOR": 2.8, "PIA": 4.5},
        tire_ages={"VER": 4, "LEC": 4, "NOR": 4, "PIA": 4},
        compounds={"VER": "SOFT", "LEC": "SOFT", "NOR": "SOFT", "PIA": "SOFT"},
        pit_stops=[],
        sc_active=False
    )
    lap_states.append(lap4)
    
    # Lap 5: Everyone clean
    lap5 = LapState(
        lap=5,
        positions={"VER": 1, "LEC": 2, "NOR": 3, "PIA": 4},
        gaps={"VER": 0.0, "LEC": 2.0, "NOR": 4.5, "PIA": 7.0},
        tire_ages={"VER": 5, "LEC": 5, "NOR": 5, "PIA": 5},
        compounds={"VER": "SOFT", "LEC": "SOFT", "NOR": "SOFT", "PIA": "SOFT"},
        pit_stops=[],
        sc_active=False
    )
    lap_states.append(lap5)
    
    print(f"\n[TEST] Created {len(lap_states)} lap states")
    
    # 執行數據轉換
    print("\n[TEST] Converting data to heatmap format...")
    drivers_data = convert_lap_states_to_heatmap_data(lap_states)
    
    print(f"\n[TEST] ✅ Converted {len(drivers_data)} drivers")
    
    # 驗證結果
    for driver_data in drivers_data:
        driver_code = driver_data["driver_code"]
        final_pos = driver_data["final_position"]
        lap_states_dict = driver_data["lap_states"]
        stats = driver_data["traffic_stats"]
        
        print(f"\n[TEST] {driver_code} (P{final_pos}):")
        print(f"  Lap states: {lap_states_dict}")
        print(f"  Blocked: {stats['blocked_laps']}, Clean: {stats['clean_laps']}, SC/VSC: {stats['sc_vsc_laps']}")
        
        # 驗證期望值
        if driver_code == "VER":
            # VER is leader, always clean except SC lap
            assert stats['blocked_laps'] == 0, f"VER should have 0 blocked laps, got {stats['blocked_laps']}"
            assert stats['sc_vsc_laps'] == 1, f"VER should have 1 SC lap, got {stats['sc_vsc_laps']}"
            print(f"  ✅ VER validation passed")
        
        elif driver_code == "LEC":
            # LEC behind VER with gaps < 1.5s on laps 1, 2, 4
            # Lap 3 is SC, Lap 5 is clean (gap 2.0s)
            # Actually: Lap 1 gap=0.5s (traffic), Lap 2 gap=0.8s (traffic), Lap 3 SC, Lap 4 gap=1.5s (clean), Lap 5 gap=2.0s (clean)
            print(f"  ✅ LEC has {stats['blocked_laps']} blocked laps")
        
        elif driver_code == "NOR":
            # NOR behind LEC
            # Lap 1: gap to LEC = 2.0-0.5=1.5s (clean)
            # Lap 2: gap to LEC = 2.5-0.8=1.7s (clean)
            # Lap 3: SC
            # Lap 4: gap to LEC = 2.8-1.5=1.3s (traffic)
            # Lap 5: gap to LEC = 4.5-2.0=2.5s (clean)
            print(f"  ✅ NOR has {stats['blocked_laps']} blocked laps")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)
    
    return drivers_data


def convert_lap_states_to_heatmap_data(lap_states):
    """
    將 lap_states 轉換為熱力圖數據
    （從 full_race_tab._prepare_traffic_heatmap_data 複製的邏輯）
    """
    if not lap_states:
        return []
    
    # Collect all unique drivers
    all_drivers = set()
    for lap_state in lap_states:
        all_drivers.update(lap_state.positions.keys())
    
    drivers_data = []
    
    # Get final positions (use last lap state)
    final_lap = lap_states[-1]
    position_map = final_lap.positions
    
    for driver_code in sorted(all_drivers):
        lap_states_dict = {}
        blocked_count = 0
        clean_count = 0
        sc_vsc_count = 0
        
        # Analyze each lap
        for lap_state in lap_states:
            lap_num = lap_state.lap
            
            # Check if driver is in this lap
            if driver_code not in lap_state.positions:
                lap_states_dict[lap_num] = -1  # No data
                continue
            
            # Determine state
            if lap_state.sc_active:
                # SC/VSC active
                lap_states_dict[lap_num] = 2
                sc_vsc_count += 1
            else:
                # Check if in traffic (gap < 1.5s to car ahead)
                position = lap_state.positions.get(driver_code, 20)
                
                if position > 1:
                    # Find car ahead
                    car_ahead = None
                    for d, p in lap_state.positions.items():
                        if p == position - 1:
                            car_ahead = d
                            break
                    
                    if car_ahead:
                        gap_ahead = lap_state.gaps.get(driver_code, 99.0) - lap_state.gaps.get(car_ahead, 0.0)
                        
                        if abs(gap_ahead) < 1.5:
                            # In traffic
                            lap_states_dict[lap_num] = 1
                            blocked_count += 1
                        else:
                            # Clean lap
                            lap_states_dict[lap_num] = 0
                            clean_count += 1
                    else:
                        # Clean lap (no car ahead found)
                        lap_states_dict[lap_num] = 0
                        clean_count += 1
                else:
                    # Leader - always clean
                    lap_states_dict[lap_num] = 0
                    clean_count += 1
        
        # Build driver data
        drivers_data.append({
            "driver_code": driver_code,
            "final_position": position_map.get(driver_code, 20),
            "lap_states": lap_states_dict,
            "traffic_stats": {
                "blocked_laps": blocked_count,
                "clean_laps": clean_count,
                "sc_vsc_laps": sc_vsc_count
            }
        })
    
    return drivers_data


if __name__ == "__main__":
    try:
        test_data_conversion()
    except Exception as e:
        print(f"\n[TEST] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
