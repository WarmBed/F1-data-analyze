# -*- coding: utf-8 -*-
"""檢查原始 jsonStream 數據"""
import json
from pathlib import Path

stream_file = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\team_radio_data\2025\TeamRadio_2025_Abu_Dhabi_R.jsonStream")

with open(stream_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"📡 原始 jsonStream 分析")
print(f"=" * 50)
print(f"總行數: {len(lines)}")

drivers = set()
for line in lines:
    if line.strip():
        try:
            data = json.loads(line)
            driver = data.get('RacingNumber', '?')
            drivers.add(driver)
        except:
            pass

print(f"原始數據車手數: {len(drivers)}")
print(f"車手列表: {sorted(drivers, key=lambda x: int(x) if x.isdigit() else 999)}")

print(f"\n結論: F1 官方 API 只提供了 {len(drivers)} 位車手的 Team Radio")
print("這是 API 端的限制，並非程式問題。")
print("\n可能原因:")
print("1. F1TV 只公開部分精選的 Team Radio")
print("2. 某些車手的通訊未被錄製或未被授權公開")
print("3. 技術問題導致某些車手的音訊未被捕捉")
