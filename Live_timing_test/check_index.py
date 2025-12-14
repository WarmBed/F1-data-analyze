"""
檢查索引建立的正確性
"""
import sys
from core.logger import get_logger

logger = get_logger("live_timing_test.check_index", component="gui")

sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

logger.info("載入資料...")
data_source.load_all_data()

processor = LivePositionDataProcessor(data_source)

# 手動建立索引
timing_data = data_source.get_timing_data()
processor._build_timing_index(timing_data)

# 檢查索引內容
timing_timestamps = processor._timing_timestamps
timing_index = processor._timing_index_full

logger.info("Timing 索引大小: %s", len(timing_timestamps))
logger.info("檢查前5個時間戳的車手 #1 的狀態:")

for i, ts in enumerate(timing_timestamps[:5]):
    driver_1_state = timing_index[ts].get('1', {})
    lap = driver_1_state.get('lap')
    position = driver_1_state.get('position')
    logger.info("  [%s] %s: 圈數=%s, 排名=%s", i, ts, lap, position)

logger.info("檢查中段5個時間戳的車手 #1 的狀態:")
mid = len(timing_timestamps) // 2
for i, ts in enumerate(timing_timestamps[mid:mid+5]):
    driver_1_state = timing_index[ts].get('1', {})
    lap = driver_1_state.get('lap')
    position = driver_1_state.get('position')
    logger.info("  [%s] %s: 圈數=%s, 排名=%s", mid + i, ts, lap, position)

logger.info("檢查最後5個時間戳的車手 #1 的狀態:")
for i, ts in enumerate(timing_timestamps[-5:]):
    driver_1_state = timing_index[ts].get('1', {})
    lap = driver_1_state.get('lap')
    position = driver_1_state.get('position')
    logger.info(
        "  [%s] %s: 圈數=%s, 排名=%s",
        len(timing_timestamps) - 5 + i,
        ts,
        lap,
        position,
    )
