#!/usr/bin/env python3
"""
Test script for Long Run Calculator integration.
Verifies that strategy simulator correctly uses main GUI's LongRunCalculator.
"""

import sys

# Use a custom print that goes to stderr to bypass logger patch
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

from strategy_simulator.data.longrun_loader import (
    LongRunCalculator,
    LongRunLoader,
    LongRunData,
    LapData,
    StintInfo,
    DriverFuelSettings,
    HAS_MAIN_GUI_CALCULATOR
)

def test_integration():
    eprint("=" * 60)
    eprint("Long Run Calculator Integration Test")
    eprint("=" * 60)
    
    # Test 1: Check if main GUI calculator is available
    eprint("\n[Test 1] Main GUI Calculator availability")
    eprint(f"  HAS_MAIN_GUI_CALCULATOR: {HAS_MAIN_GUI_CALCULATOR}")
    
    # Test 2: Create calculator and check delegation
    eprint("\n[Test 2] Calculator initialization")
    calc = LongRunCalculator()
    eprint(f"  Using main GUI: {calc._use_main_gui}")
    if calc._main_calculator:
        eprint(f"  Main calculator type: {type(calc._main_calculator).__name__}")
        eprint(f"  Main calculator module: {type(calc._main_calculator).__module__}")
    
    # Test 3: Load mock data
    eprint("\n[Test 3] Data loading")
    mock_data = {
        'data': {
            'drivers': {
                'VER': {
                    'laps': [
                        {'LapNumber': i, 'LapTime': 91.0 + i * 0.08, 
                         'Stint': 1, 'Compound': 'SOFT', 'TyreLife': i,
                         'IsAccurate': True}
                        for i in range(1, 12)  # 11 laps
                    ]
                },
                'LEC': {
                    'laps': [
                        {'LapNumber': i, 'LapTime': 91.2 + i * 0.10, 
                         'Stint': 1, 'Compound': 'MEDIUM', 'TyreLife': i,
                         'IsAccurate': True}
                        for i in range(1, 10)  # 9 laps
                    ]
                }
            }
        }
    }
    
    success = calc.load_api_data(mock_data)
    eprint(f"  Load success: {success}")
    eprint(f"  Drivers loaded: {calc.get_driver_codes()}")
    
    # Test 4: Stint detection
    eprint("\n[Test 4] Stint detection")
    stints = calc.detect_long_runs(min_laps=4)
    eprint(f"  Stints detected: {len(stints)}")
    for stint in stints:
        eprint(f"    - {stint.driver_code}: {stint.compound}, "
              f"laps {stint.start_lap}-{stint.end_lap} "
              f"(is_long_run={stint.is_long_run})")
    
    # Test 5: Check class origins
    eprint("\n[Test 5] Class origins")
    eprint(f"  LapData from: {LapData.__module__}")
    eprint(f"  StintInfo from: {StintInfo.__module__}")
    eprint(f"  DriverFuelSettings from: {DriverFuelSettings.__module__}")
    
    eprint("\n" + "=" * 60)
    eprint("All tests completed!")
    eprint("=" * 60)
    
    return success


if __name__ == "__main__":
    test_integration()
