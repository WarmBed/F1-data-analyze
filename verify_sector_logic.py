"""
驗證分段標記邏輯
"""
import json

# 讀取 JSON
with open('json/ideal_lap_ranking_2023_Japan_R.json', encoding='utf-8') as f:
    data = json.load(f)

# 檢查 VER 的數據
ver_data = data['analysis_result']['ranking'][0]

print("=== VER (第 1 名) ===")
print(f"車手: {ver_data['driver']}")
print(f"理想圈時間: {ver_data['ideal_lap_time']}")
print(f"最速圈時間: {ver_data['fastest_lap_time']}")
print(f"差異: {ver_data['time_gap']}")
print()

print("分段詳情:")
sb = ver_data['sector_breakdown']
for sector_num in [1, 2, 3]:
    sector_key = f"sector_{sector_num}"
    sector_data = sb[sector_key]
    print(f"  S{sector_num}: {sector_data['time']:.3f}s - is_optimal_in_fastest={sector_data['is_optimal_in_fastest']}")

print()
print("解釋:")
print("- 理想圈 = 最速圈 (94.183 = 94.183)")
print("- 但各分段的 is_optimal_in_fastest 都是 False")
print("- 這表示：雖然整體時間相同，但各分段可能來自不同圈次")
print("- ✗✗✗ = 理想圈的各分段並非全部來自最速圈")
