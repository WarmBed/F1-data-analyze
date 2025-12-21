# -*- coding: utf-8 -*-
"""
Complete Speed Analysis Leak Tracker

Execute in Python Debug Console:
exec(open('track_all_speed_leaks.py').read())
"""

import gc
import sys
import objgraph
from collections import defaultdict

print("\n" + "=" * 80)
print("Complete Speed Analysis Memory Leak Tracker")
print("=" * 80)

# Force GC first
gc.collect()

# Target types
speed_types = [
    'SpeedAnalysisModule',
    'SpeedDataManager',
    'SpeedAnalysisChartWidget',
    'SpeedChartWidget',
    'SpeedAnalysisDataLoader'
]

print("\n1. Object Count Check")
print("-" * 80)

leaked_objects = {}
for obj_type in speed_types:
    count = objgraph.count(obj_type)
    status = "LEAK" if count > 0 else "OK"
    print(f"  [{status}] {obj_type:30} : {count}")
    if count > 0:
        leaked_objects[obj_type] = count

if not leaked_objects:
    print("\n[SUCCESS] No Speed Analysis objects found - cleanup successful!")
    sys.exit(0)

print(f"\n[LEAK DETECTED] Found {len(leaked_objects)} types with unreleased objects")

# Check main window tracking sets
print("\n2. Main Window Tracking Check")
print("-" * 80)

try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    main_window = None
    
    for widget in app.topLevelWidgets():
        if widget.__class__.__name__ == 'StyleHMainWindow':
            main_window = widget
            break
    
    if main_window:
        print(f"  Main window found: {hex(id(main_window))}")
        
        # Check lap_analysis_windows set
        lap_windows_count = len(main_window.lap_analysis_windows)
        print(f"\n  lap_analysis_windows:")
        print(f"    Count: {lap_windows_count}")
        
        if lap_windows_count > 0:
            print(f"    [LEAK] Set is NOT empty!")
            for idx, win in enumerate(main_window.lap_analysis_windows):
                print(f"      [{idx}] {type(win).__name__} at {hex(id(win))}")
        else:
            print(f"    [OK] Set is empty")
        
        # Check active_analysis_tabs dict
        if hasattr(main_window, 'active_analysis_tabs'):
            tabs_count = len(main_window.active_analysis_tabs)
            print(f"\n  active_analysis_tabs:")
            print(f"    Count: {tabs_count}")
            
            if tabs_count > 0:
                print(f"    [LEAK] Dict is NOT empty!")
                for key, value in main_window.active_analysis_tabs.items():
                    print(f"      {key}: {type(value).__name__}")
            else:
                print(f"    [OK] Dict is empty")
    else:
        print("  [ERROR] Main window not found")
        
except Exception as e:
    print(f"  [ERROR] Failed to check main window: {e}")

# Check LinkageManager
print("\n3. LinkageManager Check")
print("-" * 80)

try:
    from modules.gui.lap_analysis.linkage.linkage_manager import LinkageManager
    linkage_mgr = LinkageManager()
    
    print(f"  LinkageManager instance: {hex(id(linkage_mgr))}")
    print(f"  registered_modules count: {len(linkage_mgr.registered_modules)}")
    
    if linkage_mgr.registered_modules:
        print(f"  [LEAK] registered_modules is NOT empty!")
        for idx, module in enumerate(linkage_mgr.registered_modules):
            print(f"    [{idx}] {type(module).__name__} at {hex(id(module))}")
    else:
        print(f"  [OK] registered_modules is empty")
        
except Exception as e:
    print(f"  [ERROR] Failed to check LinkageManager: {e}")

# Check AnalysisManager
print("\n4. AnalysisManager Check")
print("-" * 80)

