#!/usr/bin/env python3
"""檢查 function_mapper 的實際映射狀態"""

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper

# 創建 mapper 實例（不需要數據載入器）
mapper = F1AnalysisFunctionMapper(data_loader=None)

# 檢查 function 98 的映射
print("=" * 60)
print("Function 98 映射檢查")
print("=" * 60)

if 98 in mapper.function_mapping:
    func = mapper.function_mapping[98]
    print(f"✅ Function 98 存在於映射表")
    print(f"   映射到方法: {func.__name__}")
    print(f"   方法物件: {func}")
else:
    print("❌ Function 98 不存在於映射表")

# 列出所有可用方法
print("\n" + "=" * 60)
print("F1AnalysisFunctionMapper 的方法列表")
print("=" * 60)

methods = [m for m in dir(mapper) if m.startswith('_execute_')]
color_methods = [m for m in methods if 'color' in m.lower()]
weather_methods = [m for m in methods if 'weather' in m.lower()]

print(f"\n顏色相關方法 ({len(color_methods)} 個):")
for m in color_methods:
    print(f"  - {m}")

print(f"\n天氣相關方法 ({len(weather_methods)} 個):")
for m in weather_methods:
    print(f"  - {m}")

# 檢查 _execute_team_color_analysis 是否存在
if hasattr(mapper, '_execute_team_color_analysis'):
    print("\n✅ _execute_team_color_analysis 方法存在")
else:
    print("\n❌ _execute_team_color_analysis 方法不存在")

# 檢查 _execute_race_weather_forecast 是否存在
if hasattr(mapper, '_execute_race_weather_forecast'):
    print("✅ _execute_race_weather_forecast 方法存在 (Function 96)")
else:
    print("❌ _execute_race_weather_forecast 方法不存在")
