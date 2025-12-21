#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""簡單驗證腳本 - 確認 get_window_title() 方法存在"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("MDI Window Title Fix - Simple Verification")
print("="*60)

# Test 1: Brake Performance
try:
    from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
    has_method = hasattr(AllDriversBrakePerformanceMDI, 'get_window_title')
    print(f"\n1. Brake Performance MDI: {'[PASS]' if has_method else '[FAIL]'}")
    if has_method:
        print("   - get_window_title() method found")
except Exception as e:
    print(f"\n1. Brake Performance MDI: [ERROR] {e}")

# Test 2: Track Analysis
try:
    from modules.gui.track_analysis.track_analysis_mdi import TrackAnalysisUniversal
    has_method = hasattr(TrackAnalysisUniversal, 'get_window_title')
    print(f"\n2. Track Analysis MDI: {'[PASS]' if has_method else '[FAIL]'}")
    if has_method:
        print("   - get_window_title() method found")
except Exception as e:
    print(f"\n2. Track Analysis MDI: [ERROR] {e}")

# Test 3: Pitstop Analysis (reference)
try:
    from modules.gui.pitstop_analysis.pitstop_analysis_mdi import PitstopAnalysisModule
    has_method = hasattr(PitstopAnalysisModule, 'get_window_title')
    print(f"\n3. Pitstop Analysis MDI (reference): {'[PASS]' if has_method else '[FAIL]'}")
    if has_method:
        print("   - get_window_title() method found")
except Exception as e:
    print(f"\n3. Pitstop Analysis MDI: [ERROR] {e}")

print("\n" + "="*60)
print("Verification complete!")
print("="*60)
