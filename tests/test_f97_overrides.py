#!/usr/bin/env python3
"""測試 Function 97 覆寫載入"""

import sys
sys.path.insert(0, 'C:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze')

from CLI_modules.cli.analyzer.championship_standings_analysis import load_driver_overrides

print("=" * 60)
print("測試: Function 97 覆寫載入")
print("=" * 60)

overrides = load_driver_overrides(2025)

print(f"\n載入 {len(overrides)} 個覆寫")

if "TSU" in overrides:
    print(f"\n✅ TSU 覆寫:")
    print(f"  team_slug: {overrides['TSU']['team_slug']}")
    print(f"  team_name: {overrides['TSU']['team_name']}")
    print(f"  constructor_id: {overrides['TSU']['constructor_id']}")
else:
    print("\n❌ TSU 覆寫未找到")

if "LAW" in overrides:
    print(f"\n✅ LAW 覆寫:")
    print(f"  team_slug: {overrides['LAW']['team_slug']}")
    print(f"  team_name: {overrides['LAW']['team_name']}")
    print(f"  constructor_id: {overrides['LAW']['constructor_id']}")
else:
    print("\n❌ LAW 覆寫未找到")
