import json
import pprint

# 載入數據
with open('json/LiveF1/2025/Abu_Dhabi_Practice_2/TimingData.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

records = data['records']

# 尋找包含完整圈速的記錄
for i, record in enumerate(records[:5000]):
    lines = record.get('data', {}).get('Lines', {})
    
    for driver, driver_data in lines.items():
        last_lap_time = driver_data.get('LastLapTime', {})
        if last_lap_time.get('Value'):
            print(f"\n找到完整圈速數據 (記錄 {i}, 車手 {driver}):")
            print(f"NumberOfLaps: {driver_data.get('NumberOfLaps')}")
            print(f"LastLapTime: {last_lap_time}")
            print(f"\nSectors 結構:")
            pprint.pprint(driver_data.get('Sectors', {}))
            
            # 只顯示第一個範例
            exit()
