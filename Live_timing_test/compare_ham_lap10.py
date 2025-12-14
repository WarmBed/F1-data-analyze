"""
HAM Lap 10 Speed Data Comparison: LiveTiming vs fastf1
比較 Hamilton 第 10 圈的速度資料點數量
"""
import requests
import json
import base64
import zlib
import fastf1
from datetime import datetime
from core.logger import get_logger

logger = get_logger("live_timing_test.compare_ham_lap10", component="gui")

def decode_f1_packet(raw_b64_string):
    """解碼 F1 壓縮封包"""
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except:
        return None

logger.info("%s", "=" * 70)
logger.info("HAM (Hamilton) Lap 10 Speed Data Comparison")
logger.info("%s", "=" * 70)

# ========== Part 1: LiveTiming 原始資料 ==========
logger.info("[Part 1] LiveTiming Raw Data Analysis")
logger.info("%s", "-" * 70)

url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/CarData.z.jsonStream"
logger.info("[1] Downloading CarData...")
response = requests.get(url, timeout=60)
content = response.content

# 解析
text = content.decode('utf-8-sig')
lines = text.split('\r\n')
lines = [line for line in lines if line.strip()]

logger.info("[2] Parsing %s records...", len(lines))

# 收集 HAM (44號) 的所有速度資料
ham_speed_data = []

for line in lines:
    if len(line) < 12:
        continue
    
    timestamp = line[:12]
    decoded = decode_f1_packet(line[12:])
    
    if decoded and 'Entries' in decoded:
        for entry in decoded['Entries']:
            cars = entry.get('Cars', {})
            
            # 找 44 號車 (Hamilton)
            if '44' in cars:
                ham_data = cars['44']
                channels = ham_data.get('Channels', {})
                speed = channels.get('0')  # Channel 0 = Speed
                
                if speed is not None:
                    ham_speed_data.append({
                        'timestamp': timestamp,
                        'speed': speed,
                        'utc': entry.get('Utc', '')
                    })

logger.info("[3] HAM total speed readings: %s", len(ham_speed_data))

# 顯示前幾筆
logger.info("[4] Sample data (first 5):")
for i, data in enumerate(ham_speed_data[:5]):
    logger.info("    %s. %s | Speed: %s km/h", i + 1, data['timestamp'], data['speed'])

# ========== Part 2: fastf1 資料 ==========
logger.info("[Part 2] fastf1 Processed Data Analysis")
logger.info("%s", "-" * 70)

logger.info("[1] Loading session with fastf1...")
fastf1.Cache.enable_cache('f1_analysis_cache')
session = fastf1.get_session(2025, 'Japan', 'R')

logger.info("[2] Loading telemetry data...")
session.load()

# 取得 Hamilton 的資料
logger.info("[3] Filtering Hamilton's data...")
ham_laps = session.laps.pick_driver('HAM')

if len(ham_laps) == 0:
    logger.error("Hamilton not found in session!")
    logger.info("Available drivers:")
    for driver in session.drivers:
        logger.info("  - %s", driver)
    exit(1)

logger.info("    Total laps: %s", len(ham_laps))

# 取得第 10 圈
if len(ham_laps) < 10:
    logger.error("Only %s laps available, cannot get lap 10", len(ham_laps))
    exit(1)

lap_10 = ham_laps.iloc[9]  # Index 9 = Lap 10
logger.info("[4] Lap 10 info:")
logger.info("    Lap Time: %s", lap_10['LapTime'])
logger.info("    Lap Start: %s", lap_10['LapStartTime'])

# 取得第10圈的遙測資料
telemetry_10 = lap_10.get_telemetry()
speed_10 = telemetry_10['Speed']

logger.info("[5] Lap 10 telemetry:")
logger.info("    Total data points: %s", len(telemetry_10))
logger.info("    Speed readings: %s", len(speed_10))
logger.info("    Speed range: %.0f - %.0f km/h", speed_10.min(), speed_10.max())

# 顯示前幾筆
logger.info("[6] Sample telemetry (first 5):")
for i in range(min(5, len(speed_10))):
    row = telemetry_10.iloc[i]
    logger.info(
        "    %s. Time: %s | Speed: %.0f km/h | RPM: %.0f",
        i + 1,
        row['Time'],
        row['Speed'],
        row['RPM'],
    )

# ========== Part 3: 詳細比較 ==========
logger.info("[Part 3] Detailed Comparison")
logger.info("%s", "=" * 70)

