#!/usr/bin/env python3
"""
自動收集 2022 和 2023 缺失的賽事數據
"""
import subprocess
import sys
import os
import glob
from datetime import datetime

# 2022 年缺失的賽事
missing_2022 = [
    "Hungary", "Belgium", "Netherlands", "Italy",
    "Singapore", "Japan", "United States", "Mexico", "Brazil", "Abu Dhabi"
]

# 2023 年缺失的賽事
missing_2023 = [
    "Italy", "Singapore", "Japan", "Qatar", "United States",
    "Mexico", "Brazil", "Las Vegas", "Abu Dhabi"
]

def check_exists(year, race):
    """檢查檔案是否已存在"""
    pattern = f"json/predictionJSON/fp_q_data_{year}_{race.replace(' ', '_')}_*.json"
    files = glob.glob(pattern)
    return len(files) > 0

def collect_race(year, race):
    """收集單場賽事"""
    # 檢查是否已存在
    if check_exists(year, race):
        print(f"⏭️  跳過: {year} {race} (已存在)")
        return None
    
    print(f"\n{'='*60}")
    print(f"正在收集: {year} {race}")
    print(f"時間: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    cmd = ["python", "f1_analysis_modular_main.py", "-f", "70", "-y", str(year), "-r", race]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print(f"✅ 成功: {year} {race}")
            return True
        else:
            print(f"❌ 失敗: {year} {race} (Exit Code: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ 異常: {year} {race} - {e}")
        return False

def main():
    start_time = datetime.now()
    total = len(missing_2022) + len(missing_2023)
    completed = 0
    failed = 0
    skipped = 0
    
    print(f"\n開始收集缺失賽事")
    print(f"2022: {len(missing_2022)} 場")
    print(f"2023: {len(missing_2023)} 場")
    print(f"總計: {total} 場\n")
    
    # 收集 2022
    print("\n### 收集 2022 年 ###")
    for race in missing_2022:
        result = collect_race(2022, race)
        if result is None:
            skipped += 1
        elif result:
            completed += 1
        else:
            failed += 1
        print(f"進度: {completed} 完成, {failed} 失敗, {skipped} 跳過\n")
    
    # 收集 2023
    print("\n### 收集 2023 年 ###")
    for race in missing_2023:
        result = collect_race(2023, race)
        if result is None:
            skipped += 1
        elif result:
            completed += 1
        else:
            failed += 1
        print(f"進度: {completed} 完成, {failed} 失敗, {skipped} 跳過\n")
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    print(f"\n{'='*60}")
    print(f"收集完成！")
    print(f"總耗時: {elapsed:.1f} 分鐘")
    print(f"成功: {completed}")
    print(f"失敗: {failed}")
    print(f"跳過: {skipped}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
