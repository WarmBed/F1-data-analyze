#!/usr/bin/env python3
"""測試 GUI ColorPaletteProvider 的實際行為"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== 測試 GUI ColorPaletteProvider ===\n")
print("正在載入模組...")

try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    print("模組載入成功!")
except Exception as e:
    print(f"模組載入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 強制重新載入 2025 數據
print("1. 強制重新載入 2025 數據...")
color_palette_provider.ensure_loaded(year=2025, force=True)

# 檢查載入後的狀態
print(f"   _loaded_year: {color_palette_provider._loaded_year}")
print(f"   _defaults_applied: {color_palette_provider._defaults_applied}")
print(f"   _last_error: {color_palette_provider._last_error}")
print(f"   driver_palette 數量: {len(color_palette_provider._driver_palette)}")

print("\n2. 關鍵車手顏色檢查:")
print("-" * 60)
for code in ['HAM', 'SAI', 'BEA', 'ANT', 'TSU', 'LAW', 'VER', 'NOR']:
    color = color_palette_provider.get_driver_color(code, format='hex')
    team = color_palette_provider.get_driver_team(code)
    
    # 直接查看 _driver_palette 中的原始數據
    raw = color_palette_provider._driver_palette.get(code, {})
    raw_team = raw.get('team_name', 'N/A')
    raw_hex = raw.get('hex', 'N/A')
    
    print(f"{code}: api_team={team}, api_hex={color}")
    print(f"     raw_team={raw_team}, raw_hex={raw_hex}")
    print()

print("\n3. 完整 driver_palette 車隊分佈:")
print("-" * 60)
team_count = {}
for code, info in color_palette_provider._driver_palette.items():
    team = info.get('team_name', 'Unknown')
    if team not in team_count:
        team_count[team] = []
    team_count[team].append(code)

for team, drivers in sorted(team_count.items()):
    print(f"{team}: {', '.join(drivers)}")
