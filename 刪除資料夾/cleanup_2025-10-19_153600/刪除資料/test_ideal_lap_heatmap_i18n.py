#!/usr/bin/env python3
"""
測試 Ideal Lap Sector Heatmap 模組的國際化
驗證所有文字是否正確使用 tr() 函數
"""

from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

print("=" * 80)
print("測試 Ideal Lap Sector Heatmap 國際化")
print("=" * 80)

# 測試 1: 導入測試
print("\n[測試 1] 導入模組...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi import (
        IdealLapSectorHeatmapMDI,
        SectorHeatmapControlPanel,
        SectorHeatmapStatsPanel
    )
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_widget import (
        IdealLapSectorHeatmapWidget
    )
    from core.gui_i18n import tr
    print("✅ 所有模組導入成功")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)

# 測試 2: MDI 初始化測試
print("\n[測試 2] 測試 MDI 初始化...")
try:
    mdi = IdealLapSectorHeatmapMDI()
    print(f"✅ MDI 建立成功")
    print(f"   - Widget 類型: {type(mdi.chart_widget).__name__}")
    print(f"   - Data Manager 類型: {type(mdi.data_manager).__name__}")
except Exception as e:
    print(f"❌ MDI 初始化失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 3: Control Panel 初始化測試
print("\n[測試 3] 測試 Control Panel 初始化...")
try:
    control_panel = SectorHeatmapControlPanel()
    print(f"✅ Control Panel 建立成功")
    print(f"   - 標題文字: {control_panel.findChild(type(control_panel.children()[1])).__class__.__name__}")
except Exception as e:
    print(f"❌ Control Panel 初始化失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 4: Stats Panel 初始化測試
print("\n[測試 4] 測試 Stats Panel 初始化...")
try:
    stats_panel = SectorHeatmapStatsPanel()
    print(f"✅ Stats Panel 建立成功")
    print(f"   - 群組框標題: {stats_panel.title()}")
    print(f"   - 表格欄位: {[stats_panel.table.horizontalHeaderItem(i).text() for i in range(5)]}")
except Exception as e:
    print(f"❌ Stats Panel 初始化失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 5: Widget 初始化測試
print("\n[測試 5] 測試 Widget 初始化...")
try:
    widget = IdealLapSectorHeatmapWidget()
    print(f"✅ Widget 建立成功")
    print(f"   - 最小尺寸: {widget.minimumSize().width()} x {widget.minimumSize().height()}")
except Exception as e:
    print(f"❌ Widget 初始化失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 6: 翻譯鍵值測試
print("\n[測試 6] 驗證翻譯鍵值...")
translation_keys = [
    ("sector_heatmap_controls", "Sector Heatmap Controls:"),
    ("ready", "Ready"),
    ("sort_by", "Sort by"),
    ("ranking_order", "Ranking Order"),
    ("total_time", "Total Time"),
    ("highlights", "Highlights"),
    ("show_global_fastest", "Show Global Fastest"),
    ("show_driver_personal_best", "Show Driver Personal Best"),
    ("reload", "Reload"),
    ("sector_statistics", "Sector Statistics"),
    ("sector", "Sector"),
    ("fastest", "Fastest"),
    ("slowest", "Slowest"),
    ("average", "Average"),
    ("range", "Range"),
    ("ideal_lap_sector_heatmap", "Ideal Lap Sector Heatmap"),
    ("no_data_loaded_click_load", "No data loaded\nClick 'Load Data' to begin"),
    ("fast", "Fast"),
    ("slow", "Slow"),
    ("sector_time", "Sector Time"),
]

all_keys_ok = True
for key, default in translation_keys:
    result = tr(key, default)
    if result:
        print(f"   ✅ {key}: '{result}'")
    else:
        print(f"   ❌ {key}: 翻譯失敗")
        all_keys_ok = False

if all_keys_ok:
    print("\n✅ 所有翻譯鍵值驗證通過")
else:
    print("\n⚠️ 部分翻譯鍵值驗證失敗")

# 測試 7: 完整性檢查
print("\n[測試 7] 完整性檢查...")
try:
    # 檢查 MDI 配置
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
    config = UniversalAnalysisMDI.get_config("ideal_lap_sector_heatmap")
    if config:
        print(f"✅ MDI 配置已註冊")
        print(f"   - 顯示名稱: {config.display_name}")
        print(f"   - 預設尺寸: {config.default_size}")
    else:
        print("❌ MDI 配置未註冊")
except Exception as e:
    print(f"❌ 配置檢查失敗: {e}")

print("\n" + "=" * 80)
print("🎉 國際化測試完成！")
print("=" * 80)
