"""
F1 Live Timing Data Analyzer - 2025 Japan (Fixed)
Correct parsing for CarData.z.jsonStream format
"""
import requests
import json
import base64
import zlib
from collections import Counter

from core.logger import get_logger


logger = get_logger(component="gui")

def decode_f1_packet(raw_b64_string):
    """Decode F1 compressed packet"""
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        return None

# Download
logger.info("=" * 60)
logger.info("F1 Live Timing - 2025 Japan CarData Analysis")
logger.info("=" * 60)

url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/CarData.z.jsonStream"
logger.info("\n[1] Downloading from:")
logger.info(f"    {url}")

response = requests.get(url, timeout=60)
content = response.content
size_mb = len(content) / 1024 / 1024
logger.info(f"[OK] Downloaded {size_mb:.2f} MB")

# Parse
logger.info("\n[2] Parsing .jsonStream format...")
text = content.decode('utf-8-sig')
lines = text.split('\r\n')
lines = [line for line in lines if line.strip()]
logger.info(f"[OK] Total lines: {len(lines)}")

# Decode all records
logger.info("\n[3] Decoding compressed data...")
decoded_records = []
decode_errors = 0
speed_data = []

for i, line in enumerate(lines):
    if len(line) < 12:
        continue
    
    timestamp = line[:12]
    b64_data = line[12:]
    
    # Decode
    decoded = decode_f1_packet(b64_data)
    if decoded:
        decoded_records.append({
            'timestamp': timestamp,
            'data': decoded
        })
        
        # Extract speed data
        if 'Entries' in decoded:
            for entry in decoded['Entries']:
                cars = entry.get('Cars', {})
                for car_num, car_data in cars.items():
                    channels = car_data.get('Channels', {})
                    speed = channels.get('0')  # Channel 0 is Speed
                    if speed is not None:
                        speed_data.append(speed)
    else:
        decode_errors += 1

logger.info(f"[OK] Decoded {len(decoded_records)} records")
logger.info(f"     Errors: {decode_errors}")

# Analyze
logger.info("\n[4] Data Structure Analysis:")
logger.info("=" * 60)

if decoded_records:
    first = decoded_records[0]['data']
    logger.info("\nSample record structure:")
    logger.info(f"  Timestamp: {decoded_records[0]['timestamp']}")
    logger.info(f"  Keys: {list(first.keys())}")
    
    if 'Entries' in first and len(first['Entries']) > 0:
        entry = first['Entries'][0]
        logger.info("\n  Entry structure:")
        logger.info(f"    Utc: {entry.get('Utc', 'N/A')}")
        logger.info(f"    Cars: {list(entry.get('Cars', {}).keys())[:5]}...")
        
        # Show one car's data
        cars = entry.get('Cars', {})
        if cars:
            car_num = list(cars.keys())[0]
            car_data = cars[car_num]
            channels = car_data.get('Channels', {})
            
            logger.info(f"\n  Car {car_num} channels:")
            for ch_id, value in list(channels.items())[:5]:
                logger.info(f"    Channel {ch_id}: {value}")

# Speed analysis
logger.info("\n[5] Speed Data Analysis:")
logger.info("=" * 60)

if speed_data:
    logger.info(f"\nTotal speed readings: {len(speed_data)}")
    logger.info(f"Min speed: {min(speed_data)} km/h")
    logger.info(f"Max speed: {max(speed_data)} km/h")
    logger.info(f"Avg speed: {sum(speed_data)/len(speed_data):.1f} km/h")
    
    # Distribution
    logger.info("\nSpeed distribution (bins):")
    bins = [0, 50, 100, 150, 200, 250, 300, 350, 400]
    counts = Counter()
    for speed in speed_data:
        for i in range(len(bins)-1):
            if bins[i] <= speed < bins[i+1]:
                counts[f"{bins[i]}-{bins[i+1]}"] += 1
                break
    
    for bin_name in [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]:
        count = counts.get(bin_name, 0)
        pct = (count / len(speed_data) * 100) if speed_data else 0
        bar = '#' * int(pct / 2)
        logger.info(f"  {bin_name:>10} km/h: {bar:20} {count:6} ({pct:5.1f}%)")

# Channel mapping
logger.info("\n[6] Channel Mapping (F1 Standard):")
logger.info("=" * 60)
logger.info(
        """
    Channel 0:  Speed (km/h)
    Channel 2:  RPM
    Channel 3:  nGear (gear number)
    Channel 4:  Throttle (0-100%)
    Channel 5:  Brake (boolean)
    Channel 45: DRS (0-14 range)
"""
)

# Comparison
logger.info("\n[7] Comparison: LiveTiming vs fastf1")
logger.info("=" * 60)

comparison = f"""
+-------------------------+---------------------------+---------------------------+
|        Aspect           |   LiveTiming (Raw)        |   fastf1 (Processed)      |
+-------------------------+---------------------------+---------------------------+
| File Format             | .jsonStream               | Pandas DataFrame          |
| Compression             | Base64 + Zlib (wbits=-15)| Pre-decompressed          |
| Total Records           | {len(lines):,} lines              | ~Same (after parsing)     |
| File Size               | {size_mb:.2f} MB                  | Varies (CSV/pickle)       |
| Speed Data Points       | {len(speed_data):,}                   | ~Same                     |
| Data Structure          | Nested JSON               | Tabular columns           |
| Timestamp Format        | 'HH:MM:SS.mmm'            | Timedelta / datetime      |
|Channel Access           | dict['Channels']['0']     | df['Speed']               |
| Parsing Required        | Yes (decode + extract)    | No (ready to use)         |
| Memory Efficient        | No (must load all)        | Yes (chunked reading)     |
+-------------------------+---------------------------+---------------------------+
"""
logger.info(comparison)

logger.info("\n[8] Key Findings:")
logger.info("=" * 60)
logger.info(
    f"""
1. Raw Format: jsonStream uses timestamp + Base64 encoded data per line
2. Compression: MUST use wbits=-15 for Zlib (raw deflate, no header)
3. Data Volume: ~{len(speed_data):,} speed readings in {len(lines):,} records
4. Max Speed: {max(speed_data) if speed_data else 0} km/h at Suzuka
5. Structure: Each record contains multiple cars' telemetry at one timestamp

fastf1 Advantage:
- Already decoded and tabular
- Easy column access (df['Speed'])
- Time-series aligned
- Pandas operations (groupby, resample, etc.)

Raw LiveTiming Advantage:
- Direct from source (no middleman)
- Can implement custom processing
- Learning SignalR protocol
- Real-time capable (WebSocket)
"""
)

logger.info("\n" + "=" * 60)
logger.info("Analysis Complete!")
logger.info("=" * 60)
