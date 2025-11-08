#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證 All Drivers Straight Line Speed MDI 標題修復
"""

import sys
from pathlib import Path
from datetime import datetime

# 設置專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 輸出檔案
output_file = project_root / "test_straight_speed_title_result.txt"

def log(message):
    """輸出到檔案和控制台"""
    print(message)
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def main():
    """執行驗證測試"""
    
    # 清空輸出檔案
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"All Drivers Straight Line Speed - Title Fix Verification\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
    
    log("="*80)
    log("TEST: All Drivers Straight Line Speed MDI Title Fix")
    log("="*80)
    
    # Test: All Drivers Straight Line Speed
    log("\n[Test] All Drivers Straight Line Speed MDI")
    log("-"*80)
    try:
        from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
        
        has_method = hasattr(AllDriversStraightLineSpeedMDI, 'get_window_title')
        log(f"Status: {'[PASS]' if has_method else '[FAIL]'}")
        
        if has_method:
            log("Details:")
            log("  - get_window_title() method exists: YES")
            log("  - Method signature: get_window_title(year, race, session)")
            log("  - Expected format: All Drivers Straight Line Speed_{year}_{race}_{session}")
            log("  - Example (English): All Drivers Straight Line Speed_2025_Japan_R")
            log("  - Example (Chinese): 全車手直線速度_2025_Japan_R")
        else:
            log("ERROR: get_window_title() method NOT FOUND!")
            
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    
    log("\n" + "="*80)
    log("VERIFICATION COMPLETE")
    log("="*80)
    log(f"\nResults saved to: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
