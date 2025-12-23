"""分析 CarData 的採樣率，判斷是否足夠測量反應時間"""
import json
import os

os.chdir(r'c:\Users\mike2\OneDrive\Code\F1-data-analyze')

# 載入 CarData
data = json.load(open('json/LiveF1/2025/Abu_Dhabi_Race/CarData.json', encoding='utf-8'))
records = data['records']

print('=== CarData 採樣率分析 ===')
print(f'總記錄數: {len(records)}')

# 分析前 100 筆的時間間隔
timestamps = []
for rec in records[:100]:
    ts = rec.get('timestamp', '')
    parts = ts.split(':')
    if len(parts) == 3:
        h, m, s = parts
        sec = float(h)*3600 + float(m)*60 + float(s)
        timestamps.append((ts, sec))

print(f'\n前 10 筆記錄的時間戳:')
for i in range(min(10, len(timestamps))):
    print(f'  {timestamps[i][0]}')

print(f'\n時間間隔分析:')
intervals = [timestamps[i+1][1] - timestamps[i][1] for i in range(len(timestamps)-1)]
if intervals:
    avg_interval = sum(intervals) / len(intervals)
    min_interval = min(intervals)
    max_interval = max(intervals)
    print(f'  平均間隔: {avg_interval*1000:.1f} ms')
    print(f'  最小間隔: {min_interval*1000:.1f} ms')
    print(f'  最大間隔: {max_interval*1000:.1f} ms')
    print(f'  採樣率: ~{1/avg_interval:.1f} Hz')
    
    # 判斷是否足夠測量反應時間
    print(f'\n=== 反應時間測量可行性 ===')
    reaction_time_range = (0.1, 0.4)  # F1 反應時間範圍 (秒)
    
    if avg_interval <= 0.05:  # 50ms = 20Hz
        print(f'✅ 採樣率足夠 ({1/avg_interval:.0f} Hz)')
        print(f'   可以測量 {reaction_time_range[0]}-{reaction_time_range[1]} 秒的反應時間')
        print(f'   精度: ±{avg_interval*1000:.0f} ms')
    elif avg_interval <= 0.1:  # 100ms = 10Hz
        print(f'⚠️ 採樣率勉強 ({1/avg_interval:.0f} Hz)')
        print(f'   測量精度: ±{avg_interval*1000:.0f} ms')
        print(f'   可能無法區分 0.1s vs 0.2s 的差異')
    else:
        print(f'❌ 採樣率不足 ({1/avg_interval:.0f} Hz)')
        print(f'   無法準確測量反應時間')

# 檢查起跑區域的採樣率 (可能更密集)
print(f'\n=== 檢查起跑時刻附近的採樣率 ===')

# 找到車速開始變化的記錄 (起跑時刻)
start_idx = None
for i, rec in enumerate(records):
    entries = rec.get('data', {}).get('Entries', [])
    if entries:
        cars = entries[0].get('Cars', {})
        driver1 = cars.get('1', {})
        speed = driver1.get('Channels', {}).get('2', 0)  # Channel 2 = Speed
        rpm = driver1.get('Channels', {}).get('0', 0)    # Channel 0 = RPM
        
        # 起跑前: 速度=0, RPM 高 (約 10000-12000)
        # 起跑後: 速度開始上升
        if speed > 0 and rpm > 5000:
            start_idx = max(0, i - 10)  # 往前看 10 筆
            break

if start_idx:
    print(f'找到起跑時刻附近 (index {start_idx})')
    
    # 分析起跑時刻附近的採樣間隔
    start_times = []
    for rec in records[start_idx:start_idx+30]:
        ts = rec.get('timestamp', '')
        parts = ts.split(':')
        if len(parts) == 3:
            h, m, s = parts
            sec = float(h)*3600 + float(m)*60 + float(s)
            
            entries = rec.get('data', {}).get('Entries', [])
            speed = 0
            if entries:
                cars = entries[0].get('Cars', {})
                driver1 = cars.get('1', {})
                speed = driver1.get('Channels', {}).get('2', 0)
            
            start_times.append((ts, sec, speed))
            print(f'  {ts} | Speed: {speed:3d} km/h')
    
    if len(start_times) > 1:
        start_intervals = [start_times[i+1][1] - start_times[i][1] for i in range(len(start_times)-1)]
        avg_start = sum(start_intervals) / len(start_intervals)
        print(f'\n起跑區域平均間隔: {avg_start*1000:.1f} ms ({1/avg_start:.1f} Hz)')
