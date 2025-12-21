"""
查找 2025 Australia R 的完美單圈達成者
"""
import json

# 讀取 JSON
with open('json/ideal_lap_ranking_2025_Australia_R.json', encoding='utf-8') as f:
    data = json.load(f)

ranking = data['analysis_result']['ranking']

# 找出理想圈=最速圈的車手 (time_gap = 0)
perfect_drivers = [d for d in ranking if d.get('time_gap', 1) == 0]

print("=" * 60)
print(f"2025 Australia R - 完美單圈達成者 ({len(perfect_drivers)}/17)")
print("=" * 60)
print()

for idx, driver_data in enumerate(perfect_drivers, 1):
    print(f"{idx}. {driver_data['driver']}")
    print(f"   理想圈: {driver_data['ideal_lap_time']:.3f}s")
    print(f"   最速圈: {driver_data['fastest_lap_time']:.3f}s")
    print(f"   差異: {driver_data['time_gap']:.3f}s ✅")
    
    # 分段標記
    sb = driver_data['sector_breakdown']
    marks = []
    for i in [1, 2, 3]:
        sector_key = f'sector_{i}'
        is_optimal = sb[sector_key]['is_optimal_in_fastest']
        marks.append('✓' if is_optimal else '✗')
    
    combined = ''.join(marks)
    print(f"   分段標記: {combined}")
    
    # 詳細分段
    print(f"   分段詳情:")
    for i in [1, 2, 3]:
        sector_key = f'sector_{i}'
        sector = sb[sector_key]
        symbol = '✓' if sector['is_optimal_in_fastest'] else '✗'
        print(f"     S{i}: {sector['time']:.3f}s ({symbol})")
    
    print()

print("=" * 60)
print("結論:")
print(f"  共 {len(perfect_drivers)} 位車手達成「理想圈 = 最速圈」")
print(f"  但分段標記可能仍是 ✗✗✗（如前面解釋）")
