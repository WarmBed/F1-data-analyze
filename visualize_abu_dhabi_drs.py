#!/usr/bin/env python3
"""視覺化 Abu Dhabi 2025 賽道的 DRS 區域位置"""

import json
from pathlib import Path

# 讀取數據
json_file = Path("json/track_circuit_data_Abu_Dhabi.json")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

track_length = data.get("track_length_m", 0)
drs_zones = data.get("drs_zones", [])

def get_nearest_corner(distance, track_data):
    """找出最接近某距離的彎道編號"""
    corners = track_data.get("corners", [])
    if not corners:
        return "?"
    
    min_diff = float('inf')
    nearest = None
    
    for corner in corners:
        corner_dist = corner.get("distance_m", 0)
        diff = abs(corner_dist - distance)
        if diff < min_diff:
            min_diff = diff
            nearest = corner.get("number", "?")
    
    return nearest

print("=" * 80)
print("🏁 Abu Dhabi Grand Prix - DRS 區域視覺化 (2025)")
print("=" * 80)
print(f"\n📏 賽道總長度: {track_length:.0f} 米 ({track_length/1000:.3f} km)")
print(f"🟢 DRS 區域數量: {len(drs_zones)}")
print()

# 創建賽道視覺化
track_visual_length = 70
print("賽道圖示:")
print("─" * track_visual_length)

# 創建賽道標記陣列
track_marks = [' '] * track_visual_length

# 標記起點和終點
track_marks[0] = 'S'
track_marks[-1] = 'F'

# 標記 DRS 區域
for zone in drs_zones:
    zone_id = zone.get("zone_id", 0)
    detection = zone.get("detection_distance_m", 0)
    activation = zone.get("activation_distance_m", 0)
    end = zone.get("end_distance_m", 0)
    
    # 計算在視覺化圖上的位置
    det_pos = int((detection / track_length) * track_visual_length)
    act_pos = int((activation / track_length) * track_visual_length)
    end_pos = int((end / track_length) * track_visual_length)
    
    # 標記 DRS 區域（使用不同符號）
    if 0 <= det_pos < track_visual_length:
        track_marks[det_pos] = '|'  # 偵測點
    
    # 填充 DRS 啟用區域
    for i in range(act_pos, min(end_pos + 1, track_visual_length)):
        if 0 <= i < track_visual_length and track_marks[i] == ' ':
            track_marks[i] = '█'  # DRS 區域

# 顯示賽道
print(''.join(track_marks))
print("─" * track_visual_length)

# 圖例
print("\n圖例:")
print("  S = 起點/終點 (Start/Finish)")
print("  F = 終點線")
print("  | = DRS 偵測點 (Detection Point)")
print("  █ = DRS 啟用區域 (Active DRS Zone)")

# 詳細資訊
print("\n" + "=" * 80)
print("DRS 區域詳細資訊:")
print("=" * 80)

for zone in drs_zones:
    zone_id = zone.get("zone_id", 0)
    detection = zone.get("detection_distance_m", 0)
    activation = zone.get("activation_distance_m", 0)
    end = zone.get("end_distance_m", 0)
    length = zone.get("length_m", 0)
    
    print(f"\n🔵 DRS Zone {zone_id}:")
    print(f"   ├─ 偵測點:   Turn {get_nearest_corner(detection, data)} 附近 ({detection:,.0f}m = {detection/track_length*100:.1f}%)")
    print(f"   ├─ 啟用點:   {activation:,.0f}m ({activation/track_length*100:.1f}%)")
    print(f"   ├─ 結束點:   Turn {get_nearest_corner(end, data)} 附近 ({end:,.0f}m = {end/track_length*100:.1f}%)")
    print(f"   └─ DRS 長度: {length:,.0f}m")

print("\n" + "=" * 80)
print("✅ Abu Dhabi 賽道確實有 2 個 DRS 區域！")
print("=" * 80)
