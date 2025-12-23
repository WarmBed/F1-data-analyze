import json

# 讀取 JSON 文件
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== JSON 結構深度分析 ===\n')

# 1. 頂層結構
print('1️⃣ JSON 頂層鍵:')
print('   ', list(data.keys()))
print()

# 2. data 層（API 返回的數據層）
api_data = data.get('data', data)
print('2️⃣ API 數據層鍵 (data):')
print('   ', list(api_data.keys()))
print()

# 3. track_data 是否存在
track_data = api_data.get('track_data')
print('3️⃣ track_data 檢查:')
print(f'    存在: {track_data is not None}')
if track_data:
    print(f'    鍵: {list(track_data.keys())}')
    print(f'    speed_distribution 在 track_data: {"speed_distribution" in track_data}')
else:
    print('    track_data = None 或不存在')
print()

# 4. speed_distribution 位置
print('4️⃣ speed_distribution 位置檢查:')
print(f'    在 api_data (data 層): {"speed_distribution" in api_data}')
if track_data:
    print(f'    在 track_data: {"speed_distribution" in track_data}')
print()

# 5. speed_distribution 內容
if 'speed_distribution' in api_data:
    print('5️⃣ speed_distribution 內容 (來自 api_data):')
    sd = api_data['speed_distribution']
    print(json.dumps(sd, indent=4, ensure_ascii=False))
elif track_data and 'speed_distribution' in track_data:
    print('5️⃣ speed_distribution 內容 (來自 track_data):')
    sd = track_data['speed_distribution']
    print(json.dumps(sd, indent=4, ensure_ascii=False))
else:
    print('⚠️  未找到 speed_distribution')

print('\n=== 結論 ===')
print(f'GUI 應該從: data["speed_distribution"] 讀取' if 'speed_distribution' in api_data else 'track_data["speed_distribution"] 讀取')
