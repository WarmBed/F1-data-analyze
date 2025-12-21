"""
MDI Race Parameters Handler - Simple Test
測試 MDI 賽事參數變更處理器功能
"""

import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("="*70)
print("[START] MDI Race Parameters Handler Test")
print("="*70)

# Test 1: Import Verification
print("\n[TEST 1] Import Verification")
print("-"*70)
try:
    from f1t_gui_main import StyleHMainWindow
    print("[OK] StyleHMainWindow imported")
    
    assert hasattr(StyleHMainWindow, 'on_race_parameters_changed'), \
        "[FAIL] on_race_parameters_changed() not found"
    print("[OK] on_race_parameters_changed() exists")
    
    assert hasattr(StyleHMainWindow, '_get_telemetry_analysis_windows'), \
        "[FAIL] _get_telemetry_analysis_windows() not found"
    print("[OK] _get_telemetry_analysis_windows() exists")
    
    print("[PASS] Test 1 Passed")
    test1_passed = True
except Exception as e:
    print(f"[FAIL] Test 1 Failed: {e}")
    import traceback
    traceback.print_exc()
    test1_passed = False

# Test 2: Method Signature Verification
print("\n[TEST 2] Method Signature Verification")
print("-"*70)
try:
    from f1t_gui_main import StyleHMainWindow
    import inspect
    
    sig1 = inspect.signature(StyleHMainWindow.on_race_parameters_changed)
    print(f"[OK] on_race_parameters_changed signature: {sig1}")
    
    sig2 = inspect.signature(StyleHMainWindow._get_telemetry_analysis_windows)
    print(f"[OK] _get_telemetry_analysis_windows signature: {sig2}")
    
    print("[PASS] Test 2 Passed")
    test2_passed = True
except Exception as e:
    print(f"[FAIL] Test 2 Failed: {e}")
    import traceback
    traceback.print_exc()
    test2_passed = False

# Test 3: Signal Connection Verification
print("\n[TEST 3] Signal Connection Verification")
print("-"*70)
try:
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check on_year_changed() calls on_race_parameters_changed()
    if 'def on_year_changed(self' in content:
        year_section = content.split('def on_year_changed(self')[1].split('def ')[0]
        assert 'self.on_race_parameters_changed()' in year_section, \
            "[FAIL] on_year_changed() does not call on_race_parameters_changed()"
        print("[OK] on_year_changed() calls on_race_parameters_changed()")
    
    # Check on_race_changed() calls on_race_parameters_changed()
    if 'def on_race_changed(self' in content:
        race_section = content.split('def on_race_changed(self')[1].split('def ')[0]
        assert 'self.on_race_parameters_changed()' in race_section, \
            "[FAIL] on_race_changed() does not call on_race_parameters_changed()"
        print("[OK] on_race_changed() calls on_race_parameters_changed()")
    
    # Check on_session_changed() calls on_race_parameters_changed()
    if 'def on_session_changed(self' in content:
        session_section = content.split('def on_session_changed(self')[1].split('def ')[0]
        assert 'self.on_race_parameters_changed()' in session_section, \
            "[FAIL] on_session_changed() does not call on_race_parameters_changed()"
        print("[OK] on_session_changed() calls on_race_parameters_changed()")
    
    print("[PASS] Test 3 Passed")
    test3_passed = True
except Exception as e:
    print(f"[FAIL] Test 3 Failed: {e}")
    import traceback
    traceback.print_exc()
    test3_passed = False

