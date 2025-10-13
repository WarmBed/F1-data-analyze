# -*- coding: utf-8 -*-
import sys
import os

# 設置輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*60)
print("[TEST] Starting Module Tests")
print("="*60)

# Test 1: Import
print("\n[TEST 1] Import...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import IdealLapSectorComparisonModule
    print("[OK] Import successful")
    test1_pass = True
except Exception as e:
    print(f"[FAIL] {e}")
    test1_pass = False

# Test 2: Widget methods
print("\n[TEST 2] Widget methods...")
try:
    from PyQt5.QtWidgets import QApplication
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_widget import IdealLapSectorComparisonWidget
    
    app = QApplication.instance() or QApplication(sys.argv)
    w = IdealLapSectorComparisonWidget()
    
    methods = ['draw_comparison_bars', 'clear_chart', 'update_statistics_panel']
    missing = [m for m in methods if not hasattr(w, m)]
    
    if not missing:
        print("[OK] All methods exist:", methods)
        test2_pass = True
    else:
        print(f"[FAIL] Missing methods: {missing}")
        test2_pass = False
except Exception as e:
    print(f"[FAIL] {e}")
    test2_pass = False

# Test 3: MDI methods
print("\n[TEST 3] MDI methods...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI
    
    methods = ['_show_error', '_on_data_loaded', '_on_api_success']
    missing = [m for m in methods if not hasattr(IdealLapSectorComparisonMDI, m)]
    
    if not missing:
        print("[OK] All methods exist:", methods)
        test3_pass = True
    else:
        print(f"[FAIL] Missing methods: {missing}")
        test3_pass = False
except Exception as e:
    print(f"[FAIL] {e}")
    test3_pass = False

# Test 4: _show_error implementation
print("\n[TEST 4] _show_error implementation...")
try:
    import inspect
    source = inspect.getsource(IdealLapSectorComparisonMDI._show_error)
    
    has_chart_widget = 'chart_widget' in source
    has_qmessagebox = 'QMessageBox' in source
    
    if has_chart_widget and has_qmessagebox:
        print("[OK] Correct implementation (uses chart_widget as parent)")
        test4_pass = True
    else:
        print(f"[FAIL] Implementation issue (chart_widget={has_chart_widget}, QMessageBox={has_qmessagebox})")
        test4_pass = False
except Exception as e:
    print(f"[FAIL] {e}")
    test4_pass = False

# Test 5: _on_api_success implementation
print("\n[TEST 5] _on_api_success implementation...")
try:
    source = inspect.getsource(IdealLapSectorComparisonMDI._on_api_success)
    
    calls_on_data_loaded = '_on_data_loaded' in source
    calls_update_chart = 'update_chart' in source
    
    if calls_on_data_loaded and not calls_update_chart:
        print("[OK] Calls _on_data_loaded, not update_chart")
        test5_pass = True
    else:
        print(f"[FAIL] on_data_loaded={calls_on_data_loaded}, update_chart={calls_update_chart}")
        test5_pass = False
except Exception as e:
    print(f"[FAIL] {e}")
    test5_pass = False

# Summary
print("\n" + "="*60)
print("[SUMMARY] Test Results")
print("="*60)
tests = [
    ("Import", test1_pass),
    ("Widget methods", test2_pass),
    ("MDI methods", test3_pass),
    ("_show_error", test4_pass),
    ("_on_api_success", test5_pass)
]

for name, passed in tests:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")

total = len(tests)
passed_count = sum(1 for _, p in tests if p)
print(f"\n{passed_count}/{total} tests passed")

if passed_count == total:
    print("\n[SUCCESS] All tests passed!")
    sys.exit(0)
else:
    print(f"\n[FAILURE] {total - passed_count} test(s) failed")
    sys.exit(1)
