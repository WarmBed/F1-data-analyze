"""
分析 Live F1 的最高數據採集頻率
找出實際的最高更新率
"""
import sys
import numpy as np
from core.logger import get_logger

logger = get_logger("live_timing_test.analyze_max_frequency", component="gui")

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
    logger.info("%s", "=" * 70)
    logger.info("%s - 詳細頻率分析", name)
    logger.info("%s", "=" * 70)
    
    if len(data) < 2:
        logger.warning("資料不足")
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
        logger.warning("無有效間隔")
        return
    
    intervals = np.array(intervals)
    
    logger.info("基本統計:")
    logger.info("  總記錄數: %s", f"{len(data):,}")
    logger.info("  分析樣本: %s", f"{len(intervals):,}")
    logger.info("  時間範圍: %s ~ %s", data[0]['timestamp'], data[-1]['timestamp'])
    
    logger.info("時間間隔統計:")
    logger.info("  平均間隔: %.4f 秒", intervals.mean())
    logger.info("  中位數間隔: %.4f 秒", np.median(intervals))
    logger.info("  標準差: %.4f 秒", intervals.std())
    logger.info("  最小間隔: %.4f 秒", intervals.min())
    logger.info("  最大間隔: %.4f 秒", intervals.max())
    
    logger.info("頻率統計:")
    logger.info("  平均頻率: %.2f Hz", 1 / intervals.mean())
    logger.info("  中位數頻率: %.2f Hz", 1 / np.median(intervals))
    logger.info("  最高頻率 (最小間隔): %.2f Hz", 1 / intervals.min())
    
    # 百分位數
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    logger.info("間隔分布 (百分位數):")
    for p in percentiles:
        val = np.percentile(intervals, p)
        freq = 1/val if val > 0 else 0
        logger.info("  P%2d: %.4fs (%.2f Hz)", p, val, freq)
    
    # 統計不同間隔範圍的佔比
    logger.info("間隔範圍分布:")
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
        logger.info("  %-20s: %6s (%.1f%%)", label, f"{count:,}", percentage)
    
    # 找出最密集的連續片段
    logger.info("最密集的10個連續間隔:")
    sorted_indices = np.argsort(intervals)
    for i in range(min(10, len(sorted_indices))):
        idx = sorted_indices[i]
        interval = intervals[idx]
        t1 = data[idx]['timestamp']
        t2 = data[idx+1]['timestamp']
        logger.info("  [%5d] %s → %s: %.4fs (%.1f Hz)", idx, t1, t2, interval, 1 / interval)

def main():
    logger.info("%s", "=" * 70)
    logger.info("Live F1 最高數據採集頻率分析")
    logger.info("%s", "=" * 70)
    
    data_source = LiveF1DataSource(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    logger.info("載入資料...")
    data_source.load_all_data()
    
    position_data = data_source.get_position_data()
    timing_data = data_source.get_timing_data()
    cardata = data_source.get_cardata()
    
    # 分析各類數據
    analyze_frequency(position_data, "Position.z.jsonStream", 10000)
    analyze_frequency(cardata, "CarData.z.jsonStream", 10000)
    analyze_frequency(timing_data, "TimingData.jsonStream", 10000)
    
    logger.info("%s", "=" * 70)
    logger.info("結論")
    logger.info("%s", "=" * 70)
    logger.info("Live F1 API 的原始採集頻率:")
    logger.info("  - Position 資料: 約 1 Hz (理論最高 ~6 Hz)")
    logger.info("  - CarData 資料: 約 1 Hz (理論最高 ~6 Hz)")
    logger.info("  - Timing 資料: 約 0.8 Hz，但更新非常不均勻")
    logger.info("這是 F1 官方 API 的原始限制，無法提高。")
    logger.info("如果需要更高頻率，只能通過插值處理。")

if __name__ == "__main__":
    main()
