"""
檢查 DriverList 和 PIT 相關資料
"""
import sys
from core.logger import get_logger

logger = get_logger("live_timing_test.check_driver_and_pit", component="gui")

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

logger.info("%s", "=" * 70)
logger.info("檢查 DriverList 和 PIT 資料")
logger.info("%s", "=" * 70)

# 1. 檢查 DriverList
logger.info("[1] 載入 DriverList.jsonStream...")
try:
    driver_list = data_source._load_stream("DriverList.jsonStream", compressed=False)
    if driver_list:
        logger.info("成功載入 %s 筆記錄", len(driver_list))
        
        # 檢查第一筆資料結構
        if driver_list:
            first_record = driver_list[0]
            logger.info("第一筆資料:")
            logger.info("  時間戳: %s", first_record.get('timestamp'))
            
            data = first_record.get('data', {})
            if isinstance(data, dict):
                # 顯示所有車手
                for driver_num, driver_info in list(data.items())[:3]:
                    logger.info("  車手 #%s:", driver_num)
                    for key, value in driver_info.items():
                        logger.info("    %s: %s", key, value)
    else:
        logger.warning("DriverList 載入失敗")
except Exception as e:
    logger.exception("DriverList 載入失敗: %s", e)

# 2. 檢查 TimingData 中是否有 PIT 資訊
logger.info("%s", "=" * 70)
logger.info("[2] 檢查 TimingData 中的 PIT 資訊...")
logger.info("%s", "=" * 70)

data_source.load_all_data()
timing_data = data_source.get_timing_data()

logger.info("總 Timing 記錄: %s", len(timing_data))

# 搜尋包含 PIT 相關欄位的記錄
pit_related_fields = ['InPit', 'PitOut', 'PitTime', 'Pits', 'NumberOfPitStops']
found_pit_data = False

for i, record in enumerate(timing_data):
    data = record.get('data', {})
    lines = data.get('Lines', {})
    
    for driver_num, driver_data in lines.items():
        for field in pit_related_fields:
            if field in driver_data:
                if not found_pit_data:
                    logger.info("找到 PIT 相關資料!")
                    found_pit_data = True
                
                timestamp = record.get('timestamp')
                value = driver_data.get(field)
                logger.info(
                    "  [%s] %s - 車手 #%s: %s = %s",
                    i,
                    timestamp,
                    driver_num,
                    field,
                    value,
                )
                
                # 只顯示前10個
                if i > 100:
                    break
        
        if i > 100 and found_pit_data:
            break
    
    if i > 100 and found_pit_data:
        break

if not found_pit_data:
    logger.warning("未找到 PIT 相關資料")
    logger.info("可能的原因:")
    logger.info("  1. Live F1 API 不提供 PIT 資訊")
    logger.info("  2. PIT 資訊在其他 Stream 中（例如 TrackStatus.jsonStream）")
    logger.info("  3. 需要檢查其他欄位名稱")

# 3. 列出可用的所有 Stream
logger.info("%s", "=" * 70)
logger.info("[3] 可用的 Stream 檔案")
logger.info("%s", "=" * 70)

common_streams = [
    "Position.z.jsonStream",
    "CarData.z.jsonStream", 
    "TimingData.jsonStream",
    "DriverList.jsonStream",
    "TrackStatus.jsonStream",
    "SessionInfo.jsonStream",
    "TimingStats.jsonStream",
    "LapCount.jsonStream"
]

logger.info("嘗試載入各種 Stream:")
for stream_name in common_streams:
    try:
        compressed = stream_name.endswith('.z.jsonStream')
        data = data_source._load_stream(stream_name, compressed=compressed)
        if data:
            logger.info("  ✅ %s: %s 筆記錄", stream_name, len(data))
        else:
            logger.warning("  ❌ %s: 載入失敗", stream_name)
    except Exception as e:
        logger.exception("  ❌ %s: %s", stream_name, e)
