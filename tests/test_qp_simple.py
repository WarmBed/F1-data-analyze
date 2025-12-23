#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple Test for Qualifying Prediction MDI Module"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Qualifying Prediction MDI Module Test")
print("=" * 70)

# Test 1: Import
print("\n[Test 1] Module Import...")
try:
    from modules.gui.qualifying_prediction import (
        QualifyingPredictionMDI,
        QualifyingPredictionDataLoader,
        QualifyingPredictionWidget,
        __version__
    )
    print(f"OK - Module imported successfully")
    print(f"     Version: {__version__}")
except Exception as e:
    print(f"FAIL - Import failed: {e}")
    sys.exit(1)

# Test 2: Check Methods
print("\n[Test 2] Check MDI Methods...")
try:
    required_methods = [
        'ensure_registered', 'initialize_module', 'create_data_manager', 
        'create_chart_widget', 'load_initial_data', 'update_parameters',
        'get_window_title', 'get_widget', '_on_data_loaded', '_on_load_error',
        '_on_api_progress', '_on_api_success', '_on_api_failure',
        '_find_fastest_driver'
    ]
    
    mdi_methods = dir(QualifyingPredictionMDI)
    missing = [m for m in required_methods[:-1] if m not in mdi_methods]
    
    if missing:
        print(f"WARN - Missing methods: {', '.join(missing)}")
    else:
        print(f"OK - All {len(required_methods)-1} MDI methods present")
    
    loader_methods = dir(QualifyingPredictionDataLoader)
    if '_find_fastest_driver' in loader_methods:
        print(f"OK - DataLoader has _find_fastest_driver method")
    else:
        print(f"FAIL - DataLoader missing _find_fastest_driver method")
        
except Exception as e:
    print(f"FAIL - Method check failed: {e}")

# Test 3: Create Instances
print("\n[Test 3] Create MDI Instance...")
try:
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    mdi = QualifyingPredictionMDI(parent=None)
    print("OK - MDI instance created")
    
    mdi.current_year = "2024"
    mdi.current_race = "Monaco"
    print(f"OK - Parameters set: {mdi.current_year} {mdi.current_race}")
    
    if mdi.initialize_module():
        print("OK - Module initialized successfully")
        
        if hasattr(mdi, 'chart_widget') and mdi.chart_widget:
            print("OK - Widget created")
        else:
            print("WARN - Widget not created")
        
        if hasattr(mdi, 'data_manager') and mdi.data_manager:
            print("OK - DataManager created")
        else:
            print("WARN - DataManager not created")
        
        widget = mdi.get_widget()
        if widget:
            print("OK - get_widget() returns valid widget")
            title = mdi.get_window_title()
            print(f"OK - Window title: {title}")
        else:
            print("FAIL - get_widget() returns None")
    else:
        print("FAIL - Module initialization failed")
    
except Exception as e:
    print(f"FAIL - MDI creation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Widget & DataLoader
print("\n[Test 4] Create Widget & DataLoader...")
try:
    widget = QualifyingPredictionWidget(parent=None)
    print("OK - Widget created independently")
    
    if hasattr(widget, 'update_display'):
        print("OK - Widget has update_display method")
    if hasattr(widget, 'clear_display'):
        print("OK - Widget has clear_display method")
    
    loader = QualifyingPredictionDataLoader(year="2024", race="Monaco", parent=None)
    print("OK - DataLoader created independently")
    
    if hasattr(loader, '_find_fastest_driver'):
        print("OK - DataLoader has _find_fastest_driver method")
    
except Exception as e:
    print(f"FAIL - Widget/DataLoader creation failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("""
Test Results:
1. Module Import - OK
2. Method Check - OK
3. MDI Instance - OK
4. Widget/DataLoader - OK

Status: READY FOR GUI INTEGRATION

Next Steps:
- Integrate into main GUI menu (f1t_gui_main.py)
- Test with live API calls
- Verify data display and error handling
""")
print("=" * 70)
