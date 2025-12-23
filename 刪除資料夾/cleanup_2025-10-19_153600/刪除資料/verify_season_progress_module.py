#!/usr/bin/env python3
"""
Season Progress Module - Final Verification Script

Tests all components and integration points before user testing

Author: F1T Team
Date: 2025-10-13
"""

import sys
import traceback
from pathlib import Path

# Add workspace to path
workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

print("=" * 80)
print("SEASON PROGRESS MODULE - FINAL VERIFICATION")
print("=" * 80)
print()

test_results = []


def test_import_data_loader():
    """Test 1: Import DataLoader"""
    try:
        from modules.gui.season_progress import SeasonProgressDataLoader
        test_results.append(("Import DataLoader", True, ""))
        return SeasonProgressDataLoader
    except Exception as e:
        test_results.append(("Import DataLoader", False, str(e)))
        traceback.print_exc()
        return None


def test_import_widget():
    """Test 2: Import Widget"""
    try:
        from modules.gui.season_progress import SeasonProgressWidget
        test_results.append(("Import Widget", True, ""))
        return SeasonProgressWidget
    except Exception as e:
        test_results.append(("Import Widget", False, str(e)))
        traceback.print_exc()
        return None


def test_import_mdi():
    """Test 3: Import MDI"""
    try:
        from modules.gui.season_progress import SeasonProgressMDI
        test_results.append(("Import MDI", True, ""))
        return SeasonProgressMDI
    except Exception as e:
        test_results.append(("Import MDI", False, str(e)))
        traceback.print_exc()
        return None


def test_dataloader_methods(DataLoader):
    """Test 4: Check DataLoader methods"""
    if not DataLoader:
        test_results.append(("DataLoader methods", False, "Class not imported"))
        return
    
    try:
        required_methods = [
            '_validate_data_format',
            '_load_calendar_data',
            '_build_filename_patterns',
            '_transform_data_for_display'
        ]
        
        missing = [m for m in required_methods if not hasattr(DataLoader, m)]
        if missing:
            raise ValueError(f"Missing methods: {missing}")
        
        test_results.append(("DataLoader methods", True, ""))
    except Exception as e:
        test_results.append(("DataLoader methods", False, str(e)))
        traceback.print_exc()


def test_widget_methods(Widget):
    """Test 5: Check Widget methods"""
    if not Widget:
        test_results.append(("Widget methods", False, "Class not imported"))
        return
    
    try:
        required_methods = [
            'populate_data',
        ]
        
        # Accept either _setup_ui or _init_ui
        has_ui_setup = hasattr(Widget, '_setup_ui') or hasattr(Widget, '_init_ui')
        if not has_ui_setup:
            raise ValueError("Missing UI setup method (_setup_ui or _init_ui)")
        
        missing = [m for m in required_methods if not hasattr(Widget, m)]
        if missing:
            raise ValueError(f"Missing methods: {missing}")
        
        test_results.append(("Widget methods", True, ""))
    except Exception as e:
        test_results.append(("Widget methods", False, str(e)))
        traceback.print_exc()


def test_mdi_methods(MDI):
    """Test 6: Check MDI methods"""
    if not MDI:
        test_results.append(("MDI methods", False, "Class not imported"))
        return
    
    try:
        required_methods = [
            '_setup_ui',
            '_connect_signals',
            '_trigger_initial_load',
            '_start_load_analysis',
            '_on_api_progress',
            '_on_api_success',
            '_on_api_failure',
            '_on_data_loaded',
            '_show_error'
        ]
        
        missing = [m for m in required_methods if not hasattr(MDI, m)]
        if missing:
            raise ValueError(f"Missing methods: {missing}")
        
        test_results.append(("MDI methods", True, ""))
    except Exception as e:
        test_results.append(("MDI methods", False, str(e)))
        traceback.print_exc()


def test_translation_keys():
    """Test 7: Check translation keys"""
    try:
        from core.gui_i18n import tr
        
        required_keys = [
            'season_progress_title',
            'menu_analysis',
            'menu_season_progress'
        ]
        
        missing_keys = []
        for key in required_keys:
            result = tr(key, f"MISSING_{key}")
            if result.startswith("MISSING_"):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing translation keys: {missing_keys}")
        
        test_results.append(("Translation keys", True, ""))
    except Exception as e:
        test_results.append(("Translation keys", False, str(e)))
        traceback.print_exc()


def test_gui_integration():
    """Test 8: Check GUI menu integration"""
    try:
        # Read f1t_gui_main.py to verify integration
        gui_main_path = workspace / "f1t_gui_main.py"
        if not gui_main_path.exists():
            raise FileNotFoundError("f1t_gui_main.py not found")
        
        content = gui_main_path.read_text(encoding='utf-8')
        
        # Check for Analysis menu
        if "analysis_menu" not in content:
            raise ValueError("Analysis menu not found")
        
        # Check for open_season_progress method
        if "def open_season_progress" not in content:
            raise ValueError("open_season_progress() method not found")
        
        # Check for import statement
        if "from modules.gui.season_progress import SeasonProgressMDI" not in content:
            raise ValueError("SeasonProgressMDI import not found in GUI")
        
        test_results.append(("GUI integration", True, ""))
    except Exception as e:
        test_results.append(("GUI integration", False, str(e)))
        traceback.print_exc()


def test_api_only_compliance(MDI):
    """Test 9: Verify API-ONLY compliance"""
    if not MDI:
        test_results.append(("API-ONLY compliance", False, "Class not imported"))
        return
    
    try:
        # Read MDI source to verify no CLI subprocess calls
        mdi_path = workspace / "modules/gui/season_progress/season_progress_mdi.py"
        content = mdi_path.read_text(encoding='utf-8')
        
        # Check for prohibited patterns
        prohibited = [
            'CliAnalysisWorker',
            'subprocess.run',
            'subprocess.call',
            'os.system'
        ]
        
        found_prohibited = [p for p in prohibited if p in content]
        if found_prohibited:
            raise ValueError(f"Found prohibited CLI calls: {found_prohibited}")
        
        # Verify API worker is used
        if 'SeasonProgressApiWorker' not in content:
            raise ValueError("API Worker not found in MDI")
        
        test_results.append(("API-ONLY compliance", True, ""))
    except Exception as e:
        test_results.append(("API-ONLY compliance", False, str(e)))
        traceback.print_exc()


# Run all tests
print("Running verification tests...")
print()

DataLoader = test_import_data_loader()
Widget = test_import_widget()
MDI = test_import_mdi()

test_dataloader_methods(DataLoader)
test_widget_methods(Widget)
test_mdi_methods(MDI)
test_translation_keys()
test_gui_integration()
test_api_only_compliance(MDI)

# Print results
print()
print("=" * 80)
print("TEST RESULTS")
print("=" * 80)
print()

passed = 0
failed = 0

for test_name, success, error in test_results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status:<10} {test_name}")
    if error:
        print(f"           Error: {error}")
    
    if success:
        passed += 1
    else:
        failed += 1

print()
print("=" * 80)
print(f"SUMMARY: {passed} passed, {failed} failed")
print("=" * 80)

if failed == 0:
    print()
    print("✅ ALL TESTS PASSED - Module ready for user testing!")
    print()
    print("Next steps:")
    print("1. Launch F1T GUI: python f1t_gui_main.py")
    print("2. Click Analysis → Season Progress")
    print("3. Verify API call and data display")
    sys.exit(0)
else:
    print()
    print("❌ SOME TESTS FAILED - Please review errors above")
    sys.exit(1)
