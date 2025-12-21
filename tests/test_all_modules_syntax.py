#!/usr/bin/env python3
"""
測試所有 GUI 模組的語法和導入
用於驗證修復後的模組是否可以正常導入
"""

import sys
from typing import List, Tuple

# 關鍵模組列表
CRITICAL_MODULES = [
    # Track Analysis
    ("Track Analysis", "modules.gui.track_analysis.track_analysis_module"),
    ("Track Map Widget", "modules.gui.track_analysis.track_map_widget"),
    
    # Rain Analysis
    ("Rain Analysis", "modules.gui.rain_analysis.rain_analysis_module"),
    
    # Tire Analysis
    ("Tire Analysis", "modules.gui.tire_analysis.tire_analysis_module"),
    
    # Pitstop Analysis
    ("Pitstop Analysis", "modules.gui.pitstop_analysis.pitstop_analysis_mdi"),
    
    # Accident Analysis
    ("Accident Analysis", "modules.gui.accident_analysis.accident_analysis_mdi"),
    
    # Driver Race - Detailed Lap Analysis
    ("Detailed Lap Analysis", "modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module"),
    ("Lap Chart Widget", "modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_chart_widget"),
    
    # Throttle Analysis
    ("Throttle Line Chart", "modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module"),
    ("Throttle Box Plot", "modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module"),
    
    # Live Timing
    ("Live Timing Position Processor", "modules.gui.live_timing.core.position_processor"),
    ("Live Timing F1 API Downloader", "modules.gui.live_timing.core.f1_api_downloader"),
]


def test_module_import(name: str, module_path: str) -> Tuple[bool, str]:
    """測試單個模組的導入"""
    try:
        __import__(module_path)
        return True, f"✅ {name}: OK"
    except SyntaxError as e:
        return False, f"❌ {name}: SyntaxError - {e.msg} (line {e.lineno})"
    except ImportError as e:
        return False, f"⚠️  {name}: ImportError - {str(e)}"
    except Exception as e:
        return False, f"❌ {name}: {type(e).__name__} - {str(e)}"


def main():
    print("=" * 80)
    print("F1T GUI 模組語法與導入測試")
    print("=" * 80)
    print()
    
    results: List[Tuple[bool, str]] = []
    
    for name, module_path in CRITICAL_MODULES:
        success, message = test_module_import(name, module_path)
        results.append((success, message))
        print(message)
    
    print()
    print("=" * 80)
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    
    print(f"測試結果: {passed}/{total} 模組通過")
    
    if passed == total:
        print("🎉 所有模組測試通過！")
        return 0
    else:
        print(f"⚠️  {total - passed} 個模組需要修復")
        return 1


if __name__ == "__main__":
    sys.exit(main())
