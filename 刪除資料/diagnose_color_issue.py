#!/usr/bin/env python3
"""
診斷腳本：調查顏色配置 API 處理問題
"""

import json
import sys
from pathlib import Path

# API 返回的實際數據（從附件中提取）
api_response = {
    "success": True,
    "data": {
        "teams": {
            "alpine": {"team_name": "Alpine", "selected_hex": "#FF87BC"},
            "ferrari": {"team_name": "Ferrari", "selected_hex": "#E80020"},
        },
        "drivers": {
            "PIA": {"full_name": "Oscar Piastri", "team_slug": "mclaren", "hex": "#FF8000"},
            "NOR": {"full_name": "Lando Norris", "team_slug": "mclaren", "hex": "#FF8000"},
        }
    }
}

print("="*70)
print("診斷：ColorPaletteProvider 數據處理流程")
print("="*70)

# 模擬 _apply_payload 的處理邏輯
payload = api_response
data = payload.get("data") or {}
teams = data.get("teams") or {}
drivers = data.get("drivers") or {}

print(f"\n📊 API 回應分析:")
print(f"  payload.get('data'): {type(data)} - {bool(data)}")
print(f"  data.get('teams'): {type(teams)} - 包含 {len(teams)} 個車隊")
print(f"  data.get('drivers'): {type(drivers)} - 包含 {len(drivers)} 個車手")

print(f"\n🔍 處理車手數據:")
driver_palette = {}
processed_count = 0
skipped_count = 0

for code, info in drivers.items():
    code_norm = str(code or "").strip().upper()  # _normalize_driver_code
    hex_value = str(info.get("hex") or "").strip()
    
    print(f"\n  處理車手: {code}")
    print(f"    - code_norm: {code_norm}")
    print(f"    - hex_value: {hex_value}")
    print(f"    - info.get('hex'): {info.get('hex')}")
    
    if not hex_value:
        print(f"    ⚠️  hex 為空，嘗試從車隊回退")
        team_slug = str(info.get("team_slug") or "").strip().lower()
        print(f"    - team_slug: {team_slug}")
        team_entry = teams.get(team_slug)
        print(f"    - team_entry: {team_entry}")
        if team_entry:
            hex_value = team_entry.get("selected_hex")
            print(f"    ✅ 從車隊獲取顏色: {hex_value}")
        else:
            print(f"    ❌ 找不到車隊，跳過此車手")
            skipped_count += 1
            continue
    
    driver_palette[code_norm] = {
        "hex": hex_value,
        "full_name": info.get("full_name") or code_norm,
    }
    processed_count += 1
    print(f"    ✅ 成功處理")

print(f"\n📋 處理結果:")
print(f"  成功處理: {processed_count} 個車手")
print(f"  跳過: {skipped_count} 個車手")
print(f"  driver_palette 大小: {len(driver_palette)}")

print(f"\n🔍 關鍵檢查:")
if not driver_palette:
    print("  ❌ driver_palette 為空!")
    print("  ⚠️  將拋出異常: 'API payload did not contain driver colour information'")
else:
    print(f"  ✅ driver_palette 包含 {len(driver_palette)} 個條目")

print("\n" + "="*70)
print("可能的問題原因:")
print("="*70)
print("1. team_slug 與 teams 鍵名不匹配（大小寫問題）")
print("2. 所有車手的 hex 都為空且無法從車隊回退")
print("3. API 返回的 drivers 結構與預期不符")
print("="*70 + "\n")
