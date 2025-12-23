"""
完整檢查 Lap 15-25 的輪胎數據（不跳過任何一圈）
"""
import pickle
from pathlib import Path

pkl_path = Path("data/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

# 獲取車號映射
driver_info = data.get('driver_info', {})
driver_stints = data.get('driver_stints', {})

tsu_number = None
nor_number = None
for number, info in driver_info.items():
    tla = info.get('driver_tla') or info.get('tla')
    if tla == 'TSU':
        tsu_number = number
    elif tla == 'NOR':
        nor_number = number

print(f"DEBUG: TSU 車號 = {tsu_number}, NOR 車號 = {nor_number}")

print("=" * 80)
print("🔍 TSU 和 NOR 的 Stint 結構")
print("=" * 80)

print(f"\nTSU (車號 {tsu_number}) Stints:")
tsu_stints = driver_stints.get(tsu_number, [])
tsu_lap_counter = 1
for i, stint in enumerate(tsu_stints, 1):
    total_laps = stint.get('total_laps', 0)
    compound = stint.get('compound', 'UNKNOWN')
    stint_end = tsu_lap_counter + total_laps - 1
    print(f"   Stint {i}: {compound}, Lap {tsu_lap_counter}-{stint_end} ({total_laps} 圈)")
    tsu_lap_counter += total_laps

print(f"\nNOR (車號 {nor_number}) Stints:")
nor_stints = driver_stints.get(nor_number, [])
nor_lap_counter = 1
for i, stint in enumerate(nor_stints, 1):
    total_laps = stint.get('total_laps', 0)
    compound = stint.get('compound', 'UNKNOWN')
    stint_end = nor_lap_counter + total_laps - 1
    print(f"   Stint {i}: {compound}, Lap {nor_lap_counter}-{stint_end} ({total_laps} 圈)")
    nor_lap_counter += total_laps

print("\n" + "=" * 80)
print("🔍 Lap 15-25 完整輪胎數據（每一圈）")
print("=" * 80)

snapshots = data.get('snapshots', [])

for target_lap in range(15, 26):
    for snapshot in snapshots:
        if snapshot.get('current_lap') == target_lap:
            drivers = snapshot.get('drivers', {})
            
            # 找到 TSU 和 NOR 的數據
            tsu_data = None
            nor_data = None
            
            for driver in drivers.values():
                tla = driver.get('driver_tla')
                if tla == 'TSU':
                    tsu_data = driver
                elif tla == 'NOR':
                    nor_data = driver
            
            if tsu_data and nor_data:
                # 計算輪胎 age（根據 stint 結構）
                def get_tyre_from_stint(lap_num, stints):
                    current_lap = 1
                    for stint in stints:
                        total_laps = stint.get('total_laps', 0)
                        stint_end = current_lap + total_laps - 1
                        
                        if current_lap <= lap_num <= stint_end:
                            compound = stint.get('compound', 'UNKNOWN')
                            age = lap_num - current_lap + 1
                            return compound, age
                        
                        current_lap += total_laps
                    return 'UNKNOWN', 0
                
                tsu_compound, tsu_age = get_tyre_from_stint(target_lap, tsu_stints)
                nor_compound, nor_age = get_tyre_from_stint(target_lap, nor_stints)
                
                tsu_pos = tsu_data.get('position')
                nor_pos = nor_data.get('position')
                tsu_gap = float(tsu_data.get('gap_to_leader', 0))
                nor_gap = float(nor_data.get('gap_to_leader', 0))
                
                # 計算相對 Gap
                gap = tsu_gap - nor_gap
                
                print(f"\nLap {target_lap}:")
                print(f"   TSU: P{tsu_pos}, {tsu_compound} age {tsu_age}, gap_to_leader={tsu_gap:.3f}s")
                print(f"   NOR: P{nor_pos}, {nor_compound} age {nor_age}, gap_to_leader={nor_gap:.3f}s")
                print(f"   Gap (TSU vs NOR): {gap:+.3f}s ({'TSU 落後' if gap > 0 else 'TSU 領先' if gap < 0 else '並列'})")
            
            break

print("\n" + "=" * 80)
print("💡 輪胎配方變化摘要")
print("=" * 80)
print("TSU:")
print("   Lap 1-32: HARD (age 1-32)")
print("   Lap 33-58: MEDIUM (age 1-26)")
print("\nNOR:")
print("   Lap 1-16: MEDIUM (age 1-16)")
print("   Lap 17-40: HARD (age 1-24)")
print("   Lap 41-58: HARD (age 1-18)")
