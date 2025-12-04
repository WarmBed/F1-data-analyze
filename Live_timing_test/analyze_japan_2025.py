"""
F1 Live Timing Data Analyzer - 2025 Japan (Fixed)
Correct parsing for CarData.z.jsonStream format
"""
import requests
import json
import base64
import zlib
from collections import Counter

def decode_f1_packet(raw_b64_string):
    """Decode F1 compressed packet"""
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        return None

# Download
print("="*60)
print("F1 Live Timing - 2025 Japan CarData Analysis")
print("="*60)

url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/CarData.z.jsonStream"
print(f"\n[1] Downloading from:")
print(f"    {url}")

response = requests.get(url, timeout=60)
content = response.content
size_mb = len(content) / 1024 / 1024
print(f"[OK] Downloaded {size_mb:.2f} MB")

# Parse
print(f"\n[2] Parsing .jsonStream format...")
text = content.decode('utf-8-sig')
lines = text.split('\r\n')
lines = [line for line in lines if line.strip()]
print(f"[OK] Total lines: {len(lines)}")

# Decode all records
print(f"\n[3] Decoding compressed data...")
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

print(f"[OK] Decoded {len(decoded_records)} records")
print(f"     Errors: {decode_errors}")

# Analyze
print(f"\n[4] Data Structure Analysis:")
print(f"=" * 60)

if decoded_records:
    first = decoded_records[0]['data']
    print(f"\nSample record structure:")
    print(f"  Timestamp: {decoded_records[0]['timestamp']}")
    print(f"  Keys: {list(first.keys())}")
    
    if 'Entries' in first and len(first['Entries']) > 0:
        entry = first['Entries'][0]
        print(f"\n  Entry structure:")
        print(f"    Utc: {entry.get('Utc', 'N/A')}")
        print(f"    Cars: {list(entry.get('Cars', {}).keys())[:5]}...")
        
        # Show one car's data
        cars = entry.get('Cars', {})
        if cars:
            car_num = list(cars.keys())[0]
            car_data = cars[car_num]
            channels = car_data.get('Channels', {})
            
            print(f"\n  Car {car_num} channels:")
            for ch_id, value in list(channels.items())[:5]:
                print(f"    Channel {ch_id}: {value}")

# Speed analysis
print(f"\n[5] Speed Data Analysis:")
print(f"=" * 60)

if speed_data:
    print(f"\nTotal speed readings: {len(speed_data)}")
    print(f"Min speed: {min(speed_data)} km/h")
    print(f"Max speed: {max(speed_data)} km/h")
    print(f"Avg speed: {sum(speed_data)/len(speed_data):.1f} km/h")
    
    # Distribution
    print(f"\nSpeed distribution (bins):")
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
        print(f"  {bin_name:>10} km/h: {bar:20} {count:6} ({pct:5.1f}%)")

# Channel mapping
print(f"\n[6] Channel Mapping (F1 Standard):")
print(f"=" * 60)
print(f"""
  Channel 0:  Speed (km/h)
  Channel 2:  RPM
  Channel 3:  nGear (gear number)
  Channel 4:  Throttle (0-100%)
  Channel 5:  Brake (boolean)
  Channel 45: DRS (0-14 range)
""")

# Comparison
print(f"\n[7] Comparison: LiveTiming vs fastf1")
print(f"=" * 60)

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
print(comparison)

print(f"\n[8] Key Findings:")
print(f"=" * 60)
print(f"""
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
""")

print(f"\n{'='*60}")
print("Analysis Complete!")
print("="*60)
