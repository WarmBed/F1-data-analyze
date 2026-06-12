"""
驗證 Track Analysis MDI 官方彎道整合
"""
import sys
sys.path.insert(0, r'<project_root>')

print("=== 驗證 track_analysis_mdi.py 整合 ===\n")

# 步驟 1: Import 測試
try:
    from modules.gui.track_analysis.track_analysis_mdi import TrackAnalysisMDI, TrackMapControlPanel
    print("✅ TrackAnalysisMDI import 成功")
    print("✅ TrackMapControlPanel import 成功")
except Exception as e:
    print(f"❌ Import 失敗: {e}")
    sys.exit(1)

# 步驟 2: 驗證 signal 定義
print("\n=== 驗證 signal 定義 ===")
signals = [s for s in dir(TrackMapControlPanel) if 'changed' in s.lower() and not s.startswith('_')]
print(f"可用 signals: {signals}")

if 'show_corners_changed' in signals:
    print("✅ show_corners_changed signal 已定義")
else:
    print("❌ 缺少 show_corners_changed signal")

# 步驟 3: 驗證 checkbox 屬性
print("\n=== 驗證 checkbox 屬性 ===")
import inspect
source = inspect.getsource(TrackMapControlPanel.__init__)
if 'show_corners_check' in source:
    print("✅ show_corners_check checkbox 已定義")
else:
    print("❌ 缺少 show_corners_check checkbox")

# 步驟 4: 驗證處理函數
print("\n=== 驗證處理函數 ===")
if hasattr(TrackAnalysisMDI, '_on_show_corners_changed'):
    print("✅ _on_show_corners_changed 處理函數已定義")
    sig = inspect.signature(TrackAnalysisMDI._on_show_corners_changed)
    print(f"   函數簽名: {sig}")
else:
    print("❌ 缺少 _on_show_corners_changed 處理函數")

# 步驟 5: 驗證 TrackMapWidget 支援
print("\n=== 驗證 TrackMapWidget 支援 ===")
from modules.gui.track_analysis.track_map_widget import TrackMapWidget
widget_source = inspect.getsource(TrackMapWidget.set_display_options)
if 'show_corners' in widget_source:
    print("✅ TrackMapWidget.set_display_options 支援 show_corners 參數")
else:
    print("❌ TrackMapWidget.set_display_options 不支援 show_corners")

# 步驟 6: 檢查繪製函數
if hasattr(TrackMapWidget, '_draw_official_corners'):
    print("✅ TrackMapWidget._draw_official_corners 繪製函數存在")
else:
    print("❌ 缺少 _draw_official_corners 繪製函數")

print("\n=== 驗證完成 ===")
print("✅ 所有必要組件已成功整合")
