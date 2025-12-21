"""
解析 JSONL 錄製檔案中的 CarData.z
"""
import json
import base64
import zlib
import sys

def decode_compressed(data: str) -> dict:
    """解碼 base64 + zlib 壓縮的數據"""
    if data.startswith('{'):
        return json.loads(data)
    if data.startswith('"'):
        data = data.strip('"')
    
    decoded = base64.b64decode(data)
    decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
    return json.loads(decompressed.decode('utf-8-sig'))

def main():
    jsonl_path = sys.argv[1] if len(sys.argv) > 1 else "data/live_timing_recordings/raw_20251207_221251.jsonl"
    
    print(f"Parsing: {jsonl_path}")
    print("=" * 60)
    
    cardata_count = 0
    position_count = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            data = json.loads(line)
            raw = json.loads(data['raw'])
            messages = raw.get('M', [])
            
            for msg in messages:
                args = msg.get('A', [])
                if not args or len(args) < 2:
                    continue
                
                topic = args[0]
                payload = args[1]
                
                if topic == 'CarData.z' and cardata_count < 3:
                    cardata_count += 1
                    print(f"\n=== CarData.z #{cardata_count} (seq {data['seq']}) ===")
                    print(f"Timestamp: {args[2] if len(args) > 2 else 'N/A'}")
                    print(f"Raw (first 100 chars): {str(payload)[:100]}...")
                    
                    try:
                        decoded = decode_compressed(payload)
                        print(f"Decoded structure:")
                        print(json.dumps(decoded, indent=2)[:1500])
                    except Exception as e:
                        print(f"Decode error: {e}")
                
                elif topic == 'Position.z' and position_count < 2:
                    position_count += 1
                    print(f"\n=== Position.z #{position_count} (seq {data['seq']}) ===")
                    print(f"Timestamp: {args[2] if len(args) > 2 else 'N/A'}")
                    
                    try:
                        decoded = decode_compressed(payload)
                        print(f"Decoded structure:")
                        print(json.dumps(decoded, indent=2)[:1500])
                    except Exception as e:
                        print(f"Decode error: {e}")
            
            # 找到足夠樣本後停止
            if cardata_count >= 3 and position_count >= 2:
                break
    
    print("\n" + "=" * 60)
    print(f"Found {cardata_count} CarData.z samples, {position_count} Position.z samples")

if __name__ == "__main__":
    main()
