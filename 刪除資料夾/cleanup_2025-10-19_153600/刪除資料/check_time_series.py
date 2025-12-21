#!/usr/bin/env python3
"""檢查 comparison_telemetry JSON 的時間序列數據"""
import json

# 讀取 JSON
with open('json/comparison_telemetry_VER_LEC_2024_Japan_R_Lap1_Lap1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("📊 JSON 時間序列數據檢查")
print("=" * 80)

# 檢查頂層結構
print("\n頂層欄位:")
for key in data.keys():
    print(f"  • {key}")

# 檢查 time_series
if 'time_series' in data:
    print("\n✅ 找到 time_series 欄位！")
    ts = data['time_series']
    
    print("\ntime_series 結構:")
    print(f"  Keys: {list(ts.keys())}")
    
    # 檢查雙車手數據
    if 'driver1' in ts and 'driver2' in ts:
        print("\n🏎️🏎️  雙車手模式時間序列:")
        
        for driver_key in ['driver1', 'driver2']:
            driver_data = ts[driver_key]
            print(f"\n  {driver_key}: {driver_data.get('driver')}")
            print(f"    • 數據點數: {driver_data.get('data_points')}")
            print(f"    • 可用通道數: {len(driver_data.get('available_channels', []))}")
            print(f"    • 時間參考: {driver_data.get('time_reference')}")
            
            # 檢查時間數據
            if 'time_seconds' in driver_data:
                time_data = driver_data['time_seconds']
                valid_times = [t for t in time_data if t is not None]
                print(f"    ✅ 時間數據: {len(time_data)} 個數據點")
                if valid_times:
                    print(f"       - 時間範圍: {min(valid_times):.2f}s ~ {max(valid_times):.2f}s")
                    print(f"       - 平均間隔: {(max(valid_times) - min(valid_times)) / len(valid_times):.4f}s")
            else:
                print(f"    ❌ 缺少 time_seconds")
            
            # 列出可用的遙測通道
            telemetry_channels = [k for k in driver_data.keys() 
                                if k not in ['driver', 'data_points', 'time_reference', 
                                           'available_channels', 'time_seconds']]
            print(f"    • 遙測通道 ({len(telemetry_channels)}):")
            for ch in telemetry_channels[:10]:  # 只顯示前10個
                ch_data = driver_data[ch]
                valid_data = [v for v in ch_data if v is not None]
                if valid_data:
                    if ch == 'speed_kmh':
                        print(f"       ✅ {ch}: {min(valid_data):.1f} ~ {max(valid_data):.1f} km/h")
                    elif ch == 'rpm':
                        print(f"       ✅ {ch}: {int(min(valid_data))} ~ {int(max(valid_data))} RPM")
                    elif ch == 'distance_meters':
                        print(f"       ✅ {ch}: {min(valid_data):.1f} ~ {max(valid_data):.1f} m")
                    else:
                        print(f"       ✅ {ch}: {len(valid_data)} 個有效值")
            
            if len(telemetry_channels) > 10:
                print(f"       ... 還有 {len(telemetry_channels) - 10} 個通道")
    
    elif 'driver' in ts:
        print("\n🏎️  單車手模式時間序列:")
        print(f"  • 車手: {ts.get('driver')}")
        print(f"  • 數據點數: {ts.get('data_points')}")
        print(f"  • 時間參考: {ts.get('time_reference')}")
        
        if 'time_seconds' in ts:
            time_data = ts['time_seconds']
            valid_times = [t for t in time_data if t is not None]
            print(f"  ✅ 時間數據: {len(time_data)} 個數據點")
            if valid_times:
                print(f"     - 時間範圍: {min(valid_times):.2f}s ~ {max(valid_times):.2f}s")
    
    # 驗證時間序列與遙測數據對齊
    print("\n📐 數據對齊驗證:")
    results = data.get('results', {})
    telemetry_comp = results.get('telemetry_comparison', {})
    
    if 'Speed' in telemetry_comp and 'driver1' in ts:
        speed_data_count = len(telemetry_comp['Speed'].get('driver1_data', []))
        time_data_count = ts['driver1'].get('data_points', 0)
        print(f"  • 遙測數據點數: {speed_data_count}")
        print(f"  • 時間數據點數: {time_data_count}")
        if speed_data_count == time_data_count:
            print(f"  ✅ 數據點數量一致！")
        else:
            print(f"  ⚠️  數據點數量不一致")
    
else:
    print("\n❌ 沒有找到 time_series 欄位")

print("\n" + "=" * 80)
print("檢查完成！")
print("=" * 80)
