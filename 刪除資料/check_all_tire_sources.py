"""
檢查：GUI 可能使用的所有數據源
看看是否有其他 JSON 文件或緩存數據
"""
import json
import glob

print("=" * 80)
print("檢查所有可能的輪胎數據源")
print("=" * 80)

# 查找所有可能的輪胎數據文件
patterns = [
    'json/*tire*2025*Japan*.json',
    'json/*strategy*2025*Japan*.json',
    'json/*telemetry*2025*Japan*.json',
]

all_files = []
for pattern in patterns:
    all_files.extend(glob.glob(pattern))

all_files = list(set(all_files))  # 去重

print(f"\n找到 {len(all_files)} 個可能的數據文件:\n")

for filepath in all_files:
    print(f"{'='*70}")
    print(f"文件: {filepath}")
    print(f"{'='*70}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 檢查是否包含 stint 數據
        has_stint = False
        
        # 檢查各種可能的結構
        if 'drivers_analysis' in data:
            drivers = data['drivers_analysis']
            print(f"✅ 找到 drivers_analysis，包含 {len(drivers)} 個車手")
            
            # 檢查第一個車手的 stint
            first_driver = list(drivers.keys())[0] if drivers else None
            if first_driver:
                stint_data = drivers[first_driver].get('stint_analysis', [])
                if stint_data:
                    has_stint = True
                    first_stint = stint_data[0]
                    print(f"   示例 Stint: start={first_stint.get('start_lap')}, end={first_stint.get('end_lap')}")
        
        if 'data' in data and isinstance(data.get('data'), dict):
            inner_data = data['data']
            if 'all_drivers_telemetry' in inner_data:
                print(f"✅ 找到 all_drivers_telemetry 結構")
                # 這可能是 telemetry 文件，檢查是否有 tire 數據
                first_driver_key = list(inner_data['all_drivers_telemetry'].keys())[0]
                driver_info = inner_data['all_drivers_telemetry'][first_driver_key]
                if 'tire_analysis' in driver_info:
                    print(f"   包含 tire_analysis")
        
        if not has_stint:
            print("   ⚠️ 此文件可能不包含 stint_analysis 數據")
        
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")

print("\n" + "=" * 80)
print("結論:")
print("-" * 80)
print("如果有多個文件包含 stint 數據，GUI 可能載入了錯誤的文件")
print("=" * 80)
