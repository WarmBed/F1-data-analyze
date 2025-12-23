#!/usr/bin/env python3
"""
測試EXE環境下車手列表載入問題
診斷工具：檢查LapAnalysisOptionsDialog的車手載入邏輯
"""

import sys
import json
import glob
import os

print("=" * 80)
print("🔍 EXE環境車手列表載入診斷測試")
print("=" * 80)

# 測試參數
year = "2025"
race = "Japan"

print(f"\n📋 測試參數:")
print(f"   年份: {year}")
print(f"   賽事: {race}")

drivers = []

# ========== 策略 1: 從 team_colors JSON 讀取 ==========
print(f"\n🔍 步驟 1: 檢查 team_colors JSON...")
team_color_patterns = [
    f"json/team_colors_{year}_*.json",
    f"json/team_colors_2025_*.json",
    f"json/team_colors_2024_*.json"
]

for pattern in team_color_patterns:
    files = glob.glob(pattern)
    print(f"   搜索模式: {pattern}")
    print(f"   找到檔案: {files}")
    
    if files:
        latest_file = max(files, key=os.path.getmtime)
        print(f"   ✅ 使用檔案: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                color_data = json.load(f)
                
            print(f"   JSON結構: {list(color_data.keys())}")
            
            if 'data' in color_data:
                print(f"   data結構: {list(color_data['data'].keys())}")
                
                if 'drivers' in color_data['data']:
                    drivers = sorted(list(color_data['data']['drivers'].keys()))
                    print(f"   ✅ 成功提取 {len(drivers)} 個車手")
                    print(f"   車手列表: {drivers}")
                    break
                else:
                    print(f"   ⚠️ data中沒有drivers鍵")
            else:
                print(f"   ⚠️ JSON中沒有data鍵")
                
        except Exception as e:
            print(f"   ❌ 讀取失敗: {e}")
            import traceback
            traceback.print_exc()

# ========== 策略 2: 從進站 JSON 讀取 ==========
if not drivers:
    print(f"\n🔍 步驟 2: 檢查進站分析 JSON...")
    pitstop_patterns = [
        f"json/pitstop_analysis_{year}_{race}*.json",
        f"json_exports/pitstop_analysis_{year}_{race}*.json",
        f"cache/driver_fastest_pitstop_{year}_{race}*.pkl",
        f"json/driver_pitstop_summary_{year}*.json"
    ]
    
    for pattern in pitstop_patterns:
        files = glob.glob(pattern)
        print(f"   搜索模式: {pattern}")
        print(f"   找到檔案: {files}")
        
        if files:
            found_file = files[0]
            print(f"   ✅ 使用檔案: {found_file}")
            
            if found_file.endswith('.json'):
                try:
                    with open(found_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"   JSON結構: {list(data.keys())}")
                    
                    # 嘗試提取車手
                    if 'drivers' in data:
                        drivers = data['drivers']
                        print(f"   ✅ 從 data['drivers'] 提取")
                    elif 'data' in data:
                        print(f"   data結構: {list(data['data'].keys()) if isinstance(data['data'], dict) else type(data['data'])}")
                        
                        if isinstance(data['data'], dict):
                            if 'pitstop_data' in data['data']:
                                pitstop_data = data['data']['pitstop_data']
                                if isinstance(pitstop_data, dict):
                                    drivers = list(pitstop_data.keys())
                                    print(f"   ✅ 從 pitstop_data.keys() 提取")
                                elif isinstance(pitstop_data, list) and pitstop_data:
                                    driver_set = set()
                                    for record in pitstop_data:
                                        if isinstance(record, dict) and 'driver' in record:
                                            driver_set.add(record['driver'])
                                        elif isinstance(record, dict) and 'Driver' in record:
                                            driver_set.add(record['Driver'])
                                    drivers = sorted(list(driver_set))
                                    print(f"   ✅ 從 pitstop_data list 提取")
                    
                    if drivers:
                        print(f"   ✅ 成功提取 {len(drivers)} 個車手")
                        print(f"   車手列表: {drivers}")
                        break
                        
                except Exception as e:
                    print(f"   ❌ 讀取失敗: {e}")
                    import traceback
                    traceback.print_exc()

# ========== 最終結果 ==========
print(f"\n" + "=" * 80)
print(f"📊 最終結果:")
print(f"=" * 80)

if drivers:
    print(f"✅ 成功載入 {len(drivers)} 個車手")
    print(f"   車手列表: {drivers}")
    print(f"\n💡 建議: 對話框應該可以正常顯示車手選項")
else:
    print(f"❌ 無法從任何來源載入車手列表")
    print(f"\n💡 可能的問題:")
    print(f"   1. team_colors JSON檔案不存在或格式不正確")
    print(f"   2. 進站分析 JSON檔案不存在")
    print(f"   3. EXE環境下檔案路徑問題")
    print(f"\n🔧 建議解決方案:")
    print(f"   方案1: 執行 `python f1_analysis_modular_main.py -f 98 -y 2025` 生成 team_colors")
    print(f"   方案2: 檢查EXE環境下的工作目錄是否正確")
    print(f"   方案3: 在對話框中添加硬編碼的備用車手列表（臨時方案）")

print(f"\n" + "=" * 80)
print(f"🧪 診斷完成")
print(f"=" * 80)
