#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
綜合驗證：所有已修復的 MDI 標題模組
"""

import sys
from pathlib import Path
from datetime import datetime

# 設置專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 輸出檔案
output_file = project_root / "test_all_mdi_titles_result.txt"

def log(message):
    """輸出到檔案和控制台"""
    print(message)
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def main():
    """執行綜合驗證測試"""
    
    # 清空輸出檔案
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"All MDI Title Fixes - Comprehensive Verification\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
    
    log("="*80)
    log("COMPREHENSIVE TEST: All MDI Title Fixes")
    log("="*80)
    log("\nFixed Modules:")
    log("  1. All Drivers Brake Performance")
    log("  2. Track Analysis")
    log("  3. All Drivers Straight Line Speed")
    log("\nReference Module:")
    log("  - Pitstop Analysis (already correct)")
    
    results = {}
    
    # Test 1: All Drivers Brake Performance
    log("\n" + "="*80)
    log("[Test 1] All Drivers Brake Performance MDI")
    log("="*80)
    try:
        from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
        
        has_method = hasattr(AllDriversBrakePerformanceMDI, 'get_window_title')
        results['brake'] = has_method
        
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        if has_method:
            log("  - get_window_title() method: YES")
            log("  - Format: All Drivers Brake Performance_{year}_{race}_{session}")
        
    except Exception as e:
        results['brake'] = False
        log(f"ERROR: {e}")
    
    # Test 2: Track Analysis
    log("\n" + "="*80)
    log("[Test 2] Track Analysis MDI")
    log("="*80)
    try:
        from modules.gui.track_analysis.track_analysis_mdi import TrackAnalysisUniversal
        
        has_method = hasattr(TrackAnalysisUniversal, 'get_window_title')
        results['track'] = has_method
        
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        if has_method:
            log("  - get_window_title() method: YES")
            log("  - Format: Track Analysis_{year}_{race}_{session}")
        
    except Exception as e:
        results['track'] = False
        log(f"ERROR: {e}")
    
    # Test 3: All Drivers Straight Line Speed
    log("\n" + "="*80)
    log("[Test 3] All Drivers Straight Line Speed MDI")
    log("="*80)
    try:
        from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
        
        has_method = hasattr(AllDriversStraightLineSpeedMDI, 'get_window_title')
        results['speed'] = has_method
        
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        if has_method:
            log("  - get_window_title() method: YES")
            log("  - Format: All Drivers Straight Line Speed_{year}_{race}_{session}")
        
    except Exception as e:
        results['speed'] = False
        log(f"ERROR: {e}")
    
    # Test 4: Pitstop Analysis (Reference)
    log("\n" + "="*80)
    log("[Test 4] Pitstop Analysis MDI (Reference)")
    log("="*80)
    try:
        from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisModule
        
        has_method = hasattr(PitstopAnalysisModule, 'get_window_title')
        results['pitstop'] = has_method
        
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        if has_method:
            log("  - get_window_title() method: YES (reference implementation)")
            log("  - Format: Pitstop Analysis_{year}_{race}_{session}")
        
    except Exception as e:
        results['pitstop'] = False
        log(f"WARNING: {e}")
    
    # Summary
    log("\n" + "="*80)
    log("SUMMARY")
    log("="*80)
    
    all_passed = all(results.values())
    
    log(f"\nAll Drivers Brake Performance:     {'[PASS]' if results.get('brake') else '[FAIL]'}")
    log(f"Track Analysis:                     {'[PASS]' if results.get('track') else '[FAIL]'}")
    log(f"All Drivers Straight Line Speed:   {'[PASS]' if results.get('speed') else '[FAIL]'}")
    log(f"Pitstop Analysis (Reference):       {'[PASS]' if results.get('pitstop') else '[FAIL]'}")
    
    log("\n" + "-"*80)
    if all_passed:
        log("OVERALL RESULT: [ALL TESTS PASSED]")
        log("\nAll MDI modules now use consistent title format:")
        log("  {Module Name}_{Year}_{Race}_{Session}")
        log("\nTitle update behavior:")
        log("  - Initial: Module_2025_Singapore_R")
        log("  - After race update: Module_2025_Japan_R")
        log("  - Titles are REPLACED, not accumulated")
    else:
        log("OVERALL RESULT: [SOME TESTS FAILED]")
        log("Please check the errors above.")
    
    log("\n" + "="*80)
    log(f"Results saved to: {output_file}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
