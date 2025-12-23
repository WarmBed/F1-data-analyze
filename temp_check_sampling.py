"""檢查 Live Timing 數據的採樣率和精度"""
import json

# 載入數據
data = json.load(open('json/LiveF1/2025/Abu_Dhabi_Race/CarData.json', 'r', encoding='utf-8'))
records = data['records']

print(f"總記錄數: {len(records)}")
print(f"比賽時長約 2 小時 = 7200 秒")
print(f"平均採樣率: {len(records) / 7200:.2f} Hz (每秒記錄數)")

print("\n時間戳樣本 (連續 20 筆):")
for i, rec in enumerate(records[1000:1020]):
    print(f"  {i}: {rec['timestamp']}")

# 計算相鄰記錄的時間間隔
def parse_ts(ts):
    parts = ts.split(':')
    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s

print("\n時間間隔分析:")
intervals = []
for i in range(len(records) - 1):
    if i < 2000:  # 只分析前 2000 筆
        t1 = parse_ts(records[i]['timestamp'])
        t2 = parse_ts(records[i+1]['timestamp'])
        intervals.append(t2 - t1)

if intervals:
    avg_interval = sum(intervals) / len(intervals)
    min_interval = min(intervals)
    max_interval = max(intervals)
    print(f"  平均間隔: {avg_interval*1000:.1f} ms")
    print(f"  最小間隔: {min_interval*1000:.1f} ms")
    print(f"  最大間隔: {max_interval*1000:.1f} ms")
    print(f"  採樣率: {1/avg_interval:.1f} Hz")

print("\n結論:")
if min_interval <= 0.1:
    print("  ✅ 時間精度足夠測量 0.1 秒級別的反應時間差異")
else:
    print(f"  ⚠️ 最小時間間隔 {min_interval*1000:.0f}ms，可能不足以精確測量反應時間")
