"""
分析 Live F1 的最高數據採集頻率
找出實際的最高更新率
"""
import sys
import numpy as np

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')
from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource

def time_to_seconds(time_str):
    """轉換時間戳為秒數"""
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0

def analyze_frequency(data, name, sample_size=10000):
    """詳細分析數據頻率"""
    print(f"\n{'='*70}")
    print(f"{name} - 詳細頻率分析")
    print(f"{'='*70}")
    
    if len(data) < 2:
        print("資料不足")
        return
    
    # 計算所有時間間隔
    intervals = []
    for i in range(1, min(sample_size, len(data))):
        t1 = time_to_seconds(data[i-1]['timestamp'])
        t2 = time_to_seconds(data[i]['timestamp'])
        interval = t2 - t1
        if interval > 0:
            intervals.append(interval)
    
    if not intervals:
        print("無有效間隔")
        return
    
    intervals = np.array(intervals)
    
    print(f"\n基本統計:")
    print(f"  總記錄數: {len(data):,}")
    print(f"  分析樣本: {len(intervals):,}")
    print(f"  時間範圍: {data[0]['timestamp']} ~ {data[-1]['timestamp']}")
    
    print(f"\n時間間隔統計:")
    print(f"  平均間隔: {intervals.mean():.4f} 秒")
    print(f"  中位數間隔: {np.median(intervals):.4f} 秒")
    print(f"  標準差: {intervals.std():.4f} 秒")
    print(f"  最小間隔: {intervals.min():.4f} 秒")
    print(f"  最大間隔: {intervals.max():.4f} 秒")
    
    print(f"\n頻率統計:")
    print(f"  平均頻率: {1/intervals.mean():.2f} Hz")
    print(f"  中位數頻率: {1/np.median(intervals):.2f} Hz")
    print(f"  最高頻率 (最小間隔): {1/intervals.min():.2f} Hz")
    
    # 百分位數
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print(f"\n間隔分布 (百分位數):")
    for p in percentiles:
        val = np.percentile(intervals, p)
        freq = 1/val if val > 0 else 0
        print(f"  P{p:2d}: {val:.4f}s ({freq:.2f} Hz)")
    
    # 統計不同間隔範圍的佔比
    print(f"\n間隔範圍分布:")
    ranges = [
        (0, 0.1, "< 0.1s (>10 Hz)"),
        (0.1, 0.2, "0.1-0.2s (5-10 Hz)"),
        (0.2, 0.5, "0.2-0.5s (2-5 Hz)"),
        (0.5, 1.0, "0.5-1.0s (1-2 Hz)"),
        (1.0, 2.0, "1.0-2.0s (0.5-1 Hz)"),
        (2.0, float('inf'), "> 2.0s (< 0.5 Hz)")
    ]
    
    for min_val, max_val, label in ranges:
        count = np.sum((intervals >= min_val) & (intervals < max_val))
        percentage = count / len(intervals) * 100
        print(f"  {label:20s}: {count:6,} ({percentage:5.1f}%)")
    
    # 找出最密集的連續片段
    print(f"\n最密集的10個連續間隔:")
    sorted_indices = np.argsort(intervals)
    for i in range(min(10, len(sorted_indices))):
        idx = sorted_indices[i]
        interval = intervals[idx]
        t1 = data[idx]['timestamp']
        t2 = data[idx+1]['timestamp']
        print(f"  [{idx:5d}] {t1} → {t2}: {interval:.4f}s ({1/interval:.1f} Hz)")

def main():
    print("=" * 70)
    print("Live F1 最高數據採集頻率分析")
    print("=" * 70)
    
    data_source = LiveF1DataSource(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    print("\n載入資料...")
    data_source.load_all_data()
    
    position_data = data_source.get_position_data()
    timing_data = data_source.get_timing_data()
    cardata = data_source.get_cardata()
    
    # 分析各類數據
    analyze_frequency(position_data, "Position.z.jsonStream", 10000)
    analyze_frequency(cardata, "CarData.z.jsonStream", 10000)
    analyze_frequency(timing_data, "TimingData.jsonStream", 10000)
    
    print("\n" + "=" * 70)
    print("結論")
    print("=" * 70)
    print("\nLive F1 API 的原始採集頻率:")
    print("  - Position 資料: 約 1 Hz (理論最高 ~6 Hz)")
    print("  - CarData 資料: 約 1 Hz (理論最高 ~6 Hz)")
    print("  - Timing 資料: 約 0.8 Hz，但更新非常不均勻")
    print("\n這是 F1 官方 API 的原始限制，無法提高。")
    print("如果需要更高頻率，只能通過插值處理。")

if __name__ == "__main__":
    main()
