"""檢查 Position.z 的數據結構"""
import requests
import base64
import zlib
import json

url = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/Position.z.jsonStream"

print("下載 Position.z...")
response = requests.get(url, timeout=60)
content = response.content.decode('utf-8-sig')
lines = content.split('\r\n')
lines = [line for line in lines if line.strip()]

print(f"總共 {len(lines)} 行\n")

# 檢查前 3 個記錄
for i in range(min(3, len(lines))):
    line = lines[i]
    timestamp = line[:12]
    data_str = line[12:]
    
    # 解碼
    decoded_bytes = base64.b64decode(data_str)
    decompressed = zlib.decompress(decoded_bytes, wbits=-15)
    obj = json.loads(decompressed)
    
    print(f"=== 記錄 {i+1} ===")
    print(f"時間戳: {timestamp}")
    print(f"數據類型: {type(obj)}")
    print(f"數據鍵: {obj.keys() if isinstance(obj, dict) else 'N/A'}")
    
    if 'Position' in obj:
        print(f"Position 類型: {type(obj['Position'])}")
        
        if isinstance(obj['Position'], list):
            print(f"Position 列表長度: {len(obj['Position'])}")
            if obj['Position']:
                print(f"第一個元素: {json.dumps(obj['Position'][0], indent=2)[:200]}...")
        elif isinstance(obj['Position'], dict):
            print(f"Position 字典鍵數量: {len(obj['Position'])}")
            first_key = list(obj['Position'].keys())[0]
            print(f"第一個鍵: {first_key}")
            print(f"第一個值: {json.dumps(obj['Position'][first_key], indent=2)[:200]}...")
    
    print()
