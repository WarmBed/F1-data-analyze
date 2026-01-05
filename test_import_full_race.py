#!/usr/bin/env python
"""Test import of full_race_tab."""
import sys
import traceback

print("Testing full_race_tab import...")

try:
    from strategy_simulator.gui.results_tabs.full_race_tab import FullRaceTab
    print("✅ FullRaceTab import OK")
except Exception as e:
    print(f"❌ FullRaceTab import FAILED:")
    traceback.print_exc()
    sys.exit(1)

print("\nTesting main_window import...")

try:
    from strategy_simulator.gui.main_window import MainWindow
    print("✅ MainWindow import OK")
except Exception as e:
    print(f"❌ MainWindow import FAILED:")
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All imports successful!")
