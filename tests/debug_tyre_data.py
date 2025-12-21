"""
檢查 pkl 檔案中的輪胎數據結構
"""
import pickle
from pathlib import Path

pkl_path = Path("data/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

print("=" * 80)
print("🔍 PKL 檔案結構檢查")
print("=" * 80)
print(f"Top-level keys: {list(data.keys())}\n")

# 檢查 driver_stints 結構
if 'driver_stints' in data:
    print("✅ 找到 'driver_stints' 鍵")
    driver_stints = data['driver_stints']
    print(f"   Type: {type(driver_stints)}")
    
    if isinstance(driver_stints, dict):
        print(f"   包含 {len(driver_stints)} 位車手")
        
        # 檢查 TSU 和 NOR
        for driver_tla in ['TSU', 'NOR']:
            if driver_tla in driver_stints:
                print(f"\n   {driver_tla} stints:")
                stints = driver_stints[driver_tla]
                print(f"      Type: {type(stints)}")
                print(f"      數量: {len(stints)}")
                
                if stints:
                    print(f"      範例 (第一個 stint):")
                    first_stint = stints[0]
                    for key, value in first_stint.items():
                        print(f"         {key}: {value}")
            else:
                print(f"\n   ❌ {driver_tla} 不在 driver_stints 中")
    else:
        print(f"   ⚠️  driver_stints 不是 dict，而是 {type(driver_stints)}")
else:
    print("❌ 找不到 'driver_stints' 鍵")

# 檢查 snapshots 中的輪胎數據
print("\n" + "=" * 80)
print("🔍 Snapshots 中的輪胎數據 (Lap 16)")
print("=" * 80)

snapshots = data.get('snapshots', [])
for snapshot in snapshots:
    if snapshot.get('current_lap') == 16:
        drivers = snapshot.get('drivers', {})
        
        for driver_tla in ['TSU', 'NOR']:
            for driver_data in drivers.values():
                if driver_data.get('driver_tla') == driver_tla:
                    print(f"\n{driver_tla} (Lap 16):")
                    print(f"   position: {driver_data.get('position')}")
                    print(f"   compound: {driver_data.get('compound')}")
                    print(f"   tyre_age: {driver_data.get('tyre_age')}")
                    print(f"   gap_to_leader: {driver_data.get('gap_to_leader')}")
                    break
        break

# 檢查 Lap 15-20 的輪胎變化
print("\n" + "=" * 80)
print("🔍 Lap 15-20 輪胎變化追蹤")
print("=" * 80)

for target_lap in range(15, 21):
    for snapshot in snapshots:
        if snapshot.get('current_lap') == target_lap:
            drivers = snapshot.get('drivers', {})
            
            print(f"\nLap {target_lap}:")
            for driver_tla in ['TSU', 'NOR']:
                for driver_data in drivers.values():
                    if driver_data.get('driver_tla') == driver_tla:
                        compound = driver_data.get('compound')
                        age = driver_data.get('tyre_age')
                        pos = driver_data.get('position')
                        print(f"   {driver_tla}: P{pos}, {compound} age {age}")
                        break
            break
