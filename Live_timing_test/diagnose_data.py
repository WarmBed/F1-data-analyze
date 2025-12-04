"""診斷 Live Timing 數據問題"""
import json
import os

data_dir = "data/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race"

print("=" * 70)
print("診斷 Live Timing 數據")
print("=" * 70)

# 1. Position.z.jsonStream
pos_file = os.path.join(data_dir, "Position.z.jsonStream")
with open(pos_file, 'r', encoding='utf-8-sig') as f:
    pos_lines = [l.strip() for l in f if l.strip()]

print(f"\n📍 Position.z.jsonStream:")
print(f"  總行數: {len(pos_lines)}")
print(f"  第一行時間戳: {pos_lines[0][:12]}")
print(f"  第 100 行時間戳: {pos_lines[99][:12] if len(pos_lines) > 99 else 'N/A'}")
print(f"  最後一行時間戳: {pos_lines[-1][:12]}")

# 2. TimingData.jsonStream
timing_file = os.path.join(data_dir, "TimingData.jsonStream")
with open(timing_file, 'r', encoding='utf-8-sig') as f:
    timing_lines = [l.strip() for l in f if l.strip()]

print(f"\n⏱️  TimingData.jsonStream:")
print(f"  總行數: {len(timing_lines)}")
print(f"  第一行時間戳: {timing_lines[0][:12]}")
print(f"  第 100 行時間戳: {timing_lines[99][:12] if len(timing_lines) > 99 else 'N/A'}")
print(f"  最後一行時間戳: {timing_lines[-1][:12]}")

# 檢查 TimingData 第一行內容
try:
    first_timing_data = json.loads(timing_lines[0][12:])
    if 'Lines' in first_timing_data:
        print(f"  車手數量: {len(first_timing_data['Lines'])}")
        sample_driver = list(first_timing_data['Lines'].keys())[0]
        driver_data = first_timing_data['Lines'][sample_driver]
        print(f"  範例車手 {sample_driver}:")
        print(f"    圈數: {driver_data.get('NumberOfLaps', 'N/A')}")
        print(f"    排名: {driver_data.get('Position', 'N/A')}")
except Exception as e:
    print(f"  ⚠️ 解析失敗: {e}")

# 3. CarData.z.jsonStream
cardata_file = os.path.join(data_dir, "CarData.z.jsonStream")
with open(cardata_file, 'r', encoding='utf-8-sig') as f:
    cardata_lines = [l.strip() for l in f if l.strip()]

print(f"\n🚗 CarData.z.jsonStream:")
print(f"  總行數: {len(cardata_lines)}")
print(f"  第一行時間戳: {cardata_lines[0][:12]}")
print(f"  第 100 行時間戳: {cardata_lines[99][:12] if len(cardata_lines) > 99 else 'N/A'}")
print(f"  最後一行時間戳: {cardata_lines[-1][:12]}")

# 4. 時間戳轉換測試
def ts_to_seconds(ts):
    h = int(ts[0:2])
    m = int(ts[2:4])
    s = float(ts[4:])
    return h * 3600 + m * 60 + s

pos_first_sec = ts_to_seconds(pos_lines[0][:12])
pos_last_sec = ts_to_seconds(pos_lines[-1][:12])
pos_duration = pos_last_sec - pos_first_sec

print(f"\n⏰ 時間分析:")
print(f"  Position 第一筆: {pos_lines[0][:12]} ({pos_first_sec:.1f}s)")
print(f"  Position 最後一筆: {pos_lines[-1][:12]} ({pos_last_sec:.1f}s)")
print(f"  Position 時長: {pos_duration:.1f}s = {pos_duration/60:.1f}分鐘")

timing_first_sec = ts_to_seconds(timing_lines[0][:12])
timing_last_sec = ts_to_seconds(timing_lines[-1][:12])

print(f"\n  Timing 第一筆: {timing_lines[0][:12]} ({timing_first_sec:.1f}s)")
print(f"  Timing 最後一筆: {timing_lines[-1][:12]} ({timing_last_sec:.1f}s)")
print(f"  時間差: Position vs Timing 起始 = {pos_first_sec - timing_first_sec:.1f}s")

print("\n" + "=" * 70)
