#!/usr/bin/env python3
"""
批次生成 F57 和 F91 預測數據
為 2025 年 4 個賽事生成預測結果
"""

import subprocess
import time

# 目標賽事
races = [
    ("Japan", "Japanese"),
    ("Abu_Dhabi", "Abu_Dhabi"),
    ("Las_Vegas", "Las_Vegas"),
    ("Mexico", "Mexico_City")
]

print("="*70)
print("批次生成 F57 和 F91 預測 - 2025 賽季 4 場比賽")
print("="*70)

for race_cli, race_folder in races:
    print(f"\n{'='*70}")
    print(f"處理賽事: {race_cli}")
    print(f"{'='*70}")
    
    # 生成 F57 預測
    print(f"\n[1/2] 生成 F57 預測...")
    cmd_f57 = f"python f1_analysis_modular_main.py -f 57 -y 2025 -r {race_cli} -s R"
    try:
        result = subprocess.run(cmd_f57, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ F57 預測完成")
        else:
            print(f"❌ F57 預測失敗: {result.stderr[:200]}")
    except Exception as e:
        print(f"❌ F57 執行錯誤: {e}")
    
    time.sleep(2)
    
    # 生成 F91 預測
    print(f"\n[2/2] 生成 F91 預測...")
    cmd_f91 = f"python f1_analysis_modular_main.py -f 91 -y 2025 -r {race_cli}"
    try:
        result = subprocess.run(cmd_f91, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"✅ F91 預測完成")
        else:
            print(f"❌ F91 預測失敗: {result.stderr[:200]}")
    except Exception as e:
        print(f"❌ F91 執行錯誤: {e}")
    
    time.sleep(2)
    
    print(f"✅ {race_cli} 處理完成\n")

print("\n" + "="*70)
print("批次處理完成！")
print("="*70)
