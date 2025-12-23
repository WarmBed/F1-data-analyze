#!/usr/bin/env python3
"""檢查 Function 100 JSON 格式"""
import json
from pathlib import Path

json_file = Path('json/historical_flags_Japan_2022-2025.json')
with open(json_file, 'r', encoding='utf-8') as f:
    d = json.load(f)

print("=== 頂層鍵 ===")
print(list(d.keys()))

print("\n=== data 層級 ===")
data = d['data']
print("data 的鍵:", list(data.keys()))

print("\n=== Position Records ===")
pr = data.get('detailed_position_records', [])
print(f"數量: {len(pr)}")
if pr:
    print(f"第一個點的鍵: {list(pr[0].keys())}")
    print(f"Has speed: {'speed' in pr[0]}")
    if 'speed' in pr[0]:
        print(f"Speed 值: {pr[0]['speed']}")

print("\n=== Corner Analysis ===")
ca = data.get('corner_analysis', {})
print(f"彎道數: {len(ca)}")
print(f"前3個彎道: {list(ca.keys())[:3]}")

print("\n=== TrackMapWidget 的 set_corner_flags 需要的格式 ===")
print("Demo 調用: self.track_map.set_corner_flags(corner_analysis)")
print(f"corner_analysis 類型: {type(ca)}")
if ca:
    first_corner = list(ca.keys())[0]
    print(f"第一個彎道 ({first_corner}) 的鍵: {list(ca[first_corner].keys())}")
