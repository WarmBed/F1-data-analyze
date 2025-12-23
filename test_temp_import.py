#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試 temp_analysis 模組導入"""

import sys

def test_import():
    print("Testing temp_analysis module import...")
    try:
        from modules.gui.race_analysis.temp import (
            TempAnalysisModule, 
            TempAnalysisUniversal, 
            TempAnalysisDataManager, 
            TempAnalysisChartWidget
        )
        print("SUCCESS: All temp_analysis classes imported correctly!")
        print(f"  - TempAnalysisModule: {TempAnalysisModule}")
        print(f"  - TempAnalysisUniversal: {TempAnalysisUniversal}")
        print(f"  - TempAnalysisDataManager: {TempAnalysisDataManager}")
        print(f"  - TempAnalysisChartWidget: {TempAnalysisChartWidget}")
        return True
    except Exception as e:
        print(f"ERROR: Import failed - {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)
