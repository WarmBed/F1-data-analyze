"""簡單測試 GUI 能否啟動並載入分析模組
"""
import sys
from PyQt5.QtWidgets import QApplication

# 測試導入關鍵模組
print("🔍 測試導入 GUI 核心模組...")
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
    print("✅ UniversalAnalysisMDI 導入成功")
    
    from modules.gui.lap_analysis.speed_analysis_module import SpeedAnalysisModule
    print("✅ SpeedAnalysisModule 導入成功")
    
    from modules.gui.lap_analysis.brake_analysis_module import BrakeAnalysisModule
    print("✅ BrakeAnalysisModule 導入成功")
    
    from modules.gui.lap_analysis.throttle_analysis_module import ThrottleAnalysisModule
    print("✅ ThrottleAnalysisModule 導入成功")
    
    from modules.gui.rain_analysis.rain_analysis_universal import RainAnalysisModule
    print("✅ RainAnalysisModule 導入成功")
    
    print("\n✅ 所有關鍵模組導入成功!")
    print("🎉 導入錯誤已修復!")
    
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