# Test 4: Telemetry Window Filter Logic
print("\n[TEST 4] Telemetry Window Filter Logic")
print("-"*70)
try:
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def _get_telemetry_analysis_windows(self' in content:
        method_section = content.split('def _get_telemetry_analysis_windows(self')[1].split('def ')[0]
        
        expected_types = [
            'speed_analysis', 'speed', 'brake', 'throttle', 
            'steering', 'gear', 'rpm', 'acceleration',
            'speed_diff', 'Speeddiff', 'distancediff'
        ]
        
        for ttype in expected_types:
            assert f"'{ttype}'" in method_section, \
                f"[FAIL] telemetry_types missing '{ttype}'"
        
        print(f"[OK] telemetry_types contains all {len(expected_types)} types")
        
        assert 'window.analysis_type in telemetry_types' in method_section, \
            "[FAIL] Filter logic missing"
        print("[OK] Filter logic implemented")
    
    print("[PASS] Test 4 Passed")
    test4_passed = True
except Exception as e:
    print(f"[FAIL] Test 4 Failed: {e}")
    import traceback
    traceback.print_exc()
    test4_passed = False

# Test 5: Confirmation Dialog Check
print("\n[TEST 5] Confirmation Dialog Check")
print("-"*70)
try:
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def on_race_parameters_changed(self' in content:
        method_section = content.split('def on_race_parameters_changed(self')[1].split('def ')[0]
        
        assert 'QMessageBox.question' in method_section, \
            "[FAIL] QMessageBox.question not found"
        print("[OK] QMessageBox.question used")
        
        assert 'QMessageBox.Yes | QMessageBox.No' in method_section, \
            "[FAIL] Yes/No options missing"
        print("[OK] Yes/No options present")
        
        assert 'self.update_all_lap_analysis()' in method_section, \
            "[FAIL] update_all_lap_analysis() call missing"
        print("[OK] update_all_lap_analysis() called")
    
    print("[PASS] Test 5 Passed")
    test5_passed = True
except Exception as e:
    print(f"[FAIL] Test 5 Failed: {e}")
    import traceback
    traceback.print_exc()
    test5_passed = False

# Test 6: Code Review Integration
print("\n[TEST 6] Code Review Integration")
print("-"*70)
try:
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checklist = {
        "on_race_parameters_changed method": "def on_race_parameters_changed(self):",
        "_get_telemetry_analysis_windows method": "def _get_telemetry_analysis_windows(self):",
        "Parameter change handler call": "self.on_race_parameters_changed()",
        "Race control logging": "[RACE_CONTROL]",
        "Telemetry window check": "telemetry_windows = self._get_telemetry_analysis_windows()",
        "User confirmation": "reply == QMessageBox.Yes",
    }
    
    passed = 0
    total = len(checklist)
    
    for check_name, check_pattern in checklist.items():
        if check_pattern in content:
            print(f"[OK] {check_name}")
            passed += 1
        else:
            print(f"[FAIL] {check_name}")
    
    print(f"\n[STATS] Code review: {passed}/{total} checks passed")
    
    if passed == total:
        print("[PASS] Test 6 Passed")
        test6_passed = True
    else:
        print(f"[WARN] Test 6 Partial: {passed}/{total}")
        test6_passed = (passed >= total - 1)  # Allow 1 failure
        
except Exception as e:
    print(f"[FAIL] Test 6 Failed: {e}")
    import traceback
    traceback.print_exc()
    test6_passed = False

# Summary Report
print("\n" + "="*70)
print("[SUMMARY] Test Results")
print("="*70)

results = [
    ("Import Verification", test1_passed),
    ("Method Signature", test2_passed),
    ("Signal Connection", test3_passed),
    ("Telemetry Filter", test4_passed),
    ("Confirmation Dialog", test5_passed),
    ("Code Integration", test6_passed),
]

passed_count = sum(1 for _, result in results if result)
total_count = len(results)

for test_name, result in results:
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {test_name}")

print(f"\n[STATS] Total: {passed_count}/{total_count} tests passed")

if passed_count == total_count:
    print("\n[SUCCESS] All tests passed! MDI race parameters handler implemented correctly!")
    sys.exit(0)
else:
    print(f"\n[WARN] Some tests failed. Please review the errors above.")
    sys.exit(1)
