"""
深入分析：為什麼理想圈=最速圈，分段還是 XXX？
"""
import json

# 讀取 JSON
with open('json/ideal_lap_ranking_2023_Japan_R.json', encoding='utf-8') as f:
    data = json.load(f)

ranking = data['analysis_result']['ranking']

# 找到 VER
ver = [d for d in ranking if d['driver'] == 'VER'][0]

print("=" * 80)
print("VER 詳細分析")
print("=" * 80)
print(f"理想圈時間: {ver['ideal_lap_time']}")
print(f"最速圈時間: {ver['fastest_lap_time']}")
print(f"差異: {ver['time_gap']}")
print()

# 檢查是否有 ideal_lap_detail
if 'ideal_lap_detail' in ver:
    ideal_detail = ver['ideal_lap_detail']
    print("理想圈詳情:")
    print(f"  總時間: {ideal_detail.get('total_time')}")
    
    if 'sector_sources' in ideal_detail:
        print("  分段來源:")
        for sector_key, sector_info in ideal_detail['sector_sources'].items():
            lap_num = sector_info.get('lap_number', 'N/A')
            time = sector_info.get('time', 'N/A')
            print(f"    {sector_key}: Lap {lap_num} - {time}s")

# 檢查 laps 資料
if 'laps' in ver and isinstance(ver['laps'], list):
    print()
    print(f"VER 的所有圈速資料 (共 {len(ver['laps'])} 圈):")
    print()
    
    # 找到最速圈
    fastest_lap_data = min(ver['laps'], key=lambda x: x.get('lap_time_seconds', float('inf')))
    fastest_lap_num = fastest_lap_data.get('lap_number')
    
    print(f"最速圈: Lap {fastest_lap_num} - {fastest_lap_data.get('lap_time_seconds')}s")
    print(f"  S1: {fastest_lap_data.get('sector_1_time', 'N/A')}s")
    print(f"  S2: {fastest_lap_data.get('sector_2_time', 'N/A')}s")
    print(f"  S3: {fastest_lap_data.get('sector_3_time', 'N/A')}s")
    print()
    
    # 理想圈的分段
    ideal_sb = ver['sector_breakdown']
    print(f"理想圈分段:")
    print(f"  S1: {ideal_sb['sector_1']['time']}s")
    print(f"  S2: {ideal_sb['sector_2']['time']}s")
    print(f"  S3: {ideal_sb['sector_3']['time']}s")
    print()
    
    # 比較
    print("比較:")
    s1_diff = abs(fastest_lap_data.get('sector_1_time', 0) - ideal_sb['sector_1']['time'])
    s2_diff = abs(fastest_lap_data.get('sector_2_time', 0) - ideal_sb['sector_2']['time'])
    s3_diff = abs(fastest_lap_data.get('sector_3_time', 0) - ideal_sb['sector_3']['time'])
    
    print(f"  S1 差異: {s1_diff:.3f}s → {'✓' if s1_diff < 0.01 else '✗ (超過 0.01s 閾值)'}")
    print(f"  S2 差異: {s2_diff:.3f}s → {'✓' if s2_diff < 0.01 else '✗ (超過 0.01s 閾值)'}")
    print(f"  S3 差異: {s3_diff:.3f}s → {'✓' if s3_diff < 0.01 else '✗ (超過 0.01s 閾值)'}")
    print()
    
    print("結論:")
    if s1_diff >= 0.01 or s2_diff >= 0.01 or s3_diff >= 0.01:
        print("  即使理想圈總時間 = 最速圈總時間")
        print("  但由於某些分段的時間差異 >= 0.01s")
        print("  這些分段實際上來自其他圈次！")
        print()
        print("  這表示 VER 在最速圈中，各分段並非全部達到個人最佳")
        print("  理想圈是從多圈中組合出來的「理論最佳」")
