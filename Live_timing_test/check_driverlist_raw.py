"""
檢查 DriverList 原始資料結構
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

# 直接載入原始資料
driver_list_raw = data_source._load_stream("DriverList.jsonStream", compressed=False)

print(f"DriverList 記錄數: {len(driver_list_raw)}")

if driver_list_raw:
    print("\n第一筆記錄:")
    first = driver_list_raw[0]
    print(f"  timestamp: {first.get('timestamp')}")
    
    data = first.get('data', {})
    print(f"  data 類型: {type(data)}")
    print(f"  data keys: {list(data.keys())[:5]}")
    
    # 顯示第一位車手
    for key, value in list(data.items())[:2]:
        print(f"\n  車手 #{key}:")
        print(f"    類型: {type(value)}")
        if isinstance(value, dict):
            for k, v in value.items():
                print(f"      {k}: {v}")
