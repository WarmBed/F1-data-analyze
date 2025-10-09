"""調試 payload 結構"""
import json
from pathlib import Path

# 載入最新的 JSON
json_files = list(Path('json').glob('season_calendar_*.json'))
latest = max(json_files, key=lambda p: p.stat().st_mtime)
print(f"檔案: {latest.name}\n")

payload = json.load(open(latest, 'r', encoding='utf-8'))

# 顯示結構
print("📋 Payload 頂層 keys:")
for k in payload.keys():
    print(f"   - {k}: {type(payload[k]).__name__}")

print("\n📋 payload['data'] keys:")
if 'data' in payload:
    data = payload['data']
    for k in data.keys():
        print(f"   - {k}: {type(data[k]).__name__}")
        
    # 檢查是否有雙層 data
    if 'data' in data:
        print("\n⚠️  發現雙層 'data'！")
        print("📋 payload['data']['data'] keys:")
        inner = data['data']
        for k in inner.keys():
            print(f"   - {k}: {type(inner[k]).__name__}")

# 查找年份 keys
print("\n🔍 尋找年份數據...")
def find_year_data(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).isdigit() and len(str(k)) == 4:
                print(f"✅ 找到年份 key: {path}.{k}")
                return
            find_year_data(v, f"{path}.{k}")
    elif isinstance(obj, list) and len(obj) > 0:
        print(f"   {path}: list[{len(obj)}]")

find_year_data(payload, "payload")
