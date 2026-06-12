#!/usr/bin/env python3
"""快速測試 Workspace 映射"""
import sys
sys.path.insert(0, r"D:\OneDrive\Code\F1-data-analyze")

try:
    from core.workspace_serializer import WorkspaceSerializer
    
    print("=" * 60)
    print("Workspace 映射測試")
    print("=" * 60)
    
    mapping = WorkspaceSerializer.WINDOW_TYPE_MAPPING
    print(f"\n總映射數: {len(mapping)}")
    
    # 檢查新模組
    new_modules = [
        "PedalBehaviorAnalysisMDI",
        "HistoricalTrackMapMDI",
        "TrafficAnalysisMDI",
        "StartReactionAnalysisMDI",
        "LongRunAnalysis",
    ]
    
    print("\n新模組檢查:")
    for module in new_modules:
        status = "✅" if module in mapping else "❌"
        value = mapping.get(module, "缺失")
        print(f"{status} {module:40s} → {value}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
