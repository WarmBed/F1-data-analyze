"""
檢查分段標記顯示結果
"""
import json

# 讀取 JSON
with open('json/ideal_lap_ranking_2023_Japan_R.json', encoding='utf-8') as f:
    data = json.load(f)

ranking = data['analysis_result']['ranking']

print('檢查前 10 名車手的分段標記:')
print('車手 | S1 | S2 | S3 | 預期顯示')
print('-' * 40)

for d in ranking[:10]:
    sb = d['sector_breakdown']
    
    # 取得各分段標記
    s1 = '✓' if sb.get('sector_1', {}).get('is_optimal_in_fastest', False) else '✗'
    s2 = '✓' if sb.get('sector_2', {}).get('is_optimal_in_fastest', False) else '✗'
    s3 = '✓' if sb.get('sector_3', {}).get('is_optimal_in_fastest', False) else '✗'
    
    combined = f"{s1}{s2}{s3}"
    
    print(f"{d['driver']:4} | {s1}  | {s2}  | {s3}  | {combined}")
