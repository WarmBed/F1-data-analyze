#!/usr/bin/env python3
"""
驗證新增模組的 Workspace 序列化映射

檢查 WINDOW_TYPE_MAPPING 是否包含所有新增的核心模組
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.workspace_serializer import WorkspaceSerializer

# 新增模組的類名列表
NEW_MODULES = [
    "PedalBehaviorAnalysisMDI",       # 油門/煞車行為分析
    "HistoricalTrackMapMDI",          # 歷年賽道旗幟統計
    "TrafficAnalysisMDI",             # 超車難度分析
    "StartReactionAnalysisMDI",       # 起跑反應分析
    "LongRunAnalysis",                # 長跑與衰退分析
]

def main():
    print("=" * 80)
    print("驗證新增模組的 Workspace 序列化映射")
    print("=" * 80)
    
    mapping = WorkspaceSerializer.WINDOW_TYPE_MAPPING
    
    print(f"\n總共需檢查的新模組: {len(NEW_MODULES)} 個\n")
    
    found = 0
    missing = 0
    
    for module_class in NEW_MODULES:
        if module_class in mapping:
            window_type = mapping[module_class]
            print(f"✅ {module_class:40s} → {window_type}")
            found += 1
        else:
            print(f"❌ {module_class:40s} → 缺失!")
            missing += 1
    
    print("\n" + "=" * 80)
    print("驗證結果")
    print("=" * 80)
    print(f"✅ 已映射: {found}/{len(NEW_MODULES)}")
    print(f"❌ 缺失: {missing}/{len(NEW_MODULES)}")
    
    if missing == 0:
        print("\n🎉 所有新增模組都已添加 Workspace 序列化映射!")
        return True
    else:
        print("\n⚠️ 有模組缺少 Workspace 序列化映射，需要修復!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
