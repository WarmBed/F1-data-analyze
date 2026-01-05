#!/usr/bin/env python3
"""Simple import test"""
import sys
print("Step 1: Starting", flush=True)

try:
    print("Step 2: Importing logger...", flush=True)
    from core.logger import get_logger
    print("Step 3: Logger imported", flush=True)
    
    print("Step 4: Importing dataclasses...", flush=True)
    from dataclasses import dataclass, field
    print("Step 5: dataclasses imported", flush=True)
    
    print("Step 6: Trying full file...", flush=True)
    # Direct read and exec
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "long_run_calculator",
        "modules/gui/long_run_analysis/long_run_calculator.py"
    )
    print("Step 7: Spec created", flush=True)
    
    module = importlib.util.module_from_spec(spec)
    print("Step 8: Module from spec", flush=True)
    
    sys.modules["long_run_calculator"] = module
    spec.loader.exec_module(module)
    print("Step 9: Module executed!", flush=True)
    
    print("SUCCESS!", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
