"""
檢查理想圈=最速圈的車手，為何分段還是 XXX
"""
import json

# 讀取 JSON
with open('json/ideal_lap_ranking_2023_Japan_R.json', encoding='utf-8') as f:
    data = json.load(f)

ranking = data['analysis_result']['ranking']

# 找出理想圈=最速圈的車手 (time_gap = 0)
perfect_drivers = [d for d in ranking if d.get('time_gap', 1) == 0]

print(f"找到 {len(perfect_drivers)} 位車手的理想圈 = 最速圈:")
print()

for driver_data in perfect_drivers:
    print(f"車手: {driver_data['driver']}")
    print(f"  理想圈: {driver_data['ideal_lap_time']}")
    print(f"  最速圈: {driver_data['fastest_lap_time']}")
    print(f"  差異: {driver_data['time_gap']}")
    print(f"  分段:")
    
    sb = driver_data['sector_breakdown']
    for i in [1, 2, 3]:
        sector_key = f'sector_{i}'
        sector = sb[sector_key]
        symbol = "✓" if sector['is_optimal_in_fastest'] else "✗"
        print(f"    S{i}: {sector['time']:.3f}s - is_optimal_in_fastest={sector['is_optimal_in_fastest']} ({symbol})")
    
    print()

print("=" * 60)
print("解釋：")
print()
print("is_optimal_in_fastest 的意思是：")
print("  「這個分段在最速圈中，是否已經達到理想狀態」")
print()
print("判斷邏輯：")
print("  if abs(fastest_sector_time - ideal_sector_time) < 0.01:")
print("      is_optimal_in_fastest = True  # ✓")
print("  else:")
print("      is_optimal_in_fastest = False # ✗")
print()
print("所以即使 理想圈 = 最速圈（整體時間相同）")
print("但各個分段可能來自「不同圈次」！")
print()
print("範例：")
print("  最速圈：S1=33.8s, S2=42.1s, S3=18.3s → 總計 94.2s")
print("  理想圈：S1=33.7s(Lap5), S2=42.1s(Lap10), S3=18.4s(Lap15) → 總計 94.2s")
print("  雖然總時間相同，但各分段來自不同圈！")
print("  → 分段標記：✗✗✗")
