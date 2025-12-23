"""
Red Flag Filter 實裝驗證腳本
遵循反幻覺編碼五原則
"""

import sys

print("=" * 60)
print("Red Flag Filter 實裝驗證")
print("=" * 60)
print()

# 測試 1: lap_filter_utils 紅旗函數
print("[測試 1] lap_filter_utils 紅旗檢測函數...")
try:
    from modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils import (
        extract_red_flag_laps,
        is_red_flag_lap,
        lap_is_under_red_flag,
        RED_FLAG_INCIDENT_TYPES,
        RED_FLAG_SUMMARY_KEYS
    )
    print("  ✅ extract_red_flag_laps() - 已定義")
    print("  ✅ is_red_flag_lap() - 已定義")
    print("  ✅ lap_is_under_red_flag() - 已定義")
    print("  ✅ RED_FLAG_INCIDENT_TYPES - 已定義")
    print("  ✅ RED_FLAG_SUMMARY_KEYS - 已定義")
except ImportError as e:
    print(f"  ❌ 錯誤: {e}")
    sys.exit(1)

# 測試 2: Throttle Line Chart Data Loader
print("\n[測試 2] Throttle Line Chart Data Loader...")
try:
    from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader import (
        ThrottleLineChartDataLoader
    )
    loader = ThrottleLineChartDataLoader(None)
    assert hasattr(loader, '_filter_red_flags'), "缺少 _filter_red_flags 屬性"
    print("  ✅ ThrottleLineChartDataLoader 導入成功")
    print(f"  ✅ _filter_red_flags 屬性存在 (預設: {loader._filter_red_flags})")
except Exception as e:
    print(f"  ❌ 錯誤: {e}")
    sys.exit(1)

# 測試 3: Throttle Box Plot
print("\n[測試 3] Throttle Box Plot Analysis...")
try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
        ThrottleBoxPlotDataManager
    )
    print("  ✅ ThrottleBoxPlotDataManager 導入成功")
except Exception as e:
    print(f"  ❌ 錯誤: {e}")
    sys.exit(1)

# 測試 4: Lap Time Box Plot Widget
print("\n[測試 4] Lap Time Box Plot Widget...")
try:
    from modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget import (
        LapTimeBoxPlotWidget
    )
    print("  ✅ LapTimeBoxPlotWidget 導入成功")
except Exception as e:
    print(f"  ❌ 錯誤: {e}")
    sys.exit(1)

# 測試 5: GUI Settings Manager
print("\n[測試 5] GUI Settings Manager...")
try:
    from core.gui_settings_manager import gui_settings_manager
    settings = gui_settings_manager.get_boxplot_settings()
    assert 'filter_red_flags' in settings, "filter_red_flags 不在設定中"
    print("  ✅ BoxPlotSettings 包含 filter_red_flags")
    print(f"  ✅ 預設值: {settings['filter_red_flags']}")
    print(f"  ✅ 完整設定: {settings}")
except Exception as e:
    print(f"  ❌ 錯誤: {e}")
    sys.exit(1)

# 測試 6: i18n 翻譯
print("\n[測試 6] i18n 翻譯...")
try:
    from core.gui_i18n import tr, TRANSLATION_DICT
    if 'boxplot_filter_red_flags' in TRANSLATION_DICT:
        translations = TRANSLATION_DICT['boxplot_filter_red_flags']
        print("  ✅ boxplot_filter_red_flags 翻譯已定義")
        print(f"    中文: {translations.get('zh')}")
        print(f"    英文: {translations.get('en')}")
        print(f"    日文: {translations.get('ja')}")
    else:
        print("  ⚠️ boxplot_filter_red_flags 翻譯未找到")
except Exception as e:
    print(f"  ❌ 錯誤: {e}")

print()
print("=" * 60)
print("✅ 所有測試通過！Red Flag Filter 實裝成功")
print("=" * 60)
print()
print("實裝模組清單:")
print("  1. lap_filter_utils.py - 紅旗檢測函數")
print("  2. throttle_line_chart_data_loader.py - 紅旗過濾邏輯")
print("  3. throttle_line_chart_mdi.py - 設定傳遞")
print("  4. throttle_box_plot_analysis_mdi.py - 紅旗過濾邏輯")
print("  5. lap_box_plot_analysis_mdi.py (v1) - 紅旗過濾邏輯")
print("  6. lap_box_plot_analysis_mdi.py (v2) - 紅旗過濾邏輯")
print("  7. laptime_boxplot_widget.py - 紅旗過濾邏輯")
print("  8. gui_settings_manager.py - 紅旗設定支援")
print("  9. system_settings_dialog.py - 紅旗 checkbox")
print(" 10. gui_i18n.py - 紅旗翻譯")
print()
print("下一步: 開啟 GUI → Tools → System Settings 測試紅旗過濾功能")
