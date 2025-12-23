import json
import os

os.chdir(r'c:\Users\mike2\OneDrive\Code\F1-data-analyze')

# 載入數據
with open('json/LiveF1/2025/Abu_Dhabi_Race/CarData.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

records = data['records']

results = []
results.append(f"總記錄數: {len(records)}")
results.append(f"比賽時長約 2 小時 = 7200 秒")
results.append(f"平均採樣率: {len(records) / 7200:.2f} Hz")

results.append("")
results.append("時間戳樣本 (連續 20 筆):")
for i, rec in enumerate(records[1000:1020]):
    results.append(f"  {i}: {rec['timestamp']}")

# 計算相鄰記錄的時間間隔
def parse_ts(ts):
    parts = ts.split(':')
    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s

results.append("")
results.append("時間間隔分析:")
intervals = []
for i in range(min(2000, len(records) - 1)):
    t1 = parse_ts(records[i]['timestamp'])
    t2 = parse_ts(records[i+1]['timestamp'])
    intervals.append(t2 - t1)

if intervals:
    avg_interval = sum(intervals) / len(intervals)
    min_interval = min(intervals)
    max_interval = max(intervals)
    results.append(f"  平均間隔: {avg_interval*1000:.1f} ms")
    results.append(f"  最小間隔: {min_interval*1000:.1f} ms")  
    results.append(f"  最大間隔: {max_interval*1000:.1f} ms")
    results.append(f"  採樣率: {1/avg_interval:.1f} Hz")

# 測試：找到起跑時刻各車手的第一個非零速度時間
results.append("")
results.append("起跑反應時間測試:")
start_times = {}
for rec in records:
    ts = rec['timestamp']
    entries = rec.get('data', {}).get('Entries', [])
    if not entries:
        continue
    cars = entries[0].get('Cars', {})
    for driver_num, driver_data in cars.items():
        if driver_num not in start_times:
            speed = driver_data.get('Channels', {}).get('2', 0)
            rpm = driver_data.get('Channels', {}).get('0', 0)
            # 偵測起跑 (速度>0 且 RPM 高)
            if speed > 5 and rpm > 8000:
                start_times[driver_num] = parse_ts(ts)

# 找到最早的起跑時間作為基準
if start_times:
    base_time = min(start_times.values())
    results.append("各車手相對反應時間 (相對於最快反應者):")
    sorted_times = sorted(start_times.items(), key=lambda x: x[1])
    for driver, t in sorted_times[:10]:
        delta = (t - base_time) * 1000
        results.append(f"  車手 #{driver}: +{delta:.0f} ms")
else:
    results.append("無法找到起跑資料")

# 寫入結果
with open('temp_output_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print("Done! Check temp_output_result.txt")
