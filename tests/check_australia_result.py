"""檢查最新的 Australia 測試結果"""
import json

json_file = "json/all_drivers_straight_line_speed_2025_Australia_R.json"

try:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 80)
    print("Australia 2025 R - 全車手直線加速分析")
    print("=" * 80)
    
    print(f"\nAlgorithm Version: {data['data'].get('algorithm_version', 'N/A')}")
    print(f"Unified End Speed: {data['data'].get('unified_end_speed_kmh', 'N/A')} km/h")
    
    drivers = data['data']['driver_speeds']
    print(f"\n總車手數: {len(drivers)}")
    
    # 重點檢查 GAS、OCO、ALO
    target_drivers = ['GAS', 'OCO', 'ALO']
    
    print("\n" + "=" * 80)
    print("重點檢查: GAS、OCO、ALO 的最高速度時間")
    print("=" * 80)
    
    for driver_data in drivers:
        driver = driver_data['driver']
        if driver in target_drivers:
            accel_time = driver_data.get('segment_accel_time_seconds', 'N/A')
            max_speed_time = driver_data.get('max_speed_time_seconds', 'N/A')
            unified_end = driver_data.get('segment_unified_end_speed_kmh', 'N/A')
            personal_max = driver_data.get('segment_personal_max_speed_kmh', 'N/A')
            
            print(f"\n{driver}:")
            print(f"  加速時間（到統一終點）: {accel_time}s")
            print(f"  最高速度時間: {max_speed_time}s")
            print(f"  統一終點速度: {unified_end} km/h")
            print(f"  個人最高速度: {personal_max} km/h")
            
            if max_speed_time == 'N/A' or max_speed_time is None:
                print(f"  ⚠️  最高速度時間仍然是 N/A！")
            else:
                print(f"  ✅ 最高速度時間已修正！")
    
    # 顯示前 5 名
    print("\n" + "=" * 80)
    print("加速時間排名前 5 名:")
    print("=" * 80)
    
    sorted_drivers = sorted(drivers, key=lambda x: x.get('segment_accel_time_seconds', 9999))
    for i, driver_data in enumerate(sorted_drivers[:5], 1):
        driver = driver_data['driver']
        accel_time = driver_data.get('segment_accel_time_seconds', 'N/A')
        max_speed_time = driver_data.get('max_speed_time_seconds', 'N/A')
        print(f"{i}. {driver}: 加速 {accel_time}s, 最高速度時間 {max_speed_time}s")

except FileNotFoundError:
    print(f"❌ 找不到檔案: {json_file}")
except Exception as e:
    print(f"❌ 讀取失敗: {e}")
