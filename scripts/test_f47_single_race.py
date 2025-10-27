#!/usr/bin/env python3
"""
F47 單一賽事測試腳本
測試 CLI Function 47 是否正常運作
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 測試參數
YEAR = 2025
RACE = "Mexico"
SESSION = "Q"

print("=" * 70)
print("  F47 全車手彎道分析 - 單一賽事測試")
print("=" * 70)
print()
print("測試配置：")
print(f"  - 年份：{YEAR}")
print(f"  - 賽事：{RACE}")
print(f"  - 會話：{SESSION}")
print(f"  - 功能：F47 (全車手彎道速度分析)")
print()

# 檢查 JSON 是否已存在
json_dir = Path("json")
json_pattern = f"all_drivers_cornering_analysis_{YEAR}_{RACE}_{SESSION}_*.json"
existing_jsons = list(json_dir.glob(json_pattern))

if existing_jsons:
    print("發現已存在的 JSON 檔案：")
    for json_file in existing_jsons:
        size_kb = json_file.stat().st_size / 1024
        mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
        print(f"  - {json_file.name}")
        print(f"    大小：{size_kb:.1f} KB")
        print(f"    修改時間：{mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    response = input("是否要重新生成？(y/N): ").strip().lower()
    if response != 'y':
        print("測試取消")
        sys.exit(0)

print()
print("開始執行 CLI F47...")
print("-" * 70)

# 執行命令
cmd = [
    sys.executable,
    "f1_analysis_modular_main.py",
    "-f", "47",
    "-y", str(YEAR),
    "-r", RACE,
    "-s", SESSION
]

print(f"執行命令：{' '.join(cmd)}")
print("-" * 70)
print()

start_time = datetime.now()

try:
    # 執行並顯示即時輸出
    result = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # 顯示輸出
    print(result.stdout)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("-" * 70)
    
    if result.returncode == 0:
        print(f"✅ 執行成功！")
        print(f"⏱️  執行時間：{duration:.2f} 秒")
        
        # 檢查生成的 JSON
        new_jsons = sorted(
            json_dir.glob(json_pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if new_jsons:
            latest_json = new_jsons[0]
            print()
            print("生成的 JSON 檔案：")
            print(f"  - 檔名：{latest_json.name}")
            
            size_kb = latest_json.stat().st_size / 1024
            print(f"  - 大小：{size_kb:.1f} KB")
            
            mtime = datetime.fromtimestamp(latest_json.stat().st_mtime)
            print(f"  - 時間：{mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 讀取並顯示 JSON 結構
            try:
                with open(latest_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print()
                print("JSON 內容預覽：")
                print(f"  - 成功：{data.get('success', False)}")
                print(f"  - 訊息：{data.get('message', 'N/A')}")
                
                if data.get('data'):
                    print("  - 數據區塊：")
                    
                    # 選擇的彎道
                    if 'selected_corners' in data['data']:
                        corners = data['data']['selected_corners']
                        print("    └─ 選擇的彎道：")
                        
                        if 'low_speed' in corners:
                            low = corners['low_speed']
                            print(f"       • 低速彎：{low.get('corner_number', 'N/A')} "
                                  f"({low.get('avg_speed', 'N/A')} km/h)")
                        
                        if 'medium_speed' in corners:
                            med = corners['medium_speed']
                            print(f"       • 中速彎：{med.get('corner_number', 'N/A')} "
                                  f"({med.get('avg_speed', 'N/A')} km/h)")
                        
                        if 'high_speed' in corners:
                            high = corners['high_speed']
                            print(f"       • 高速彎：{high.get('corner_number', 'N/A')} "
                                  f"({high.get('avg_speed', 'N/A')} km/h)")
                    
                    # 最速圈分析
                    if 'fastest_lap_analysis' in data['data']:
                        fastest = data['data']['fastest_lap_analysis']
                        print("    └─ 最速圈分析：")
                        
                        if 'low_speed' in fastest:
                            driver_count = len(fastest['low_speed'])
                            print(f"       • 低速彎數據：{driver_count} 位車手")
                        
                        if 'medium_speed' in fastest:
                            driver_count = len(fastest['medium_speed'])
                            print(f"       • 中速彎數據：{driver_count} 位車手")
                        
                        if 'high_speed' in fastest:
                            driver_count = len(fastest['high_speed'])
                            print(f"       • 高速彎數據：{driver_count} 位車手")
                    
                    # 全圈分析
                    if 'all_laps_analysis' in data['data']:
                        all_laps = data['data']['all_laps_analysis']
                        print("    └─ 全圈分析：")
                        
                        if 'low_speed' in all_laps:
                            lap_count = len(all_laps['low_speed'])
                            print(f"       • 低速彎數據：{lap_count} 筆記錄")
                
            except Exception as e:
                print(f"  ⚠️  無法讀取 JSON 內容：{e}")
        else:
            print()
            print("⚠️  警告：未找到生成的 JSON 檔案")
    else:
        print(f"❌ 執行失敗！")
        print(f"   返回碼：{result.returncode}")
        print(f"⏱️  執行時間：{duration:.2f} 秒")

except Exception as e:
    print()
    print(f"❌ 異常錯誤：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("測試完成！")
