"""
追蹤 UniversalAnalysisMDI 匯入鏈的詳細過程
"""

import sys
import importlib.util

# 監控所有模組匯入
original_import = __builtins__.__import__

def tracking_import(name, *args, **kwargs):
    if 'speed_analysis' in name or 'MODULE_FACTORY' in name or 'lap_analysis' in name:
        print(f"  → 偵測到匯入: {name}")
    return original_import(name, *args, **kwargs)

__builtins__.__import__ = tracking_import

print("開始追蹤...")
print("[1] 匯入 core.gui_i18n...")
from core.gui_i18n import tr
print("    [OK] gui_i18n 完成")

print("[2] 匯入 PyQt5...")
from PyQt5.QtWidgets import QWidget
print("    [OK] PyQt5 完成")

print("[3] 匯入 IAnalysisModule...")
from modules.gui.interfaces.analysis_module import IAnalysisModule
print("    [OK] IAnalysisModule 完成")

print("[4] 匯入 UniversalDataLoader...")
from modules.gui.base.universal_data_loader_base import UniversalDataLoader
print("    [OK] UniversalDataLoader 完成")

print("[5] 匯入 UniversalAnalysisMDI（關鍵步驟）...")
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
print("    [OK] UniversalAnalysisMDI 完成")

print("\n[OK] 所有匯入成功完成！")
print(f"已載入的 speed_analysis 相關模組: {[m for m in sys.modules.keys() if 'speed' in m.lower()]}")