try:
    from modules.gui.managers.analysis_manager import AnalysisManager
    analysis_mgr = AnalysisManager()
    
    print(f"  AnalysisManager instance: {hex(id(analysis_mgr))}")
    print(f"  registered_modules count: {len(analysis_mgr.registered_modules)}")
    print(f"  chart_widgets count: {len(analysis_mgr.chart_widgets)}")
    
    if analysis_mgr.registered_modules:
        print(f"  [LEAK] registered_modules is NOT empty!")
        for idx, module in enumerate(analysis_mgr.registered_modules):
            print(f"    [{idx}] {module}")
    else:
        print(f"  [OK] registered_modules is empty")
    
    if analysis_mgr.chart_widgets:
        print(f"  [LEAK] chart_widgets is NOT empty!")
        for idx, widget in enumerate(analysis_mgr.chart_widgets):
            print(f"    [{idx}] {type(widget).__name__} at {hex(id(widget))}")
    else:
        print(f"  [OK] chart_widgets is empty")
        
except Exception as e:
    print(f"  [ERROR] Failed to check AnalysisManager: {e}")

# Detailed referrer analysis for each leaked type
print("\n5. Detailed Referrer Analysis")
print("-" * 80)

for obj_type, count in leaked_objects.items():
    print(f"\n  Analyzing: {obj_type}")
    print(f"  " + "-" * 76)
    
    try:
        objects = objgraph.by_type(obj_type)
        
        for idx, obj in enumerate(objects):
            print(f"\n    Object #{idx + 1}:")
            print(f"      Memory: {hex(id(obj))}")
            print(f"      Refcount: {sys.getrefcount(obj)}")
            
            # Get referrers
            referrers = gc.get_referrers(obj)
            print(f"      Referrers: {len(referrers)} total")
            
            # Count referrer types
            referrer_types = defaultdict(int)
            for ref in referrers:
                ref_type = type(ref).__name__
                referrer_types[ref_type] += 1
            
            # Show referrer type stats
            print(f"      Referrer types:")
            for ref_type, ref_count in sorted(referrer_types.items(), key=lambda x: -x[1]):
                print(f"        {ref_type}: {ref_count}")
            
            # Show first 3 referrers details
            print(f"      First 3 referrers:")
            for ref_idx, ref in enumerate(referrers[:3]):
                ref_type = type(ref).__name__
                ref_id = hex(id(ref))
                print(f"        [{ref_idx + 1}] {ref_type} at {ref_id}")
                
                # Identify specific referrers
                if isinstance(ref, dict):
                    keys = list(ref.keys())[:3]
                    print(f"            Keys: {keys}")
                elif isinstance(ref, list):
                    print(f"            Length: {len(ref)}")
                elif isinstance(ref, set):
                    print(f"            Size: {len(ref)}")
                    # Check if it's lap_analysis_windows
                    if hasattr(main_window, 'lap_analysis_windows'):
                        if ref is main_window.lap_analysis_windows:
                            print(f"            [LEAK SOURCE] This is main_window.lap_analysis_windows!")
                
    except Exception as e:
        print(f"    [ERROR] Failed to analyze {obj_type}: {e}")

print("\n" + "=" * 80)
print("Analysis Complete")
print("=" * 80)

# Summary
print("\nSummary:")
print(f"  Leaked object types: {len(leaked_objects)}")
print(f"  Total leaked objects: {sum(leaked_objects.values())}")

# Recommendations
print("\nRecommendations:")
if any('set' in str(referrer_types) for referrer_types in []):
    print("  [!] Check lap_analysis_windows.discard() is being called")
if any('list' in str(referrer_types) for referrer_types in []):
    print("  [!] Check LinkageManager.unregister_module() is being called")
if any('dict' in str(referrer_types) for referrer_types in []):
    print("  [!] Check AnalysisManager cleanup")

print("\nNext Steps:")
print("  1. Review the referrer analysis above")
print("  2. Check if cleanup methods are being called")
print("  3. Verify manager unregistration logic")
print("  4. Use objgraph.show_backrefs() for visual reference graph")
