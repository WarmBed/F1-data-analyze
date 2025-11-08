import json

# 讀取 2021 Bahrain JSON 檔案
with open('json/all_incidents_summary_2021_Bahrain_Grand_Prix_RACE.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找出所有 Safety Car 相關記錄
sc_records = [r for r in data.get('all_incidents', []) if 'SAFETY' in r.get('message', '').upper()]

print(f"找到 {len(sc_records)} 筆 Safety Car 相關記錄\n")
print("=" * 80)

# 檢查前 10 筆記錄的 sector 資訊
for i, record in enumerate(sc_records[:10], 1):
    lap = record.get('lap')
    message = record.get('message', '')
    sector = record.get('sector')
    category = record.get('category')
    
    print(f"\n記錄 {i}:")
    print(f"  圈數: {lap}")
    print(f"  分類: {category}")
    print(f"  Sector: {sector}")
    print(f"  訊息: {message}")

print("\n" + "=" * 80)
print("\n統計 Safety Car 事件的 Sector 分布:")
sectors_count = {}
for record in sc_records:
    sector = record.get('sector')
    sectors_count[sector] = sectors_count.get(sector, 0) + 1

for sector, count in sorted(sectors_count.items()):
    print(f"  Sector {sector}: {count} 次")
