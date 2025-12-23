"""
檢查 JSON 中是否有缺少 length 欄位的 stint
這會導致 MDI 回退到 end_lap = start_lap
"""
import json

filepath = 'json/tire_strategy_2025_Japan_R.json'

print("=" * 80)
print("檢查缺少 length 欄位的 stint")
print("=" * 80)

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data.get('drivers_analysis', {})

problem_count = 0
total_stints = 0

for driver, info in drivers.items():
    stint_analysis = info.get('stint_analysis', [])
    
    for idx, stint in enumerate(stint_analysis, 1):
        total_stints += 1
        
        start_lap = stint.get('start_lap')
        end_lap = stint.get('end_lap')
        length = stint.get('length')
        
        # 檢查關鍵情況：end_lap 無效且沒有 length
        has_problem = False
        reason = []
        
        if end_lap is None or end_lap <= 0:
            reason.append("end_lap 無效")
            has_problem = True
        
        if length is None or length <= 0:
            reason.append("length 無效")
            has_problem = True
        
        if start_lap is None:
            reason.append("start_lap 無效")
            has_problem = True
        
        if has_problem:
            problem_count += 1
            print(f"\n❌ {driver} - Stint {idx}:")
            print(f"   start_lap: {start_lap}")
            print(f"   end_lap: {end_lap}")
            print(f"   length: {length}")
            print(f"   問題: {', '.join(reason)}")
            print(f"   → 這會導致回退到 end_lap = start_lap = {start_lap}")

print("\n" + "=" * 80)
print(f"總計: {total_stints} 個 stint，{problem_count} 個有問題")
print("=" * 80)

if problem_count > 0:
    print("\n⚠️  這些 stint 會觸發警告，因為它們會被設置為 end_lap = start_lap")
else:
    print("\n✅ 所有 stint 都有有效的數據")
