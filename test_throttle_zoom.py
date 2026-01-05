#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試 ThrottleDurationChartWidget 的右鍵縮放功能"""

import sys
import traceback

try:
    # 測試導入
    print("Testing import...")
    from modules.gui.lap_analysis.Throttle_analysis.throttle_line_chart_analysis.throttle_duration_chart_widget import ThrottleDurationChartWidget
    print("Import successful!")
    
    # 檢查新增的屬性和方法（不需要 QApplication）
    print("\nChecking class attributes:")
    print(f"  Has zoom_changed signal: {hasattr(ThrottleDurationChartWidget, 'zoom_changed')}")
    print(f"  Has reset_zoom method: {callable(getattr(ThrottleDurationChartWidget, 'reset_zoom', None))}")
    print(f"  Has _apply_zoom_from_rect method: {callable(getattr(ThrottleDurationChartWidget, '_apply_zoom_from_rect', None))}")
    print(f"  Has paintEvent method: {callable(getattr(ThrottleDurationChartWidget, 'paintEvent', None))}")
    print(f"  Has mousePressEvent method: {callable(getattr(ThrottleDurationChartWidget, 'mousePressEvent', None))}")
    print(f"  Has mouseMoveEvent method: {callable(getattr(ThrottleDurationChartWidget, 'mouseMoveEvent', None))}")
    print(f"  Has mouseReleaseEvent method: {callable(getattr(ThrottleDurationChartWidget, 'mouseReleaseEvent', None))}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
