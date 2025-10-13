import json

# 載入 JSON
data = json.load(open('json/ideal_lap_ranking_2023_Japan_R.json', encoding='utf-8'))
summary = data['analysis_result']['summary']
ranking = data['analysis_result']['ranking']

print('=' * 80)
print('全場最速實際圈:', summary['session_fastest_lap'], f"({summary['session_fastest_driver']})")
print('=' * 80)
print()
print('前 5 名車手的差距比較:')
print()
print(f"{'排名':<6} {'車手':<6} {'理想圈':<10} {'車手最速圈':<12} {'差異':<12} {'與全場最速差距':<18}")
print('-' * 80)

for d in ranking[:5]:
    gap_str = f"+{d['time_gap']:.3f}s" if d['time_gap'] is not None else "N/A"
    gap_to_fastest_str = f"+{d['gap_to_session_fastest']:.3f}s" if d['gap_to_session_fastest'] is not None else "N/A"
    
    print(f"{d['position']:<6} {d['driver']:<6} {d['ideal_lap_time']:<10.3f} "
          f"{d['fastest_lap_time']:<12.3f} {gap_str:<12} {gap_to_fastest_str:<18}")

print()
print('=' * 80)
print('說明:')
print('  - 差異 = 車手最速圈 - 理想圈（車手自己的提升空間）')
print('  - 與全場最速差距 = 理想圈 - 全場最速實際圈（完美發揮時的競爭力）')
print('=' * 80)
