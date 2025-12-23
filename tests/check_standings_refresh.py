#!/usr/bin/env python3
"""快速檢查 Championship Standings JSON 內容"""

import json
from pathlib import Path

json_file = Path("json/championship_standings_2025_R19_20251020T133813Z.json")

if json_file.exists():
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 70)
    print("Championship Standings - 刷新後資料摘要")
    print("=" * 70)
    
    metadata = data.get("metadata", {})
    print(f"\n📋 基本資訊:")
    print(f"  • 賽季: {metadata.get('season_year')}")
    print(f"  • 輪次: R{metadata.get('resolved_round')}")
    print(f"  • 生成時間: {metadata.get('generated_at')}")
    print(f"  • 刷新間隔: {metadata.get('refresh_interval_hours')} 小時")
    print(f"  • 強制重新生成: {metadata.get('force_regenerated')}")
    
    drivers = data.get("data", {}).get("drivers", [])
    constructors = data.get("data", {}).get("constructors", [])
    
    print(f"\n🏆 車手積分榜 (前 10 名) - 共 {len(drivers)} 位車手:")
    for i, driver in enumerate(drivers[:10], 1):
        driver_info = driver.get("driver", {})
        code = driver_info.get("code", "???")
        name = driver_info.get("full_name", "Unknown")
        points = driver.get("points", 0)
        wins = driver.get("wins", 0)
        delta = driver.get("points_delta", 0)
        
        # 取得車隊資訊
        teams = driver.get("constructors", [])
        team_name = teams[0].get("name", "Unknown") if teams else "Unknown"
        
        print(f"  {i:2d}. {code:3s} | {name:20s} | {team_name:12s} | {points:6.1f} 分 | {wins} 勝 | -{delta:.1f}")
    
    print(f"\n🏁 車隊積分榜 (前 10 名) - 共 {len(constructors)} 支車隊:")
    for i, constructor in enumerate(constructors[:10], 1):
        constructor_info = constructor.get("constructor", {})
        name = constructor_info.get("name", "Unknown")
        points = constructor.get("points", 0)
        wins = constructor.get("wins", 0)
        delta = constructor.get("points_delta", 0)
        
        print(f"  {i:2d}. {name:15s} | {points:6.1f} 分 | {wins} 勝 | -{delta:.1f}")
    
    print("\n" + "=" * 70)
    print("✅ Championship Standings 已成功刷新！")
    print("=" * 70)
else:
    print(f"❌ 找不到檔案: {json_file}")
