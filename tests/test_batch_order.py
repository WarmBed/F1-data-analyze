#!/usr/bin/env python3
"""
測試腳本：驗證批次下載順序
"""

import sys
sys.path.insert(0, 'scripts')

from batch_f47_2025_to_mexico import get_2025_races

print("=" * 80)
print("批次下載順序測試")
print("=" * 80)
print()

races = get_2025_races()

print(f"總賽事數：{len(races)} 場")
print(f"總會話數：{sum(len(r['sessions']) for r in races)} 個")
print()
print("下載順序預覽（前 10 場）:")
print("-" * 80)

for i, race in enumerate(races[:10], 1):
    sessions_str = ", ".join(race["sessions"])
    print(f"{i:2d}. [R{race['round']:2d}] {race['name']:20s} - {sessions_str}")

print("    ...")
print()
print("下載順序預覽（後 3 場）:")
print("-" * 80)

for i, race in enumerate(races[-3:], len(races) - 2):
    sessions_str = ", ".join(race["sessions"])
    print(f"{i:2d}. [R{race['round']:2d}] {race['name']:20s} - {sessions_str}")

print()
print("✅ 順序驗證:")
print(f"  - 第一場：{races[0]['name']} (Round {races[0]['round']})")
print(f"  - 最後一場：{races[-1]['name']} (Round {races[-1]['round']})")
print()

if races[0]['name'] == 'Mexico' and races[0]['round'] == 20:
    print("✅ 正確！從墨西哥站 (R20) 開始")
else:
    print("❌ 錯誤！第一場應該是墨西哥站")

if races[-1]['name'] == 'Australia' and races[-1]['round'] == 1:
    print("✅ 正確！到澳洲站 (R1) 結束")
else:
    print("❌ 錯誤！最後一場應該是澳洲站")

print()
print("=" * 80)
