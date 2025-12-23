"""查看 TimingData 的 NumberOfLaps 和 Position 結構"""
import json

data = json.load(open('json/LiveF1/2025/Abu_Dhabi_Race/TimingData.json', encoding='utf-8'))
records = data['records']

print("尋找 Lap 1 完成的記錄...")
for i, rec in enumerate(records):
    lines = rec['data'].get('Lines', {})
    if '1' in lines:
        d = lines['1']
        if isinstance(d, dict):
            laps = d.get('NumberOfLaps')
            pos = d.get('Position')
            if laps is not None:
                ts = rec['timestamp']
                try:
                    lap_num = int(laps)
                except:
                    lap_num = laps
                print(f"Record {i}: ts={ts}, NumberOfLaps={lap_num}, Position={pos}")
                if isinstance(lap_num, int) and lap_num >= 2:
                    break

print("\n尋找 Grid Position...")
for i, rec in enumerate(records[:500]):
    lines = rec['data'].get('Lines', {})
    if '1' in lines:
        d = lines['1']
        if isinstance(d, dict):
            pos = d.get('Position')
            if pos is not None:
                print(f"Record {i}: ts={rec['timestamp']}, Position={pos}")
                break
