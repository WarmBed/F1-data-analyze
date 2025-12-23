#!/usr/bin/env python
"""強制更新 Season Calendar"""

from CLI_modules.cli.analyzer.season_calendar_analysis import generate_season_calendar

print("🔄 強制重新生成 Season Calendar (2020-2025)...")
print("⚠️  force=True，將忽略緩存和刷新間隔")
print("")

result = generate_season_calendar(save_json=True, all_years=True, force=True)

print("")
print("=" * 60)
print("✅ 執行結果:")
print(f"  Success: {result['success']}")
print(f"  訊息: {result['message']}")
print(f"  總賽事數: {result['metadata']['total_events_all_years']}")
print(f"  已完成: {result['metadata']['completed_events_all_years']}")
print(f"  即將舉行: {result['metadata']['upcoming_events_all_years']}")
print(f"  生成時間: {result['metadata']['generated_at']}")
print(f"  強制重新生成: {result['metadata']['force_regenerated']}")
print("=" * 60)
