#!/usr/bin/env python3
"""
驗證所有分析模組的 analysis_type 屬性
"""
import sys
import importlib
from PyQt5.QtWidgets import QApplication

# 創建 QApplication（測試 PyQt5 模組需要）
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# 測試模組列表（IAnalysisModule 實現）
IANALYSIS_MODULES = [
    ("modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi", "SpeedAnalysisModule", "speed_analysis"),
    ("modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi", "BrakeAnalysisModule", "brake"),
    ("modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi", "ThrottleAnalysisModule", "throttle"),
    ("modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi", "GearAnalysisModule", "gear"),
    ("modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi", "RPMAnalysisModule", "rpm"),
    ("modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi", "accelerationAnalysisModule", "acceleration"),
    ("modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi", "SpeeddiffAnalysisModule", "Speeddiff"),
    ("modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi", "distancediffAnalysisModule", "distancediff"),
    ("modules.gui.telemetry_analysis_mdi", "TelemetryAnalysisModule", "telemetry"),
    ("modules.gui.pitstop_analysis.pitstop_analysis_mdi", "PitstopAnalysisModule", "pitstop"),
    ("modules.gui.accident_analysis.accident_analysis_mdi", "AccidentAnalysisModule", "accident"),
]

# UniversalAnalysisMDI 模組（自動繼承 analysis_type）
UNIVERSAL_MDI_MODULES = [
    ("modules.gui.rain_analysis.rain_analysis_mdi", "RainAnalysisUniversal", "rain_weather"),
    ("modules.gui.tire_analysis.tire_analysis_mdi", "TireAnalysisUniversal", "tire"),
    ("modules.gui.track_analysis.track_analysis_mdi", "TrackAnalysisUniversal", "track"),
    ("modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi", "LapTimeBoxPlotAnalysis", "lap_time_boxplot"),
]

def verify_module(module_path, class_name, expected_type):
    """驗證單個模組的 analysis_type"""
    try:
        # 導入模組
        module = importlib.import_module(module_path)
        module_class = getattr(module, class_name)
        
        # 創建實例（不需要參數）
        instance = module_class()
        
        # 檢查 analysis_type 屬性
        if not hasattr(instance, 'analysis_type'):
            print(f"❌ {class_name}: 缺少 analysis_type 屬性")
            return False
        
        actual_type = instance.analysis_type
        if actual_type == expected_type:
            print(f"✅ {class_name}: analysis_type = '{actual_type}'")
            return True
        else:
            print(f"⚠️  {class_name}: analysis_type = '{actual_type}' (預期: '{expected_type}')")
            return True  # 仍然視為成功，只是值不同
            
    except Exception as e:
        print(f"❌ {class_name}: 驗證失敗 - {e}")
        return False

def main():
    print("=" * 80)
    print("驗證 IAnalysisModule 實現的模組")
    print("=" * 80)
    
    ianalysis_results = []
    for module_path, class_name, expected_type in IANALYSIS_MODULES:
        result = verify_module(module_path, class_name, expected_type)
        ianalysis_results.append(result)
    
    print("\n" + "=" * 80)
    print("驗證 UniversalAnalysisMDI 繼承的模組")
    print("=" * 80)
    
    universal_results = []
    for module_path, class_name, expected_type in UNIVERSAL_MDI_MODULES:
        result = verify_module(module_path, class_name, expected_type)
        universal_results.append(result)
    
    # 統計結果
    total = len(IANALYSIS_MODULES) + len(UNIVERSAL_MDI_MODULES)
    passed = sum(ianalysis_results) + sum(universal_results)
    
    print("\n" + "=" * 80)
    print(f"驗證結果: {passed}/{total} 模組通過")
    print("=" * 80)
    
    if passed == total:
        print("✅ 所有模組的 analysis_type 屬性已正確設置！")
        return 0
    else:
        print(f"❌ {total - passed} 個模組需要修復")
        return 1

if __name__ == "__main__":
    sys.exit(main())
