#!/usr/bin/env python3
"""Test with step-by-step debug"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Step 1: Basic imports", flush=True)
import os
from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QThread, pyqtSignal
print("Step 1: OK", flush=True)

print("Step 2: Testing lazy import...", flush=True)
import importlib.util

def _lazy_import_base_loader():
    """Lazy import UniversalDataLoader to avoid circular import"""
    base_path = os.path.join(os.path.dirname(__file__), "modules", "gui", "base", "universal_data_loader_base.py")
    print(f"  Path: {base_path}", flush=True)
    print(f"  Exists: {os.path.exists(base_path)}", flush=True)
    
    spec = importlib.util.spec_from_file_location(
        "universal_data_loader_base",
        base_path
    )
    print("  Spec created", flush=True)
    
    module = importlib.util.module_from_spec(spec)
    print("  Module from spec", flush=True)
    
    sys.modules["universal_data_loader_base"] = module
    print("  Added to sys.modules", flush=True)
    
    print("  Executing module...", flush=True)
    spec.loader.exec_module(module)
    print("  Module executed", flush=True)
    
    return module.UniversalDataLoader, module.AnalysisConfig

UniversalDataLoader, AnalysisConfig = _lazy_import_base_loader()
print("Step 2: OK", flush=True)

print("ALL TESTS PASSED!", flush=True)
