"""
檢查 driver_stints 使用的鍵值格式
"""
import pickle
from pathlib import Path

pkl_path = Path("data/live_timing_cache/2025/Abu_Dhabi_Race.pkl")
with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

driver_stints = data.get('driver_stints', {})
driver_info = data.get('driver_info', {})

print("=" * 80)
print("🔍 driver_stints 鍵值檢查")
print("=" * 80)
print(f"driver_stints 的鍵: {list(driver_stints.keys())}\n")

# 尋找 TSU 和 NOR 對應的車號
print("=" * 80)
print("🔍 driver_info 結構")
print("=" * 80)
print(f"driver_info 的鍵: {list(driver_info.keys())}\n")

if driver_info:
    print("車手映射 (車號 → TLA):")
    tsu_number = None
    nor_number = None
    
    for driver_number, info in driver_info.items():
        tla = info.get('driver_tla', info.get('tla', 'UNKNOWN'))
        name = info.get('full_name', info.get('name', 'UNKNOWN'))
        print(f"   {driver_number}: {tla} ({name})")
        
        if tla == 'TSU':
            tsu_number = driver_number
        elif tla == 'NOR':
            nor_number = driver_number
    
    # 檢查這些車號在 driver_stints 中的數據
    print("\n" + "=" * 80)
    print("🔍 TSU 和 NOR 的 stints 數據")
    print("=" * 80)
    
    if tsu_number and tsu_number in driver_stints:
        print(f"\n✅ TSU (車號 {tsu_number}) stints:")
        stints = driver_stints[tsu_number]
        for i, stint in enumerate(stints, 1):
            print(f"   Stint {i}:")
            for key, value in stint.items():
                print(f"      {key}: {value}")
    else:
        print(f"\n❌ TSU (車號 {tsu_number}) 沒有 stints 數據")
    
    if nor_number and nor_number in driver_stints:
        print(f"\n✅ NOR (車號 {nor_number}) stints:")
        stints = driver_stints[nor_number]
        for i, stint in enumerate(stints, 1):
            print(f"   Stint {i}:")
            for key, value in stint.items():
                print(f"      {key}: {value}")
    else:
        print(f"\n❌ NOR (車號 {nor_number}) 沒有 stints 數據")

# 檢查 tyre_state_index
print("\n" + "=" * 80)
print("🔍 tyre_state_index 結構")
print("=" * 80)

tyre_state_index = data.get('tyre_state_index', {})
print(f"tyre_state_index 的鍵: {list(tyre_state_index.keys())[:10]}...")  # 只顯示前 10 個

if tsu_number in tyre_state_index:
    print(f"\n✅ TSU (車號 {tsu_number}) 在 tyre_state_index 中")
    print(f"   數據點數量: {len(tyre_state_index[tsu_number])}")
    # 顯示前幾筆
    for i, (lap, state) in enumerate(list(tyre_state_index[tsu_number].items())[:5]):
        print(f"   Lap {lap}: {state}")
