"""
診斷索引累積問題
檢查為什麼所有時間戳都有圈數53
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource
from core.logger import get_logger


logger = get_logger(component="gui")

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

logger.info("載入 Timing 資料...")
data_source.load_all_data()
timing_data = data_source.get_timing_data()

# 按時間排序
sorted_timing = sorted(timing_data, key=lambda item: item.get('timestamp', ''))

logger.info(f"總記錄數: {len(sorted_timing)}")

# 找出車手 #1 圈數變化的記錄
logger.info("\n車手 #1 的圈數變化:")
prev_lap = None
change_count = 0

for i, record in enumerate(sorted_timing):
    timestamp = record.get('timestamp')
    data = record.get('data', {})
    lines = data.get('Lines', {})
    
    if '1' in lines:
        lap_num = lines['1'].get('NumberOfLaps')
        
        if lap_num != prev_lap:
            if change_count < 20:  # 只顯示前20次變化
                logger.info(f"  [{i}] {timestamp}: {prev_lap} → {lap_num}")
            change_count += 1
            prev_lap = lap_num

logger.info(f"\n總共 {change_count} 次圈數變化")

# 檢查最後一次圈數出現的位置
logger.info("\n檢查圈數53首次出現:")
for i, record in enumerate(sorted_timing):
    data = record.get('data', {})
    lines = data.get('Lines', {})
    
    if '1' in lines:
        lap_num = lines['1'].get('NumberOfLaps')
        if lap_num == 53:
            timestamp = record.get('timestamp')
            logger.info(f"  首次出現在 [{i}] {timestamp}")
            logger.info(f"  這是第 {i+1}/{len(sorted_timing)} 筆記錄 ({(i+1)/len(sorted_timing)*100:.1f}%)")
            break
