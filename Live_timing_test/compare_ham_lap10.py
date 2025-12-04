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

def decode_f1_packet(raw_b64_string):
    """解碼 F1 壓縮封包"""
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except:
        return None

print("="*70)
print("HAM (Hamilton) Lap 10 Speed Data Comparison")
print("="*70)

# ========== Part 1: LiveTiming 原始資料 ==========
print("\n[Part 1] LiveTiming Raw Data Analysis")
print("-"*70)

url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/CarData.z.jsonStream"
print(f"[1] Downloading CarData...")
response = requests.get(url, timeout=60)
content = response.content

# 解析
text = content.decode('utf-8-sig')
lines = text.split('\r\n')
lines = [line for line in lines if line.strip()]

print(f"[2] Parsing {len(lines)} records...")

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

print(f"[3] HAM total speed readings: {len(ham_speed_data)}")

# 顯示前幾筆
print(f"\n[4] Sample data (first 5):")
for i, data in enumerate(ham_speed_data[:5]):
    print(f"    {i+1}. {data['timestamp']} | Speed: {data['speed']:3} km/h")

# ========== Part 2: fastf1 資料 ==========
print(f"\n\n[Part 2] fastf1 Processed Data Analysis")
print("-"*70)

print(f"[1] Loading session with fastf1...")
fastf1.Cache.enable_cache('f1_analysis_cache')
session = fastf1.get_session(2025, 'Japan', 'R')

print(f"[2] Loading telemetry data...")
session.load()

# 取得 Hamilton 的資料
print(f"[3] Filtering Hamilton's data...")
ham_laps = session.laps.pick_driver('HAM')

if len(ham_laps) == 0:
    print("[ERROR] Hamilton not found in session!")
    print("Available drivers:")
    for driver in session.drivers:
        print(f"  - {driver}")
    exit(1)

print(f"    Total laps: {len(ham_laps)}")

# 取得第 10 圈
if len(ham_laps) < 10:
    print(f"[ERROR] Only {len(ham_laps)} laps available, cannot get lap 10")
    exit(1)

lap_10 = ham_laps.iloc[9]  # Index 9 = Lap 10
print(f"\n[4] Lap 10 info:")
print(f"    Lap Time: {lap_10['LapTime']}")
print(f"    Lap Start: {lap_10['LapStartTime']}")

# 取得第10圈的遙測資料
telemetry_10 = lap_10.get_telemetry()
speed_10 = telemetry_10['Speed']

print(f"\n[5] Lap 10 telemetry:")
print(f"    Total data points: {len(telemetry_10)}")
print(f"    Speed readings: {len(speed_10)}")
print(f"    Speed range: {speed_10.min():.0f} - {speed_10.max():.0f} km/h")

# 顯示前幾筆
print(f"\n[6] Sample telemetry (first 5):")
for i in range(min(5, len(speed_10))):
    row = telemetry_10.iloc[i]
    print(f"    {i+1}. Time: {row['Time']} | Speed: {row['Speed']:.0f} km/h | RPM: {row['RPM']:.0f}")

# ========== Part 3: 詳細比較 ==========
print(f"\n\n[Part 3] Detailed Comparison")
print("="*70)

print(f"\n+------------------------+------------------+------------------+")
print(f"|      Metric            |   LiveTiming     |     fastf1       |")
print(f"+------------------------+------------------+------------------+")
print(f"| HAM Total Readings     | {len(ham_speed_data):>16} | N/A (all laps)   |")
print(f"| Lap 10 Readings        | (需手動過濾)     | {len(speed_10):>16} |")
print(f"| Data Format            | JSON (nested)    | DataFrame        |")
print(f"| Timestamp Type         | String           | Timedelta        |")
print(f"| Speed Filter           | Manual           | Auto (valid)     |")
print(f"+------------------------+------------------+------------------+")

# 嘗試從 LiveTiming 提取第10圈資料 (需要圈數資訊)
print(f"\n[NOTE] LiveTiming 的 CarData.z 不包含圈數資訊!")
print(f"       需要額外下載 TimingData 或 Position 來對應圈數。")

print(f"\n[4] Key Findings:")
print(f"  1. LiveTiming CarData.z 只包含遙測,無圈數標記")
print(f"  2. fastf1 已整合多個資料源,自動對應圈數")
print(f"  3. fastf1 的 Lap 10 有 {len(speed_10)} 個速度資料點")
print(f"  4. 要從 LiveTiming 取得相同資料,需要:")
print(f"     a. 下載 TimingData.jsonStream (圈數資訊)")
print(f"     b. 下載 Position.z.jsonStream (GPS + 圈數)")
print(f"     c. 時間戳對齊 CarData 與 Position")

# ========== Part 4: 下載 Position 資料嘗試對應 ==========
print(f"\n\n[Part 4] Attempting to get lap data from Position.z")
print("-"*70)

position_url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/Position.z.jsonStream"
print(f"[1] Downloading Position.z...")

try:
    pos_response = requests.get(position_url, timeout=60)
    if pos_response.status_code == 200:
        pos_content = pos_response.content
        pos_text = pos_content.decode('utf-8-sig')
        pos_lines = pos_text.split('\r\n')
        pos_lines = [line for line in pos_lines if line.strip()]
        
        print(f"[2] Position records: {len(pos_lines)}")
        
        # 解析第一筆看結構
        if pos_lines:
            first_pos = decode_f1_packet(pos_lines[0][12:])
            if first_pos:
                print(f"\n[3] Position data structure:")
                print(f"    Keys: {list(first_pos.keys())}")
                
                if 'Position' in first_pos:
                    positions = first_pos['Position']
                    if isinstance(positions, list) and len(positions) > 0:
                        sample = positions[0]
                        print(f"    Sample entry: {sample}")
                        
                        # 檢查是否有圈數資訊
                        if 'Entries' in sample:
                            print(f"    Has 'Entries' field")
                        
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
                    print(f"\n[4] HAM position samples (first 5):")
                    for data in ham_lap_data[:5]:
                        print(f"    Lap {data.get('lap', 'N/A')}: {data}")
                
    else:
        print(f"[ERROR] Position.z not available (HTTP {pos_response.status_code})")
        
except Exception as e:
    print(f"[ERROR] Failed to download Position.z: {e}")

print(f"\n\n{'='*70}")
print("Comparison Complete!")
print("="*70)

print(f"""
SUMMARY:
--------
fastf1 優勢:
  ✓ 自動整合 CarData + Position + Timing
  ✓ 圈數已對應好,直接取 Lap 10
  ✓ Lap 10 有 {len(speed_10) if 'speed_10' in locals() else 'N/A'} 個資料點
  ✓ DataFrame 格式,易於分析

LiveTiming 原始資料:
  ✓ 需手動整合多個資料源
  ✓ CarData.z 無圈數,需配合 Position.z
  ✓ 時間戳對齊較複雜
  ✓ 但可完整控制處理流程

建議: 若只需分析,用 fastf1; 若要學習協定或即時應用,用 LiveTiming
""")
