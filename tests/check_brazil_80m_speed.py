#!/usr/bin/env python3
"""檢查 Brazil JSON 中 80m 附近的速度數據"""

import json

# 讀取 JSON 檔案
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    root_data = json.load(f)

# 提取實際數據（nested structure）
data = root_data.get('data', {})
print(f"Data keys: {list(data.keys())}\n")

# 獲取 detailed_position_records
records = data.get('detailed_position_records', [])
print(f"總共 {len(records)} 個數據點\n")

# 篩選 80m 附近的數據 (70-90m)
filtered = [r for r in records if 70 <= r.get('distance_m', 0) <= 90]
print(f"80m 附近 (70-90m) 的數據點: {len(filtered)} 個\n")
print("="*80)

# 顯示前 20 個數據點
for i, r in enumerate(filtered[:20]):
    distance = r.get('distance_m', 0)
    speed = r.get('speed', 0)
    x = r.get('position_x', 0)
    y = r.get('position_y', 0)
    print(f"{i+1:2d}. Distance: {distance:7.2f}m | Speed: {speed:6.1f} km/h | X: {x:8.1f} | Y: {y:8.1f}")

print("\n" + "="*80)
# 計算平均速度
speeds = [r.get('speed', 0) for r in filtered]
if speeds:
    avg_speed = sum(speeds) / len(speeds)
    min_speed = min(speeds)
    max_speed = max(speeds)
    print(f"\n速度統計:")
    print(f"  最小速度: {min_speed:.1f} km/h")
    print(f"  最大速度: {max_speed:.1f} km/h")
    print(f"  平均速度: {avg_speed:.1f} km/h")
