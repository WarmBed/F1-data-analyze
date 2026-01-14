#!/usr/bin/env python3
"""檢查 Abu Dhabi 2025 賽道的 DRS 區域"""

import json
from pathlib import Path

# 讀取 Abu Dhabi track circuit data
json_file = Path("json/track_circuit_data_Abu_Dhabi.json")

if not json_file.exists():
    print(f"❌ 找不到檔案: {json_file}")
    exit(1)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("🏁 Abu Dhabi Track Circuit Data (2025)")
print("=" * 70)

# 基本資訊
track_length = data.get("track_length_m", 0)
print(f"\n📏 賽道長度: {track_length:.0f} 米 ({track_length/1000:.3f} km)")

# DRS 區域
drs_zones = data.get("drs_zones", [])
print(f"\n🟢 DRS 區域數量: {len(drs_zones)}")

if drs_zones:
    print("\n" + "=" * 70)
    print("DRS 區域詳細資訊:")
    print("=" * 70)
    
    for zone in drs_zones:
        zone_id = zone.get("zone_id", 0)
        detection = zone.get("detection_distance_m", 0)
        activation = zone.get("activation_distance_m", 0)
        end = zone.get("end_distance_m", 0)
        length = zone.get("length_m", 0)
        
        print(f"\n🔵 DRS Zone {zone_id}:")
        print(f"   偵測點 (Detection):   {detection:7.0f} m")
        print(f"   啟用點 (Activation):  {activation:7.0f} m")
        print(f"   結束點 (End):         {end:7.0f} m")
        print(f"   長度 (Length):        {length:7.0f} m")
        
        # 計算相對位置（百分比）
        detection_pct = (detection / track_length) * 100
        activation_pct = (activation / track_length) * 100
        end_pct = (end / track_length) * 100
        
        print(f"   相對位置: 偵測 {detection_pct:.1f}% → 啟用 {activation_pct:.1f}% → 結束 {end_pct:.1f}%")
else:
    print("\n❌ 此賽道沒有 DRS 區域數據！")

# 彎道資訊
corners = data.get("corners", [])
print(f"\n🔄 彎道數量: {len(corners)}")

print("\n" + "=" * 70)
print("✅ 分析完成")
print("=" * 70)
