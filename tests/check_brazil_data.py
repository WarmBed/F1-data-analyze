import json

data = json.load(open('2025_f1_parts_changes_classified.json', encoding='utf-8'))
brazil = [r for r in data if r.get('賽事') == 'Brazil']

print(f'Brazil 記錄數: {len(brazil)}')
print(f'\n前 5 筆 Brazil 記錄:')
for r in brazil[:5]:
    print(f'  車隊={r.get("車隊")}, 車手={r.get("車手")}, 部件={r.get("部件")[:50]}...')
