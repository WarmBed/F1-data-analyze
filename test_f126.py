#!/usr/bin/env python3
"""測試 F126 Live Timing 天氣分析"""
import sys
sys.path.insert(0, '.')

print("Testing F126...")
print("=" * 60)

try:
    from CLI_modules.cli.analyzer.live_timing_weather_analysis import run_live_timing_weather_analysis
    print("[OK] Import successful")
    
    result = run_live_timing_weather_analysis(year=2025, race='Australia', session='R')
    print(f"[RESULT] Success: {result.get('success', 'N/A')}")
    print(f"[RESULT] Message: {result.get('message', 'N/A')}")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
