#!/usr/bin/env python3
"""測試 team_color_analysis 的車隊映射"""

from CLI_modules.cli.analyzer.team_color_analysis import generate_team_color_report

# 強制重新生成
result = generate_team_color_report(year=2025, force=True, include_drivers=True)

print("\n" + "=" * 70)
print("=== 生成結果 ===")
print("=" * 70)

if result.get("success"):
    drivers = result.get("data", {}).get("drivers", {})
    print(f"\n共 {len(drivers)} 位車手:\n")
    
    # 按車隊分組
    team_drivers = {}
    for code, info in drivers.items():
        team = info.get("team_name", "Unknown")
        if team not in team_drivers:
            team_drivers[team] = []
        team_drivers[team].append((code, info.get("hex", "N/A")))
    
    for team, members in sorted(team_drivers.items()):
        print(f"{team}:")
        for code, hex_color in members:
            print(f"  - {code}: {hex_color}")
        print()
    
    # 特別檢查關鍵車手
    print("=" * 70)
    print("=== 關鍵車手顏色檢查 ===")
    print("=" * 70)
    key_drivers = ["HAM", "SAI", "BEA", "ANT", "TSU", "LAW"]
    for code in key_drivers:
        info = drivers.get(code, {})
        print(f"{code}: team={info.get('team_name', 'NOT FOUND')}, hex={info.get('hex', 'N/A')}")
else:
    print(f"生成失敗: {result.get('message')}")
