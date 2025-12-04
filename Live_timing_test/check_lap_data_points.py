"""
檢查 Live F1 在一圈內的數據點數
一圈約90秒，看看有多少數據點
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

print("載入資料...")
data_source.load_all_data()

position_data = data_source.get_position_data()
cardata = data_source.get_cardata()

def time_to_seconds(time_str):
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0

# 找一個90秒的區間（約一圈）
start_time = "01:00:00.000"
end_time = "01:01:30.000"  # 90秒後

start_sec = time_to_seconds(start_time)
end_sec = time_to_seconds(end_time)

# 計算這個區間內的資料點數
position_count = 0
cardata_count = 0

for rec in position_data:
    t = time_to_seconds(rec['timestamp'])
    if start_sec <= t <= end_sec:
        position_count += 1

for rec in cardata:
    t = time_to_seconds(rec['timestamp'])
    if start_sec <= t <= end_sec:
        cardata_count += 1

print(f"\n在90秒內 (一圈時間):")
print(f"  Position 資料點: {position_count} 個")
print(f"  CarData 資料點: {cardata_count} 個")
print(f"\n這意味著:")
print(f"  Position: 每 {90/max(1,position_count):.1f} 秒更新一次")
print(f"  CarData: 每 {90/max(1,cardata_count):.1f} 秒更新一次")

print(f"\n對比 FastF1:")
print(f"  遙測資料: 90秒 × 7.6 Hz = 約 {90*7.6:.0f} 個資料點")
print(f"  位置資料: 90秒 × 3.8 Hz = 約 {90*3.8:.0f} 個資料點")

print(f"\n結論:")
print(f"  Live F1 的資料密度是 FastF1 的 {(90*3.8)/max(1,position_count):.1f}x 到 {(90*7.6)/max(1,cardata_count):.1f}x")
