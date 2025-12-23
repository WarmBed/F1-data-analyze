#!/usr/bin/env python3
"""Simple test - no imports from project modules"""
import sys
print("Test starting...")
sys.stdout.flush()

# Only use standard library
print("Step 1: Standard imports")
import json
import logging
from pathlib import Path
print("  OK")

print("\nStep 2: Test file access")
live_timing_path = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2025\Abu_Dhabi_Race")
print(f"  Path exists: {live_timing_path.exists()}")

print("\nStep 3: List directory")
if live_timing_path.exists():
    files = list(live_timing_path.glob("*.json"))
    print(f"  Found {len(files)} JSON files")
    for f in files[:5]:
        print(f"    - {f.name}")

print("\nDone!")
