#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新生成 2025 年所有賽道的 track_position JSON 檔案

此腳本會：
1. 刪除所有 2025 年的 track_position_analysis JSON 檔案
2. 刪除對應的 pickle 快取
3. 使用 CLI -f 2 重新生成每個賽道的 JSON（包含新的 distance 欄位）

Usage:
    python scripts/regenerate_2025_track_json.py
"""

import os
import sys
import subprocess
from pathlib import Path

# 確保可以導入專案模組
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 2025 年賽事列表
RACES_2025 = [
    "Australia",
    "China", 
    "Japan",
    "Bahrain",
    "Saudi_Arabia",
    "Miami",
    "Emilia_Romagna",  # Imola
    "Monaco",
    "Spain",
    "Canada",
    "Austria",
    "Great_Britain",  # Silverstone
    "Hungary",
    "Belgium",
    "Netherlands",
    "Italy",  # Monza
    "Azerbaijan",
    "Singapore",
    "United_States",  # Austin
    "Mexico",
    "Brazil",  # São Paulo
    "Las_Vegas",
    "Qatar",
    "Abu_Dhabi",
]

def main():
    json_dir = PROJECT_ROOT / "json"
    cache_dir = PROJECT_ROOT / "cache"
    
    print("=" * 60)
    print("重新生成 2025 年賽道 JSON 檔案")
    print("=" * 60)
    
    # Step 1: 刪除 2025 年的 track_position JSON 檔案
    print("\n[Step 1] 刪除 2025 年的 track_position JSON 檔案...")
    deleted_json = 0
    for json_file in json_dir.glob("track_position_analysis_2025_*.json"):
        print(f"  刪除: {json_file.name}")
        json_file.unlink()
        deleted_json += 1
    print(f"  共刪除 {deleted_json} 個 JSON 檔案")
    
    # Step 2: 刪除對應的 pickle 快取
    print("\n[Step 2] 刪除 2025 年的 pickle 快取...")
    deleted_cache = 0
    for cache_file in cache_dir.glob("*track_position*2025*.pkl"):
        print(f"  刪除: {cache_file.name}")
        cache_file.unlink()
        deleted_cache += 1
    print(f"  共刪除 {deleted_cache} 個快取檔案")
    
    # Step 3: 重新生成 JSON
    print("\n[Step 3] 重新生成 JSON 檔案...")
    print("-" * 60)
    
    success_count = 0
    failed_races = []
    
    for race in RACES_2025:
        race_display = race.replace("_", " ")
        print(f"\n處理: {race_display}...")
        
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "f1_analysis_modular_main.py",
                    "-f", "2",
                    "-y", "2025",
                    "-r", race,
                    "-s", "R"
                ],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=120  # 2 分鐘超時
            )
            
            # 檢查是否生成了 JSON 檔案
            json_patterns = [
                f"track_position_analysis_2025_{race}_R.json",
                f"track_position_analysis_2025_{race.replace('_', ' ')}_R.json",
            ]
            
            generated = False
            for pattern in json_patterns:
                if (json_dir / pattern).exists():
                    print(f"  ✅ 成功: {pattern}")
                    success_count += 1
                    generated = True
                    break
            
            if not generated:
                print(f"  ⚠️  未生成 JSON（可能賽事尚未舉行）")
                failed_races.append(race_display)
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ 超時")
            failed_races.append(race_display)
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            failed_races.append(race_display)
    
    # 總結
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"成功生成: {success_count} 個賽道")
    
    if failed_races:
        print(f"未成功: {len(failed_races)} 個賽道")
        print(f"  (可能是賽事尚未舉行: {', '.join(failed_races[:5])}{'...' if len(failed_races) > 5 else ''})")
    
    # 驗證新的 distance 欄位
    print("\n[驗證] 檢查新 JSON 的 distance 欄位...")
    import json
    sample_files = list(json_dir.glob("track_position_analysis_2025_*.json"))[:3]
    
    for json_file in sample_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            corners = data.get('data', {}).get('official_corners', {}).get('corners', [])
            if corners and 'distance' in corners[0]:
                first_corner = corners[0]
                print(f"  ✅ {json_file.name}: T1 distance={first_corner['distance']:.0f}m")
            else:
                print(f"  ⚠️  {json_file.name}: 缺少 distance 欄位")
        except Exception as e:
            print(f"  ❌ {json_file.name}: {e}")


if __name__ == "__main__":
    main()
