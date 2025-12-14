"""
檢查 CarData 和 TimingData 的時間範圍
"""
import requests
import json
import base64
import zlib
from datetime import timedelta
from core.logger import get_logger

logger = get_logger("live_timing_test.check_time_range", component="gui")

def decode_f1_packet(b64_str):
    try:
        decoded = base64.b64decode(b64_str)
        decompressed = zlib.decompress(decoded, wbits=-15)
        return json.loads(decompressed.decode('utf-8'))
    except:
        return None

def parse_ts(ts_str):
    parts = ts_str.split(':')
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    return timedelta(hours=h, minutes=m, seconds=s)

# CarData
logger.info("CarData time range:")
url1 = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/CarData.z.jsonStream"
r1 = requests.get(url1, timeout=60)
lines1 = r1.content.decode('utf-8-sig').split('\r\n')
lines1 = [l for l in lines1 if l.strip()]
logger.info("  First: %s", lines1[0][:12])
logger.info("  Last:  %s", lines1[-1][:12])

# TimingData  
logger.info("TimingData time range:")
url2 = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/TimingData.jsonStream"
r2 = requests.get(url2, timeout=60)
lines2 = r2.content.decode('utf-8-sig').split('\r\n')
lines2 = [l for l in lines2 if l.strip()]
logger.info("  First: %s", lines2[0][:12])
logger.info("  Last:  %s", lines2[-1][:12])

# 檢查 Lap 10 附近的 CarData
logger.info("CarData around 01:11:54 (Lap 10 start):")
target = timedelta(hours=1, minutes=11, seconds=54)
for line in lines1:
    ts = parse_ts(line[:12])
    if timedelta(hours=1, minutes=11, seconds=50) <= ts <= timedelta(hours=1, minutes=12, seconds=0):
        decoded = decode_f1_packet(line[12:])
        if decoded and 'Entries' in decoded:
            entry = decoded['Entries'][0]
            cars = entry.get('Cars', {})
            has_44 = '44' in cars
            logger.info("  %s | Cars: %s | Has 44: %s", line[:12], len(cars), has_44)
            if has_44:
                logger.info("    -> Speed: %s", cars['44']['Channels'].get('0', 'N/A'))
            break
