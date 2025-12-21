"""展示最近的直線速度分析結果"""
import json
import os
from datetime import datetime

print("=" * 80)
print("📊 最近的直線速度分析結果")
print("=" * 80)

# 檢查已生成的 JSON 檔案
json_files = [
    "json/all_drivers_straight_line_speed_2025_China_R_20251018_210305.json",
    "json/all_drivers_straight_line_speed_2025_Australia_R_20251018_205712.json",
]

for json_file in json_files:
    if not os.path.exists(json_file):
        print(f"\n⚠️  檔案不存在：{json_file}")
        continue
    
    print(f"\n{'=' * 80}")
    print(f"📄 {os.path.basename(json_file)}")
    print(f"{'=' * 80}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data.get('success'):
            print(f"❌ 分析失敗：{data.get('message')}")
            continue
        
        result_data = data.get('data', {})
        metadata = result_data.get('metadata', {})
        drivers = result_data.get('drivers', [])
        
        # 元數據
        print(f"\n📋 元數據：")
        print(f"   年份：{metadata.get('year')}")
        print(f"   賽事：{metadata.get('race')}")
        print(f"   會話：{metadata.get('session')}")
        print(f"   演算法版本：{metadata.get('algorithm_version')}")
        print(f"   統一終點速度：{metadata.get('unified_end_speed_kmh', 'N/A')} km/h")
        print(f"   分析時間：{metadata.get('timestamp')}")
        
        # 車手排名（前 10 名）
        print(f"\n🏁 加速性能排名（前 10 名）：")
        print(f"{'排名':<6} {'車手':<8} {'車隊':<25} {'加速時間':<12} {'最高速度':<12} {'最高速度時間':<15}")
        print("-" * 90)
        
        for i, driver in enumerate(drivers[:10], 1):
            driver_code = driver.get('driver', 'N/A')
            team = driver.get('team', 'N/A')
            accel_time = driver.get('segment_accel_time_seconds')
            max_speed = driver.get('max_speed_kmh')
            max_speed_time = driver.get('max_speed_time_seconds')
            
            accel_str = f"{accel_time:.3f}s" if accel_time is not None else "N/A"
            speed_str = f"{max_speed:.1f} km/h" if max_speed is not None else "N/A"
            time_str = f"{max_speed_time:.3f}s" if max_speed_time is not None else "N/A"
            
            # 截斷車隊名稱
            team_short = team[:23] + ".." if len(team) > 25 else team
            
            print(f"{i:<6} {driver_code:<8} {team_short:<25} {accel_str:<12} {speed_str:<12} {time_str:<15}")
        
        # 統計數據
        print(f"\n📊 統計數據：")
        print(f"   總車手數：{len(drivers)}")
        
        if drivers:
            # 最快加速
            fastest = min(drivers, key=lambda d: d.get('segment_accel_time_seconds', float('inf')))
            print(f"   最快加速：{fastest.get('driver')} - {fastest.get('segment_accel_time_seconds'):.3f}s")
            
            # 最高速度
            top_speed = max(drivers, key=lambda d: d.get('max_speed_kmh', 0))
            print(f"   最高速度：{top_speed.get('driver')} - {top_speed.get('max_speed_kmh'):.1f} km/h")
            
            # 平均加速時間
            valid_times = [d.get('segment_accel_time_seconds') for d in drivers if d.get('segment_accel_time_seconds') is not None]
            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                print(f"   平均加速時間：{avg_time:.3f}s")
        
        print(f"\n✅ 檔案大小：{os.path.getsize(json_file) / 1024:.1f} KB")
        
    except Exception as e:
        print(f"\n❌ 讀取檔案失敗：{e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("💡 提示：使用以下命令生成新的分析")
print("=" * 80)
print("\npython f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s R")
print("\n" + "=" * 80)
