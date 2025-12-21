"""檢查功能13的JSON輸出是否包含時間序列數據"""
import json
import os

json_file = "json/comparison_telemetry_VER_LEC_2024_Australia_R_Lap1_Lap1.json"

if not os.path.exists(json_file):
    print(f"❌ 找不到檔案: {json_file}")
    exit(1)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("📊 JSON 結構檢查報告")
print("="*80)

# 檢查基本結構
print(f"\n✅ 是否有 time_series: {'time_series' in data}")

if 'time_series' not in data:
    print("❌ 沒有 time_series 數據！")
    exit(1)

ts = data['time_series']

# 檢查 driver1 結構
print(f"\n📋 Driver1 資訊:")
driver1 = ts.get('driver1', {})
print(f"  • 車手代碼: {driver1.get('driver_code', 'N/A')}")
print(f"  • 總通道數: {driver1.get('total_channels', 0)}")
print(f"  • 可用通道: {ts.get('available_channels', [])}")

# 檢查第一個通道的詳細結構
if driver1.get('channels'):
    first_channel = list(driver1['channels'].keys())[0]
    first_data = driver1['channels'][first_channel]
    
    print(f"\n🔍 第一個通道 ({first_channel}) 的數據結構:")
    print(f"  • 通道名稱: {first_data.get('name', 'N/A')}")
    print(f"  • 數據點數: {first_data.get('data_points', 0)}")
    print(f"  • 是否有 distance_meters: {'distance_meters' in first_data}")
    print(f"  • 是否有 time_seconds: {'time_seconds' in first_data}")
    print(f"  • 是否有 values: {'values' in first_data}")
    
    if 'distance_meters' in first_data:
        print(f"  • distance_meters 長度: {len(first_data['distance_meters'])}")
        print(f"  • distance_meters 範圍: {first_data['distance_meters'][0]:.2f} ~ {first_data['distance_meters'][-1]:.2f} m")
    
    if 'time_seconds' in first_data:
        print(f"  • time_seconds 長度: {len(first_data['time_seconds'])}")
        print(f"  • time_seconds 範圍: {first_data['time_seconds'][0]:.2f} ~ {first_data['time_seconds'][-1]:.2f} s")
        print(f"  ✅ 時間數據已成功添加！")
    else:
        print(f"  ❌ 沒有 time_seconds 數據！")
    
    if 'values' in first_data:
        print(f"  • values 長度: {len(first_data['values'])}")
        print(f"  • values 範圍: {min(first_data['values']):.2f} ~ {max(first_data['values']):.2f}")

# 檢查所有通道
print(f"\n📊 所有通道的時間數據統計:")
channels_with_time = 0
total_channels = len(driver1.get('channels', {}))

for ch_name, ch_data in driver1.get('channels', {}).items():
    if 'time_seconds' in ch_data:
        channels_with_time += 1
        print(f"  ✅ {ch_name}: 有時間數據 ({len(ch_data['time_seconds'])} 個點)")
    else:
        print(f"  ❌ {ch_name}: 沒有時間數據")

print(f"\n📈 總結: {channels_with_time}/{total_channels} 個通道包含時間數據")

if channels_with_time == total_channels:
    print("✅ 所有通道都包含時間數據！")
elif channels_with_time > 0:
    print("⚠️ 部分通道包含時間數據")
else:
    print("❌ 沒有通道包含時間數據！")

print("\n" + "="*80)
