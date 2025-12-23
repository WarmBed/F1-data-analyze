#!/usr/bin/env python3
"""檢查 Unknown 車隊/車手記錄"""
import json

# 載入主要升級數據
with open('2025_f1_major_upgrades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找出所有 Unknown 記錄
unknown_records = [
    r for r in data['主要部件升級記錄'] 
    if r['車隊'] == 'Unknown' or r['車手'] == 'Unknown'
]

print("="*100)
print(f"🔍 找到 {len(unknown_records)} 筆 Unknown 記錄")
print("="*100)
print(f"{'車號':<6} {'車隊':<20} {'車手':<25} {'比賽':<18} {'部件':<40}")
print("="*100)

for r in unknown_records:
    print(f"{r['車號']:<6} {r['車隊']:<20} {r['車手']:<25} {r['比賽']:<18} {r['部件'][:40]:<40}")

print("="*100)

# 分析車號分佈
car_numbers = {}
for r in unknown_records:
    car_num = r['車號']
    car_numbers[car_num] = car_numbers.get(car_num, 0) + 1

print(f"\n📊 Unknown 記錄的車號分佈:")
for car_num, count in sorted(car_numbers.items()):
    print(f"  車號 {car_num}: {count} 次")

# 檢查原始完整數據
print("\n" + "="*100)
print("🔍 檢查原始完整數據中的相同車號...")
print("="*100)

with open('2025_f1_parts_changes_complete.json', 'r', encoding='utf-8') as f:
    all_changes = json.load(f)

for car_num in car_numbers.keys():
    matching = [r for r in all_changes if r['車號'] == car_num]
    if matching:
        sample = matching[0]
        print(f"\n車號 {car_num}:")
        print(f"  原始記錄: 車隊={sample['車隊']}, 車手={sample['車手']}")
        print(f"  來源文件: {sample['來源文件']}")
        print(f"  原始文本: {sample['原始文本'][:80]}")
