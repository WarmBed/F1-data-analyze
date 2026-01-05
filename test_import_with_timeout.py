#!/usr/bin/env python3
"""Test with forced flush and timeout detection"""
import sys
import os
import signal
import threading

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

def timeout_handler():
    print("\n[TIMEOUT] Test took too long!", flush=True)
    os._exit(1)

# Set a 10-second timeout
timer = threading.Timer(10.0, timeout_handler)
timer.start()

try:
    print("[TEST] Step 1: Basic imports", flush=True)
    from typing import Dict, List, Any, Optional, Tuple
    from dataclasses import dataclass, field
    print("[TEST] Step 1: OK", flush=True)
    
    print("[TEST] Step 2: Import long_run_calculator", flush=True)
    from modules.gui.long_run_analysis.long_run_calculator import LongRunCalculator
    print("[TEST] Step 2: OK", flush=True)
    
    print("[TEST] Step 3: Import long_run_data_loader", flush=True)
    from modules.gui.long_run_analysis.long_run_data_loader import LongRunDataLoader
    print("[TEST] Step 3: OK", flush=True)
    
    print("[TEST] Step 4: Import LongRunAnalysis", flush=True)
    from modules.gui.long_run_analysis import LongRunAnalysis
    print("[TEST] Step 4: OK", flush=True)
    
    print("\n[SUCCESS] All imports passed!", flush=True)
    timer.cancel()
    
except Exception as e:
    print(f"\n[ERROR] {e}", flush=True)
    import traceback
    traceback.print_exc()
    timer.cancel()
