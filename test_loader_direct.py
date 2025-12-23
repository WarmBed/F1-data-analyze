#!/usr/bin/env python3
"""Test direct loader file import"""
import sys
import os

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")
sys.path.insert(0, r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

print("Test starting...")
sys.stdout.flush()

# Step 1: Direct file import using exec
print("Step 1: Read loader file content...")
loader_path = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\race_analysis\start_reaction\start_reaction_loader.py"

# Step 2: Import only standard libs and read file
print("\nStep 2: Import standard libs...")
import json
import logging
from pathlib import Path
print("  OK")

# Step 3: Read file content
print("\nStep 3: Read file content (first 50 lines)...")
with open(loader_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()[:50]
for i, line in enumerate(lines[:20], 1):
    print(f"  {i:2d}: {line.rstrip()}")

# Step 4: Try direct import without package __init__
print("\nStep 4: Direct import using importlib...")
sys.stdout.flush()

import importlib.util
spec = importlib.util.spec_from_file_location("start_reaction_loader", loader_path)
loader_module = importlib.util.module_from_spec(spec)
print(f"  Module object created: {loader_module}")
sys.stdout.flush()

print("\nStep 5: Execute module...")
sys.stdout.flush()
spec.loader.exec_module(loader_module)
print("  OK - Module executed")

# Step 6: Create loader
print("\nStep 6: Create loader instance...")
StartReactionDataLoader = loader_module.StartReactionDataLoader
loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
print("  OK")

# Step 7: Load data
print("\nStep 7: Load data...")
data = loader.load_data()
if data:
    print(f"  OK - {len(data.get('drivers', []))} drivers loaded")
else:
    print("  FAIL - No data")

print("\nDone!")
