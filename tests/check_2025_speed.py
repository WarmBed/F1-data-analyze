import json

# 檢查當前 JSON
with open('json/historical_flags_Brazil_2022-2025.json', encoding='utf-8') as f:
    data = json.load(f)

year_2025 = data['data']['yearly_summary']['2025']

print("="*60)
print("2025 年巴西站最高速度數據檢查")
print("="*60)
print(f"\n當前 JSON 記錄:")
print(f"  最高速度: {year_2025.get('max_speed', 'N/A')}")
print(f"  車手: {year_2025.get('max_speed_driver', 'N/A')}")
print(f"  圈數: {year_2025.get('max_speed_lap', 'N/A')}")

print(f"\n用戶提供的正確數據:")
print(f"  最高速度: 346 km/h")
print(f"  車手: VER")
print(f"  圈數: Lap 17")

print(f"\n差異分析:")
current_speed = year_2025.get('max_speed', 0)
if current_speed < 346:
    print(f"  ⚠️  當前數據偏低: {current_speed} < 346")
    print(f"  差異: {346 - current_speed:.1f} km/h")
else:
    print(f"  ✅ 數據正確")

print("="*60)
