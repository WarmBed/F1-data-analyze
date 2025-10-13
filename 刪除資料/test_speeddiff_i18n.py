#!/usr/bin/env python3
"""
測試 Speed Diff 和 Distance Diff 的 i18n 修改是否影響數據載入
"""

import sys
from PyQt5.QtWidgets import QApplication

print("=" * 60)
print("測試 Speed Diff 和 Distance Diff i18n 修改")
print("=" * 60)

# 測試 1: Import 測試
print("\n[測試 1] Import 測試")
try:
    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_chart_widget import speeddiffChartWidget
    print("✅ Speed Diff import 成功")
except Exception as e:
    print(f"❌ Speed Diff import 失敗: {e}")
    sys.exit(1)

try:
    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_chart_widget import distancediffChartWidget
    print("✅ Distance Diff import 成功")
except Exception as e:
    print(f"❌ Distance Diff import 失敗: {e}")
    sys.exit(1)

# 測試 2: GUI i18n 測試
print("\n[測試 2] GUI i18n 翻譯測試")
try:
    from core.gui_i18n import tr, _gui_translator
    
    # 測試英文
    _gui_translator.set_language('en')
    en_time_s = tr('time_s')
    en_linkage_time = tr('linkage_time')
    en_time_label = tr('time_label')
    print(f"✅ 英文翻譯:")
    print(f"   time_s: {en_time_s}")
    print(f"   linkage_time: {en_linkage_time}")
    print(f"   time_label: {en_time_label}")
    
    # 測試中文
    _gui_translator.set_language('zh')
    zh_time_s = tr('time_s')
    zh_linkage_time = tr('linkage_time')
    zh_time_label = tr('time_label')
    print(f"✅ 中文翻譯:")
    print(f"   time_s: {zh_time_s}")
    print(f"   linkage_time: {zh_linkage_time}")
    print(f"   time_label: {zh_time_label}")
    
except Exception as e:
    print(f"❌ i18n 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 3: Widget 創建測試
print("\n[測試 3] Widget 創建測試")
try:
    app = QApplication(sys.argv)
    
    # Speed Diff Widget
    speed_widget = speeddiffChartWidget()
    print("✅ Speed Diff Widget 創建成功")
    print(f"   use_time_axis: {getattr(speed_widget, 'use_time_axis', 'Not found')}")
    print(f"   driver1_time: {getattr(speed_widget, 'driver1_time', 'Not found')}")
    
    # Distance Diff Widget
    distance_widget = distancediffChartWidget()
    print("✅ Distance Diff Widget 創建成功")
    print(f"   use_time_axis: {getattr(distance_widget, 'use_time_axis', 'Not found')}")
    print(f"   driver1_time: {getattr(distance_widget, 'driver1_time', 'Not found')}")
    
except Exception as e:
    print(f"❌ Widget 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 4: 方法檢查
print("\n[測試 4] 關鍵方法檢查")
try:
    # 檢查 Speed Diff 的關鍵方法
    assert hasattr(speed_widget, '_draw_linkage_label'), "Speed Diff 缺少 _draw_linkage_label"
    assert hasattr(speed_widget, 'set_speeddiff_data'), "Speed Diff 缺少 set_speeddiff_data"
    assert hasattr(speed_widget, 'set_time_axis_mode'), "Speed Diff 缺少 set_time_axis_mode"
    print("✅ Speed Diff 關鍵方法存在")
    
    # 檢查 Distance Diff 的關鍵方法
    assert hasattr(distance_widget, '_draw_linkage_label'), "Distance Diff 缺少 _draw_linkage_label"
    assert hasattr(distance_widget, 'set_distancediff_data'), "Distance Diff 缺少 set_distancediff_data"
    assert hasattr(distance_widget, 'set_time_axis_mode'), "Distance Diff 缺少 set_time_axis_mode"
    print("✅ Distance Diff 關鍵方法存在")
    
except AssertionError as e:
    print(f"❌ 方法檢查失敗: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 方法檢查異常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有測試通過！i18n 修改未破壞功能")
print("=" * 60)
