#!/usr/bin/env python3
"""強制刷新 2025 年積分榜"""

from CLI_modules.cli.analyzer.championship_standings_analysis import generate_championship_standings

print("正在強制刷新 2025 年積分榜...")
print("=" * 60)

result = generate_championship_standings(year=2025)

print()
print("=" * 60)
print(f"生成結果: {'成功' if result['success'] else '失敗'}")
print(f"訊息: {result.get('message', 'N/A')}")
