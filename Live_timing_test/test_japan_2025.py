"""
F1 Live Timing Data Downloader - 2025 Japan
Pure ASCII version for Windows console
"""
import requests
import json
import base64
import zlib

def decode_f1_packet(raw_b64_string):
    """Decode F1 compressed packet"""
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        return None

# Get 2025 Index
print("="*60)
print("F1 Live Timing - 2025 Japan Analysis")
print("="*60)
print("\n[1] Fetching 2025 season index...")
url = "https://livetiming.formula1.com/static/2025/Index.json"
response = requests.get(url, timeout=30)
text = response.content.decode('utf-8-sig')
index = json.loads(text)
print(f"[OK] Found {len(index.get('Meetings', []))} races")

# Find Japan
meetings = index.get('Meetings', [])
japan = None
for meeting in meetings:
    if 'Japan' in meeting.get('Name', '') or 'Suzuka' in meeting.get('Location', ''):
        japan = meeting
        break

if not japan:
    print("[ERROR] Japan not found!")
    exit(1)

print(f"\n[2] Found Japan Grand Prix")
print(f"    Official Name: {japan.get('OfficialName', 'N/A')}")
print(f"    Location: {japan.get('Location', 'N/A')}")
print(f"    Race Date: 2025-04-06")

# Find Race session
race_session = None
for session in japan.get('Sessions', []):
    if session.get('Type') == 'Race':
        race_session = session
        break

if not race_session:
    print("[ERROR] Race session not found!")
    exit(1)

session_path = race_session.get('Path', '')
print(f"\n[3] Race Session Path: {session_path}")

# Download CarData
cardata_url = f"https://livetiming.formula1.com/static/{session_path}CarData.z.jsonStream"
print(f"\n[4] Downloading CarData...")
print(f"    URL: {cardata_url}")

try:
    response = requests.get(cardata_url, timeout=60)
    if response.status_code == 404:
        print("[WARN] CarData not found (404) - Race may not have occurred yet")
        print("       Trying to download Index.json from session instead...")
        
        # Try session index
        index_url = f"https://livetiming.formula1.com/static/{session_path}Index.json"
        print(f"       URL: {index_url}")
        response2 = requests.get(index_url, timeout=30)
        
        if response2.status_code == 200:
            print("[OK]   Session Index found!")
            text = response2.content.decode('utf-8-sig')
            session_index = json.loads(text)
            print(f"\n[5] Available data feeds:")
            for feed in session_index.get('Feeds', {}).keys():
                print(f"    - {feed}")
        else:
            print(f"[ERROR] Session not available yet (HTTP {response2.status_code})")
        exit(0)
    
    response.raise_for_status()
    content = response.content
    size_mb = len(content) / 1024 / 1024
    print(f"[OK]   Downloaded {size_mb:.2f} MB")
    
    # Parse jsonStream
    print(f"\n[5] Parsing .jsonStream format...")
    text = content.decode('utf-8-sig')
    lines = text.split('\r\n')
    lines = [line for line in lines if line.strip()]
    print(f"[OK]   Total lines: {len(lines)}")
    
    # Parse first few records
    print(f"\n[6] Analyzing data structure (first 3 records):\n")
    for i, line in enumerate(lines[:3]):
        if len(line) < 12:
            continue
        
        timestamp = line[:12]
        json_data = line[12:]
        
        try:
            data = json.loads(json_data)
            print(f"Record {i+1}:")
            print(f"  Timestamp: {timestamp}")
            print(f"  Type: {type(data).__name__}")
            
            # Check if compressed
            if 'M' in data:
                print(f"  Format: SignalR message")
                messages = data.get('M', [])
                if messages and len(messages) > 0:
                    msg = messages[0]
                    print(f"  Method: {msg.get('M', 'N/A')}")
                    
                    # Try decode
                    args = msg.get('A', [])
                    if args and isinstance(args[0], str):
                        decoded = decode_f1_packet(args[0])
                        if decoded:
                            print(f"  Decoded: {str(decoded)[:150]}...")
                            
                            # Count entries
                            if 'Entries' in decoded:
                                print(f"  Entry count: {len(decoded['Entries'])}")
            else:
                print(f"  Format: Direct JSON")
                print(f"  Keys: {list(data.keys())[:5]}")
            
            print()
        except Exception as e:
            print(f"  [ERROR] Parse failed: {e}\n")
    
    print(f"\n[7] Summary:")
    print(f"  Total records: {len(lines)}")
    print(f"  File size: {size_mb:.2f} MB")
    print(f"  Format: jsonStream (timestamp + JSON per line)")
    
    print(f"\n[8] Comparison with fastf1:")
    print(f"  LiveTiming raw:")
    print(f"    - Format: .jsonStream (line-by-line)")
    print(f"    - Compression: Base64 + Zlib")
    print(f"    - Structure: SignalR protocol wrapped")
    print(f"  fastf1 processed:")
    print(f"    - Format: Pandas DataFrame")
    print(f"    - Compression: Already decompressed")
    print(f"    - Structure: Tabular, time-aligned")
    
    print(f"\n{'='*60}")
    print("Analysis complete!")
    print("="*60)
    
except Exception as e:
    print(f"[ERROR] {e}")
