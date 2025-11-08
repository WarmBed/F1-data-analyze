import json

with open('2025_f1_parts_changes_classified.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

unclassified = [r for r in data if r['變更類型'] == '未分類 (Unclassified)']

print(f"剩餘未分類: {len(unclassified)} 筆\n")

for i, r in enumerate(unclassified, 1):
    print(f"{i:2}. [{r['車隊']:20s}] {r['部件']}")
    
# 分析為何 brake calipers 沒被分類
print("\n檢查 'brake caliper' 關鍵字:")
brake_calipers = [r for r in unclassified if 'caliper' in r['部件'].lower()]
print(f"包含 'caliper' 的未分類: {len(brake_calipers)} 筆")
for r in brake_calipers[:3]:
    print(f"  - {r['部件']}")
    print(f"    小寫: {r['部件'].lower()}")
    
# 檢查 seat belts
print("\n檢查 'seat belt' 關鍵字:")
seat_belts = [r for r in unclassified if 'belt' in r['部件'].lower()]
print(f"包含 'belt' 的未分類: {len(seat_belts)} 筆")
for r in seat_belts:
    print(f"  - {r['部件']}")
    print(f"    小寫: {r['部件'].lower()}")
