#!/usr/bin/env python3
"""Test loader import step by step"""
import sys
import os

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

print("Test starting...")
sys.stdout.flush()

# Step 1: Add project to path
print("Step 1: Add project to path")
sys.path.insert(0, r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")
print("  OK")

# Step 2: Test import of loader module file directly
print("\nStep 2: Import loader module...")
sys.stdout.flush()

try:
    import modules.gui.race_analysis.start_reaction.start_reaction_loader as loader_module
    print("  OK - Module imported")
    
    # Step 3: Access the class
    print("\nStep 3: Access StartReactionDataLoader class...")
    StartReactionDataLoader = loader_module.StartReactionDataLoader
    print(f"  OK - Class: {StartReactionDataLoader}")
    
    # Step 4: Create instance
    print("\nStep 4: Create instance for Abu Dhabi 2025...")
    loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
    print("  OK - Instance created")
    
    # Step 5: Load data
    print("\nStep 5: Load data...")
    data = loader.load_data()
    print(f"  OK - Data loaded: {len(data.get('drivers', [])) if data else 0} drivers")
    
except Exception as e:
    print(f"\n  ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
