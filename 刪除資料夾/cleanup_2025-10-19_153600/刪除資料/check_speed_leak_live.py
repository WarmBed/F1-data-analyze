# -*- coding: utf-8 -*-
"""
實時檢查 Speed Analysis 模組物件狀態

在 F1T GUI 運行時，在 Python Debug Console 中執行此腳本
"""

import objgraph
import gc
import sys
from collections import defaultdict

print("\n" + "=" * 80)
print("Speed Analysis module object live check")
print("=" * 80)

# 先執行 GC
gc.collect()

# 檢查的類型
target_types = [
    'SpeedAnalysisModule',
    'SpeedDataManager',
    'SpeedAnalysisChartWidget',
    'SpeedChartWidget',
    'SpeedAnalysisDataLoader',
]

print("\nCurrent object count:")
print("-" * 80)

leaked_objects = {}

for obj_type in target_types:
    count = objgraph.count(obj_type)
    print(f"{obj_type:30} : {count}")
    
    if count > 0:
        leaked_objects[obj_type] = count

if not leaked_objects:
    print("\n[OK] No Speed Analysis module objects found - cleanup successful!")
else:
    print(f"\n[LEAK] Found {len(leaked_objects)} types of unreleased objects")
    print("\nTracing reference sources...")
    
    for obj_type, count in leaked_objects.items():
        print(f"\n{'=' * 80}")
        print(f"Tracing: {obj_type} ({count} objects)")
        print("=" * 80)
        
        try:
            objects = objgraph.by_type(obj_type)
            
            for idx, obj in enumerate(objects):
                print(f"\nObject #{idx + 1}:")
                print(f"  Memory address: {hex(id(obj))}")
                print(f"  Type: {type(obj)}")
                print(f"  Refcount: {sys.getrefcount(obj)}")
                
                # Get referrers
                referrers = gc.get_referrers(obj)
                print(f"  Referrer count: {len(referrers)}")
                
                # Count referrer types
                referrer_types = defaultdict(int)
                for ref in referrers:
                    ref_type = type(ref).__name__
                    referrer_types[ref_type] += 1
                
                print(f"\n  Referrer types:")
                for ref_type, ref_count in sorted(referrer_types.items(), key=lambda x: -x[1]):
                    print(f"    {ref_type}: {ref_count}")
                
                # Show details of first 3 referrers
                print(f"\n  First 3 referrers details:")
                for ref_idx, ref in enumerate(referrers[:3]):
                    ref_type = type(ref).__name__
                    ref_id = hex(id(ref))
                    print(f"    [{ref_idx + 1}] {ref_type} at {ref_id}")
                    
                    # Try to identify referrer
                    if isinstance(ref, dict):
                        keys = list(ref.keys())[:5]
                        print(f"        Dict keys: {keys}")
                        
                        # Check if it's an object's __dict__
                        if 'chart_widget' in ref or 'data_manager' in ref:
                            print(f"        [!] Likely module attribute dict")
                    
                    elif isinstance(ref, list):
                        print(f"        List length: {len(ref)}")
                    
                    elif isinstance(ref, set):
                        print(f"        Set size: {len(ref)}")
                        # Might be lap_analysis_windows
                        if hasattr(ref, '__iter__'):
                            print(f"        [!] Likely tracking set (lap_analysis_windows?)")
                    
                    elif hasattr(ref, '__name__'):
                        print(f"        Name: {ref.__name__}")
        
        except Exception as e:
            print(f"[ERROR] Failed to trace {obj_type}: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "=" * 80)
print("Check complete")
print("=" * 80)