logger.info("+------------------------+------------------+------------------+")
logger.info("|      Metric            |   LiveTiming     |     fastf1       |")
logger.info("+------------------------+------------------+------------------+")
logger.info("| HAM Total Readings     | %16s | N/A (all laps)   |", len(ham_speed_data))
logger.info("| Lap 10 Readings        | (需手動過濾)     | %16s |", len(speed_10))
logger.info("| Data Format            | JSON (nested)    | DataFrame        |")
logger.info("| Timestamp Type         | String           | Timedelta        |")
logger.info("| Speed Filter           | Manual           | Auto (valid)     |")
logger.info("+------------------------+------------------+------------------+")

# 嘗試從 LiveTiming 提取第10圈資料 (需要圈數資訊)
logger.info("[NOTE] LiveTiming 的 CarData.z 不包含圈數資訊!")
logger.info("       需要額外下載 TimingData 或 Position 來對應圈數。")

logger.info("[4] Key Findings:")
logger.info("  1. LiveTiming CarData.z 只包含遙測,無圈數標記")
logger.info("  2. fastf1 已整合多個資料源,自動對應圈數")
logger.info("  3. fastf1 的 Lap 10 有 %s 個速度資料點", len(speed_10))
logger.info("  4. 要從 LiveTiming 取得相同資料,需要:")
logger.info("     a. 下載 TimingData.jsonStream (圈數資訊)")
logger.info("     b. 下載 Position.z.jsonStream (GPS + 圈數)")
logger.info("     c. 時間戳對齊 CarData 與 Position")

# ========== Part 4: 下載 Position 資料嘗試對應 ==========
logger.info("[Part 4] Attempting to get lap data from Position.z")
logger.info("%s", "-" * 70)

position_url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/Position.z.jsonStream"
logger.info("[1] Downloading Position.z...")

try:
    pos_response = requests.get(position_url, timeout=60)
    if pos_response.status_code == 200:
        pos_content = pos_response.content
        pos_text = pos_content.decode('utf-8-sig')
        pos_lines = pos_text.split('\r\n')
        pos_lines = [line for line in pos_lines if line.strip()]
        
        logger.info("[2] Position records: %s", len(pos_lines))
        
        # 解析第一筆看結構
        if pos_lines:
            first_pos = decode_f1_packet(pos_lines[0][12:])
            if first_pos:
                logger.info("[3] Position data structure:")
                logger.info("    Keys: %s", list(first_pos.keys()))
                
                if 'Position' in first_pos:
                    positions = first_pos['Position']
                    if isinstance(positions, list) and len(positions) > 0:
                        sample = positions[0]
                        logger.info("    Sample entry: %s", sample)
                        
                        # 檢查是否有圈數資訊
                        if 'Entries' in sample:
                            logger.info("    Has 'Entries' field")
                        
                # 嘗試找 HAM 的圈數資訊
                ham_lap_data = []
                for line in pos_lines[:100]:  # 只看前100筆
                    decoded = decode_f1_packet(line[12:])
                    if decoded and 'Position' in decoded:
                        for entry in decoded['Position']:
                            if str(entry.get('DriverNumber')) == '44':
                                ham_lap_data.append({
                                    'timestamp': entry.get('Timestamp'),
                                    'lap': entry.get('LapNumber'),
                                    'status': entry.get('Status')
                                })
                
                if ham_lap_data:
                    logger.info("[4] HAM position samples (first 5):")
                    for data in ham_lap_data[:5]:
                        logger.info("    Lap %s: %s", data.get('lap', 'N/A'), data)
                
    else:
        logger.error("Position.z not available (HTTP %s)", pos_response.status_code)
        
except Exception as e:
    logger.exception("Failed to download Position.z: %s", e)

logger.info("%s", "=" * 70)
logger.info("Comparison Complete!")
logger.info("%s", "=" * 70)

logger.info(
        "SUMMARY:\n--------\nfastf1 優勢:\n"
        "  ✓ 自動整合 CarData + Position + Timing\n"
        "  ✓ 圈數已對應好,直接取 Lap 10\n"
        "  ✓ Lap 10 有 %s 個資料點\n"
        "  ✓ DataFrame 格式,易於分析",
        len(speed_10) if 'speed_10' in locals() else 'N/A',
)
  ✓ 需手動整合多個資料源
  ✓ CarData.z 無圈數,需配合 Position.z
  ✓ 時間戳對齊較複雜
  ✓ 但可完整控制處理流程

建議: 若只需分析,用 fastf1; 若要學習協定或即時應用,用 LiveTiming
""")
