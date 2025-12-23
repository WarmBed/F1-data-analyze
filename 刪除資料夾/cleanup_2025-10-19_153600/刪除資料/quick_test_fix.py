"""快速測試 3 個修復模組的 use_time_axis 參數"""
import sys
import inspect
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

print("="*60)
print("測試 Throttle、SpeedDiff、DistanceDiff 模組")
print("="*60)

# Throttle
print("\n1. Throttle:")
from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
mdi = ThrottleAnalysisModule()
sig = inspect.signature(mdi.update_lap_parameters)
params = list(sig.parameters.keys())
print(f"   參數: {params}")
print(f"   結果: {'✅ 通過' if 'use_time_axis' in params else '❌ 失敗'}")

# SpeedDiff
print("\n2. SpeedDiff:")
from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule
mdi = SpeeddiffAnalysisModule()
sig = inspect.signature(mdi.update_lap_parameters)
params = list(sig.parameters.keys())
print(f"   參數: {params}")
print(f"   結果: {'✅ 通過' if 'use_time_axis' in params else '❌ 失敗'}")

# DistanceDiff
print("\n3. DistanceDiff:")
from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi import distancediffAnalysisModule
mdi = distancediffAnalysisModule()
sig = inspect.signature(mdi.update_lap_parameters)
params = list(sig.parameters.keys())
print(f"   參數: {params}")
print(f"   結果: {'✅ 通過' if 'use_time_axis' in params else '❌ 失敗'}")

print("\n" + "="*60)
print("測試完成")
print("="*60)
