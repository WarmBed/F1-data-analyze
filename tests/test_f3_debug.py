#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Function 3 - Driver Fastest Pitstop Ranking"""

import sys
import os

# Set UTF-8 encoding for output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("[TEST] Function 3 - Driver Fastest Pitstop Ranking")
print("=" * 80)

try:
    print("\n[IMPORT] Loading modules...")
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
    
    print("[SUCCESS] Modules imported")
    
    # Create data loader
    print("\n[INIT] Creating data loader...")
    data_loader = CompatibleF1DataLoader()
    
    # Load race data
    print("\n[LOAD] Loading 2025 United States R data...")
    success = data_loader.load_race_data(2025, "United States", "R")
    
    if not success:
        print("[ERROR] Failed to load data")
        sys.exit(1)
    
    print("[SUCCESS] Data loaded")
    
    # Create function mapper
    print("\n[INIT] Creating function mapper...")
    mapper = F1AnalysisFunctionMapper(
        data_loader=data_loader,
        driver="VER",
        driver2="LEC"
    )
    
    # Execute function 3
    print("\n[EXECUTE] Running function 3...")
    result = mapper._execute_driver_fastest_pitstop_ranking(show_detailed_output=True)
    
    if result and result.get("success"):
        print("\n[SUCCESS] Function 3 completed!")
        data = result.get("data", [])
        print(f"[RESULT] Found {len(data)} driver pitstop records")
        
        if data:
            print("\n[TOP 5]")
            for i, item in enumerate(data[:5], 1):
                driver = item.get('driver', 'N/A')
                team = item.get('team', 'N/A')
                time = item.get('fastest_time', 0)
                print(f"  {i}. {driver} ({team}): {time:.1f}s")
    else:
        print("\n[ERROR] Function 3 failed")
        print(f"[RESULT] {result}")
        
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("[TEST] Completed")
print("=" * 80)
