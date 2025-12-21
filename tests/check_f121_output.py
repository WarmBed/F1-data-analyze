"""檢查 F121 輸出是否包含加速性能數據"""
import json

# 讀取 JSON 檔案
with open('json/fp2_straight_line_all_laps_analysis_2024_Bahrain_FP2.json', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("F121 加速性能數據驗證報告")
print("=" * 80)

# 檢查模式 A（統一分析）
mode_a = data.get('mode_a_unified', {})
drivers = mode_a.get('drivers', [])

if drivers:
    print(f"\n✅ 找到 {len(drivers)} 位車手的數據\n")
    
    # 檢查前 3 位車手
    for i, driver_data in enumerate(drivers[:3], 1):
        driver = driver_data['driver']
        print(f"【車手 {i}】{driver}")
        print(f"  圈數: {driver_data['total_laps']} 圈")
        print(f"  有效速度圈: {driver_data['valid_speed_laps']} 圈")
        
        # 速度統計
        speed_stats = driver_data.get('speed_stats', {})
        print(f"  速度中位數: {speed_stats.get('median', 0):.1f} km/h")
        print(f"  速度平均值: {speed_stats.get('mean', 0):.1f} km/h")
        
        # ✅ 檢查加速性能數據（100→300 km/h）
        accel_stats = driver_data.get('acceleration_100_300_stats')
        if accel_stats:
            print(f"  ✅ 100→300 km/h 加速時間:")
            print(f"     中位數: {accel_stats.get('median', 0):.3f} 秒")
            print(f"     平均值: {accel_stats.get('mean', 0):.3f} 秒")
            print(f"     最快: {accel_stats.get('min', 0):.3f} 秒")
            print(f"     最慢: {accel_stats.get('max', 0):.3f} 秒")
        else:
            print(f"  ❌ 無 100→300 km/h 加速數據")
        
        # ✅ 檢查推算到最高速度的時間
        time_to_max_stats = driver_data.get('time_to_max_speed_stats')
        if time_to_max_stats:
            print(f"  ✅ 100 km/h → 最高速度時間（線性推算）:")
            print(f"     中位數: {time_to_max_stats.get('median', 0):.3f} 秒")
            print(f"     平均值: {time_to_max_stats.get('mean', 0):.3f} 秒")
        else:
            print(f"  ❌ 無推算到最高速度的時間數據")
        
        print()
else:
    print("❌ 沒有找到車手數據")

print("=" * 80)
print("驗證完成")
print("=" * 80)
