#!/usr/bin/env python
"""強制更新積分榜（使用最新的 calendar JSON）"""

from CLI_modules.cli.analyzer.championship_standings_analysis import generate_championship_standings

print("🔄 強制重新生成 2025 年積分榜...")
print("📅 將使用最新的 season_calendar JSON")
print("")

result = generate_championship_standings(year=2025, force=True)

print("")
print("=" * 60)
print("✅ 執行結果:")
print(f"  Success: {result['success']}")
print(f"  訊息: {result['message']}")

# 檢查 calendar 數據
if result['success'] and 'data' in result:
    data = result['data']
    calendar = data.get('calendar', {})
    print(f"  📅 Calendar: {calendar.get('completed')}/{calendar.get('total')} completed")
    if calendar.get('next_race'):
        print(f"  🏁 Next Race: {calendar['next_race']['name']}")
        print(f"  📆 Date: {calendar['next_race']['date']}")

print("=" * 60)
