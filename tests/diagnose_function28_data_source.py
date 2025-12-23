#!/usr/bin/env python3
"""
診斷 Function 28 的數據來源問題
檢查 data_loader 是否使用了錯誤的賽事數據
"""

import json
from pathlib import Path


print("="*80)
print("Function 28 數據來源診斷")
print("="*80)

# 1. 檢查現有 JSON 檔案的內容
json_file = Path("json/detailed_laptime_analysis_2025_United States_R_all_drivers.json")

if json_file.exists():
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n📄 JSON 檔案資訊:")
    print(f"   檔案: {json_file.name}")
    print(f"   大小: {json_file.stat().st_size / 1024:.1f} KB")
    
    # Metadata
    metadata = data.get('metadata', {})
    print(f"\n📊 Metadata:")
    print(f"   race: {metadata.get('race')}")
    print(f"   year: {metadata.get('year')}")
    print(f"   session: {metadata.get('session')}")
    print(f"   generated_at: {metadata.get('generated_at')}")
    
    # VER 數據
    all_drivers = data.get('all_drivers_detailed_laptime', {})
    ver_data = all_drivers.get('VER', {})
    
    if ver_data:
        detailed_laps = ver_data.get('detailed_lap_data', [])
        
        if detailed_laps:
            valid_laps = [l for l in detailed_laps if l.get('lap_time_seconds') is not None]
            
            if valid_laps:
                fastest_lap = min(valid_laps, key=lambda x: x.get('lap_time_seconds', 999))
                fastest_time = fastest_lap.get('lap_time_seconds')
                
                print(f"\n🏎️  VER 數據:")
                print(f"   總圈數: {len(detailed_laps)}")
                print(f"   有效圈數: {len(valid_laps)}")
                print(f"   最速圈: Lap {fastest_lap.get('lap_number')} - {fastest_time:.3f}s ({fastest_time/60:.0f}:{fastest_time%60:06.3f})")
                
                # 判斷賽事來源
                print(f"\n🔍 賽事來源推測:")
                if 88 <= fastest_time <= 92:
                    print(f"   ⚠️  最速圈 {fastest_time:.3f}s 符合 Japan/Singapore/Bahrain GP 的時間範圍")
                    print(f"   ❌ 不符合 United States GP (應該是 ~97-98s)")
                    print(f"   🐛 BUG 確認: JSON 檔案名稱是 United States 但數據來自其他賽事！")
                elif 97 <= fastest_time <= 99:
                    print(f"   ✅ 最速圈 {fastest_time:.3f}s 符合 United States GP 的時間範圍")
                    print(f"   ✅ 數據正確")
                else:
                    print(f"   ⚠️  最速圈 {fastest_time:.3f}s 未能識別賽事來源")
                
                # 顯示前5圈數據作為範例
                print(f"\n📋 前5圈數據範例:")
                for lap in detailed_laps[:5]:
                    lap_num = lap.get('lap_number')
                    lap_time = lap.get('lap_time_seconds')
                    tire = lap.get('tire_compound', 'N/A')
                    
                    if lap_time:
                        print(f"   Lap {lap_num:2d}: {lap_time:.3f}s ({lap_time/60:.0f}:{lap_time%60:06.3f}) - {tire}")
                    else:
                        print(f"   Lap {lap_num:2d}: N/A - {tire}")
else:
    print(f"\n❌ 找不到檔案: {json_file}")

# 2. 對比正確的 ideal_lap_ranking 數據
print("\n" + "="*80)
print("對比正確的數據來源 (Ideal Lap Ranking)")
print("="*80)

ideal_lap_file = Path("json/ideal_lap_ranking_2025_United States_R.json")

if ideal_lap_file.exists():
    with open(ideal_lap_file, 'r', encoding='utf-8') as f:
        ideal_data = json.load(f)
    
    metadata = ideal_data.get('metadata', {})
    ranking = ideal_data.get('analysis_result', {}).get('ranking', [])
    ver_ideal = next((d for d in ranking if d.get('driver') == 'VER'), None)
    
    if ver_ideal:
        print(f"\n✅ Ideal Lap Ranking (正確參考):")
        print(f"   race: {metadata.get('race')}")
        print(f"   VER 最速圈: {ver_ideal.get('fastest_lap_time'):.3f}s")
        print(f"   VER 理想圈: {ver_ideal.get('ideal_lap_time'):.3f}s")
else:
    print(f"\n❌ 找不到檔案: {ideal_lap_file}")

# 3. 建議修復方案
print("\n" + "="*80)
print("💡 修復建議")
print("="*80)
print("\n問題根源:")
print("   • Function 28 使用了共享的 data_loader 實例")
print("   • data_loader 可能已經載入了其他賽事的數據（如 Japan）")
print("   • analyzer 沒有重新載入正確賽事的 session 數據")
print("\n修復方案:")
print("   1. 在 Function 28 的 analyze_every_lap() 中添加數據驗證")
print("   2. 確保 analyzer 使用傳入的 year/race/session 參數重新載入數據")
print("   3. 或者讓 analyzer 不依賴 data_loader，直接使用傳入的參數載入 session")
print("\n手動修復步驟:")
print("   1. 刪除錯誤的 JSON:")
print("      del json/detailed_laptime_analysis_2025_United States_R_all_drivers.json")
print("   2. 重新生成正確數據:")
print("      python f1_analysis_modular_main.py -f 28 -y 2025 -r \"United States\" -s R")
