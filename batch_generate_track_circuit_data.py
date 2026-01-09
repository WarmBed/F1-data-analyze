#!/usr/bin/env python3
"""
批量生成賽道彎道和 DRS 區域數據

使用 track_circuit_analyzer 為所有 2025 賽季賽道生成
track_circuit_data_{race}.json 檔案

Author: F1T Team
Date: 2025-01-05
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategy_simulator.data.track_circuit_analyzer import analyze_track_circuit


# 2025 賽季賽道列表
RACES_2025 = [
    "Bahrain",
    "Saudi Arabia", 
    "Australia",
    "Japan",
    "China",
    "Miami",
    "Emilia Romagna",
    "Monaco",
    "Canada",
    "Spain",
    "Austria",
    "Great Britain",
    "Hungary",
    "Belgium",
    "Netherlands",
    "Italy",
    "Azerbaijan",
    "Singapore",
    "United States",
    "Mexico",
    "Brazil",
    "Las Vegas",
    "Qatar",
    "Abu Dhabi"
]


def batch_generate_track_data(year: int = 2025, session: str = "R"):
    """
    批量生成所有賽道的彎道和 DRS 數據
    
    Args:
        year: 年份
        session: 場次類型 (R=正賽, Q=排位賽)
    """
    print(f"\n{'='*60}")
    print(f"批量生成 {year} 賽季賽道數據")
    print(f"{'='*60}\n")
    
    success_count = 0
    failed_races = []
    
    for race in RACES_2025:
        print(f"\n▶ 處理 {race}...", end=" ")
        
        try:
            result = analyze_track_circuit(year, race, session, save_json=True)
            
            if result:
                print(f"✅ 成功")
                print(f"   - 彎道數: {result['corners_count']}")
                print(f"   - DRS 區數: {result['drs_zones_count']}")
                print(f"   - 賽道長度: {result['track_length_m']:.0f}m")
                success_count += 1
            else:
                print(f"❌ 失敗 (無返回值)")
                failed_races.append(race)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            failed_races.append(race)
    
    # 總結
    print(f"\n{'='*60}")
    print(f"生成完成")
    print(f"{'='*60}")
    print(f"成功: {success_count}/{len(RACES_2025)}")
    
    if failed_races:
        print(f"失敗賽道: {', '.join(failed_races)}")
    
    print(f"\n輸出目錄: {project_root / 'json'}")


if __name__ == "__main__":
    batch_generate_track_data(2025, "R")
