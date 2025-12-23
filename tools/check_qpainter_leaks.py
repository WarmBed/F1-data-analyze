"""
批量檢查並報告所有 QPainter 未正確結束的 paintEvent

這個問題會導致 Qt 警告：
"QBackingStore::endPaint() called with active painter; did you forget to destroy it or call QPainter::end() on it?"
"""

import os
import re

# 需要檢查的檔案列表
files_to_check = [
    "modules/gui/Throttle_analysis/throttle_line_chart_analysis/linked_chart_widget.py",
    "modules/gui/universal_chart_widget.py",
    "modules/gui/tire_analysis/tire_analysis_chart_widget.py",
    "modules/gui/track_analysis/track_map_widget.py",
    "modules/gui/track_analysis/track_analysis_module.py",
    "modules/gui/lap_box_plot_analysis/lap_box_plot_chart_widget.py",
    "modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py",
    "modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_chart_widget.py",
    "modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py",
    "modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_chart_widget.py",
    "modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py",
    "modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py",
    "modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py",
    "modules/gui/base/universal_chart_widget_base.py",
    "modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_chart_widget.py",
    "modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_chart_widget.py",
    "modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py",
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_chart_widget.py",
]

print("=" * 80)
print("QPainter 資源洩漏檢查報告")
print("=" * 80)
print()

issues_found = []

for file_path in files_to_check:
    if not os.path.exists(file_path):
        print(f"⚠️  檔案不存在: {file_path}")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 搜尋 paintEvent 方法
    paint_event_pattern = r'def paintEvent\(self, event\):.*?(?=\n    def |\nclass |\Z)'
    matches = list(re.finditer(paint_event_pattern, content, re.DOTALL))
    
    if not matches:
        continue
    
    for match in matches:
        paint_event_code = match.group(0)
        
        # 檢查是否有 painter = QPainter(self)
        if 'painter = QPainter(self)' not in paint_event_code:
            continue
        
        # 檢查是否有 painter.end() 或 finally 區塊
        has_painter_end = 'painter.end()' in paint_event_code
        has_finally = 'finally:' in paint_event_code
        
        if not has_painter_end and not has_finally:
            # 找到問題！
            # 取得行號
            line_num = content[:match.start()].count('\n') + 1
            
            issues_found.append({
                'file': file_path,
                'line': line_num,
                'has_end': has_painter_end,
                'has_finally': has_finally
            })
            
            print(f"❌ {file_path}")
            print(f"   Line {line_num}: paintEvent 中 QPainter 沒有正確結束")
            print()

print("=" * 80)
print(f"檢查完成！找到 {len(issues_found)} 個問題")
print("=" * 80)
print()

if issues_found:
    print("建議修復方式：")
    print()
    print("在 paintEvent 方法中，將所有繪圖程式碼包裹在 try-finally 區塊中：")
    print()
    print("```python")
    print("def paintEvent(self, event):")
    print("    painter = QPainter(self)")
    print("    try:")
    print("        # 所有繪圖程式碼...")
    print("        painter.setRenderHint(QPainter.Antialiasing)")
    print("        # ...")
    print("    finally:")
    print("        # 🔑 確保 painter 總是被正確結束")
    print("        painter.end()")
    print("```")
    print()
    print("或使用 context manager (需要 Python 3.10+):")
    print()
    print("```python")
    print("def paintEvent(self, event):")
    print("    with QPainter(self) as painter:")
    print("        # 所有繪圖程式碼...")
    print("        painter.setRenderHint(QPainter.Antialiasing)")
    print("        # ...")
    print("```")
else:
    print("✅ 所有檢查的檔案都正確處理了 QPainter！")
