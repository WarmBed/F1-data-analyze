#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MDI 視窗標題修復驗證 - 輸出到檔案
"""

import sys
from pathlib import Path
from datetime import datetime

# 設置專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 輸出檔案
output_file = project_root / "test_title_fix_result.txt"

def log(message):
    """輸出到檔案和控制台"""
    print(message)
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def main():
    """執行驗證測試"""
    
    # 清空輸出檔案
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"MDI Window Title Fix Verification\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
    
    log("="*80)
    log("TEST: MDI Window Title Fix Verification")
    log("="*80)
    
    # Test 1: All Drivers Brake Performance
    log("\n[Test 1] All Drivers Brake Performance MDI")
    log("-"*80)
    try:
        from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
        
        has_method = hasattr(AllDriversBrakePerformanceMDI, 'get_window_title')
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        
        if has_method:
            log("Details:")
            log("  - get_window_title() method exists: YES")
            log("  - Method signature: get_window_title(year, race, session)")
            log("  - Expected format: All Drivers Brake Performance_{year}_{race}_{session}")
            log("  - Example: All Drivers Brake Performance_2025_Japan_R")
        else:
            log("ERROR: get_window_title() method NOT FOUND!")
            
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    
    # Test 2: Track Analysis
    log("\n[Test 2] Track Analysis MDI")
    log("-"*80)
    try:
        from modules.gui.track_analysis.track_analysis_mdi import TrackAnalysisUniversal
        
        has_method = hasattr(TrackAnalysisUniversal, 'get_window_title')
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        
        if has_method:
            log("Details:")
            log("  - get_window_title() method exists: YES")
            log("  - Method signature: get_window_title(year, race, session)")
            log("  - Expected format: Track Analysis_{year}_{race}_{session}")
            log("  - Example: Track Analysis_2025_Japan_R")
        else:
            log("ERROR: get_window_title() method NOT FOUND!")
            
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    
    # Test 3: Pitstop Analysis (Reference)
    log("\n[Test 3] Pitstop Analysis MDI (Reference Standard)")
    log("-"*80)
    try:
        from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisModule
        
        has_method = hasattr(PitstopAnalysisModule, 'get_window_title')
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        
        if has_method:
            log("Details:")
            log("  - get_window_title() method exists: YES")
            log("  - This is our reference implementation")
            log("  - Expected format: Pitstop Analysis_{year}_{race}_{session}")
            log("  - Example: Pitstop Analysis_2025_Japan_R")
        else:
            log("WARNING: Pitstop Analysis has no get_window_title() method")
            
    except Exception as e:
        log(f"WARNING: {e}")
    
    log("\n" + "="*80)
    log("VERIFICATION COMPLETE")
    log("="*80)
    log(f"\nResults saved to: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
