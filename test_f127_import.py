"""測試 F127 模組導入"""
import sys
print("Python version:", sys.version)
print("Starting import test...")

try:
    print("Step 1: Testing basic imports...")
    from pathlib import Path
    print("  Path imported OK")
    
    print("Step 2: Testing module import...")
    from CLI_modules.cli.analyzer import live_timing_traffic_distance_analysis
    print("  Module imported OK")
    
    print("Step 3: Testing function import...")
    from CLI_modules.cli.analyzer.live_timing_traffic_distance_analysis import analyze_live_timing_traffic_distance
    print("  Function imported OK")
    
    print("\nAll imports successful!")
    
except Exception as e:
    import traceback
    print(f"\nError: {type(e).__name__}: {e}")
    traceback.print_exc()
