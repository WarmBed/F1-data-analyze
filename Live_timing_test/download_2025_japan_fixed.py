"""
F1 Live Timing ???????
??: 2025 ??(Suzuka) ??
"""
import requests
import json
import base64
import zlib
from datetime import datetime

def decode_f1_packet(raw_b64_string):
    """
    ? F1 ?
    ?: F1 ?
    """
    try:
        # 1. Base64 Decode
        decoded_bytes = base64.b64decode(raw_b64_string)
        # 2. Zlib Decompress (wbits=-15 ?!)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        # 3. Parse JSON
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        print(f"????: {e}")
        return None


def get_2025_index():
    """?? 2025 ??""
    url = "https://livetiming.formula1.com/static/2025/Index.json"
    print(f"[INFO] ? 2025 ??..")
    print(f"[URL]  {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # ?? UTF-8 BOM
        text = response.content.decode('utf-8-sig')
        data = json.loads(text)
        
        print(f"[OK]   ??! ? {len(data.get('Meetings', []))} ???)
        return data
    except Exception as e:
        print(f"[ERROR] ?: {e}")
        return None


def find_japan_meeting(index_data):
    """????""
    meetings = index_data.get('Meetings', [])
    
    print(f"\n[SEARCH] ????..")
    for meeting in meetings:
        name = meeting.get('Name', '')
        location = meeting.get('Location', '')
        
        if 'Japan' in name or 'Suzuka' in location or 'japan' in name.lower():
            print(f"[FOUND] {meeting}")
            return meeting
    
    print(f"[ERROR] ????")
    return None


def download_cardata(meeting_path, session_name='Race'):
    """
    ? CarData.z.jsonStream
    
    meeting_path ?: "2025-04-06_Japanese_Grand_Prix"
    """
    # ?
    year = "2025"
    # Session ???: YYYY-MM-DD_Session_Type
    date_prefix = meeting_path.split('_')[0]  # ??????
    session_path = f"{date_prefix}_{session_name}"
    
    url = f"https://livetiming.formula1.com/static/{year}/{meeting_path}/{session_path}/CarData.z.jsonStream"
    
    print(f"\n? ???...")
    print(f"?? URL: {url}")
    
    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        # ????
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_mb = int(content_length) / 1024 / 1024
            print(f"?? ??: {size_mb:.2f} MB")
        
        # ??
        content = response.content
        print(f"????! ??: {len(content) / 1024 / 1024:.2f} MB")
        
        return content
    except requests.exceptions.HTTPError as e:
        print(f"??HTTP ?: {e}")
        print(f"? ?: ??? (Race/Qualifying/Practice_1 ?")
        return None
    except Exception as e:
        print(f"????: {e}")
        return None


def parse_jsonstream(content):
    """
    ?? .jsonStream ??
    ??: ? = 12?????+ JSON?
    """
    print(f"\n? ?? jsonStream ??...")
    
    try:
        # ??( \r\n)
        text = content.decode('utf-8-sig')
        lines = text.split('\r\n')
        
        # ?
        lines = [line for line in lines if line.strip()]
        
        print(f"?? ??? {len(lines)}")
        
        # ????
        records = []
        for i, line in enumerate(lines):
            if len(line) < 12:
                continue
            
            # ??????
            timestamp = line[:12]
            json_data = line[12:]
            
            try:
                data = json.loads(json_data)
                records.append({
                    'timestamp': timestamp,
                    'data': data
                })
            except json.JSONDecodeError as e:
                if i < 5:  # ???
                    print(f"??  ?{i+1} ??? {e}")
        
        print(f"?????? {len(records)} ???)
        return records
    
    except Exception as e:
        print(f"?????: {e}")
        return []


def analyze_cardata_structure(records, max_samples=10):
    """?? CarData ?"""
    print(f"\n?? ????...")
    print(f"=" * 60)
    
    if not records:
        print("???????")
        return
    
    # ????
    print(f"\n??{max_samples} ????\n")
    for i, record in enumerate(records[:max_samples]):
        print(f"[{i+1}] ???? {record['timestamp']}")
        
        data = record['data']
        
        # ?
        if 'A' in data and isinstance(data['A'], list) and len(data['A']) > 0:
            # SignalR ??,???
            print(f"    ?: SignalR ")
            print(f"    ?: {str(data)[:200]}...")
            
            # ???
            for item in data['A']:
                if isinstance(item, str):
                    decoded = decode_f1_packet(item)
                    if decoded:
                        print(f"    ?? {str(decoded)[:200]}...")
                        break
        else:
            print(f"    ?: ? JSON")
            print(f"    ?: {str(data)[:200]}...")
        
        print()
    
    print(f"=" * 60)


def compare_with_fastf1():
    """???fastf1 ???""
    print(f"\n?? ??fastf1 ?????\n")
    print(f"LiveTiming API (??):")
    print(f"  - ??: .jsonStream (?? JSON)")
    print(f"  - : Base64 + Zlib (wbits=-15)")
    print(f"  - ?: SignalR ???")
    print(f"  - ?: ???? (Speed, RPM, nGear, Throttle, Brake)")
    print()
    print(f"fastf1 (???:")
    print(f"  - ??: Pandas DataFrame")
    print(f"  - : ")
    print(f"  - ?: ?????)
    print(f"  - ?: ????(Speed, RPM, nGear, Throttle, Brake, DRS ?")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("F1 Live Timing - 2025 ???????)
    print("=" * 60)
    
    # ? 1: ?? 2025 ?
    index = get_2025_index()
    
    if index:
        # ? 2: ???
        japan = find_japan_meeting(index)
        
        if japan:
            meeting_path = japan.get('Path', '')
            print(f"\n?? ??: {meeting_path}")
            
            # ? 3: ? CarData
            cardata = download_cardata(meeting_path, session_name='Race')
            
            if cardata:
                # ? 4: ???
                records = parse_jsonstream(cardata)
                
                # ? 5: ???
                analyze_cardata_structure(records, max_samples=5)
                
                # ? 6: ??fastf1 ?
                compare_with_fastf1()
                
                print(f"\n?????!")
            else:
                print(f"\n? ?: ???,??????)
                print(f"   ?????")
                print(f"   - Practice_1, Practice_2, Practice_3")
                print(f"   - Qualifying")
                print(f"   - Sprint (???")
    
    print(f"\n" + "=" * 60)
