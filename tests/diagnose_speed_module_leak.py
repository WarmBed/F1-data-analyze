#!/usr/bin/env python3
"""
速度模組記憶體洩漏視覺化診斷工具
Visual Diagnostic Tool for Speed Module Memory Leak

用於追蹤和視覺化速度模組的清理過程
"""

import gc
import sys
import threading
from PyQt5.QtWidgets import QApplication


def analyze_speed_module_references():
    """分析速度模組的引用關係"""
    print("=" * 80)
    print("速度模組記憶體洩漏診斷")
    print("=" * 80)
    print()
    
    # 導入模組
    try:
        from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import (
            SpeedAnalysisModule,
            SpeedDataManager
        )
        print("✅ 模組導入成功")
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        return
    
    app = QApplication(sys.argv)
    
    # 階段 1: 創建模組
    print("\n" + "=" * 80)
    print("【階段 1】創建速度模組")
    print("=" * 80)
    
    import objgraph
    
    # 記錄初始狀態
    initial_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader'),
    }
    
    print("初始物件數:")
    for obj_type, count in initial_counts.items():
        print(f"  {obj_type}: {count}")
    
    # 創建模組實例
    print("\n創建模組實例...")
    module = SpeedAnalysisModule()
    
    # 強制事件處理
    app.processEvents()
    gc.collect()
    
    # 記錄創建後狀態
    after_create_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader'),
    }
    
    print("\n創建後物件數:")
    for obj_type, count in after_create_counts.items():
        increase = count - initial_counts[obj_type]
        status = "✅" if increase > 0 else "⚠️"
        print(f"  {status} {obj_type}: {count} (+{increase})")
    
    # 階段 2: 分析引用關係
    print("\n" + "=" * 80)
    print("【階段 2】分析引用關係")
    print("=" * 80)
    
    # 檢查模組的屬性
    print("\nSpeedAnalysisModule 的屬性:")
    for attr in dir(module):
        if not attr.startswith('_') and hasattr(module, attr):
            value = getattr(module, attr)
            if not callable(value):
                print(f"  - {attr}: {type(value).__name__}")
    
    # 檢查 data_manager
    if hasattr(module, 'data_manager'):
        print("\nSpeedDataManager 的屬性:")
        for attr in dir(module.data_manager):
            if not attr.startswith('_') and hasattr(module.data_manager, attr):
                value = getattr(module.data_manager, attr)
                if not callable(value):
                    print(f"  - {attr}: {type(value).__name__}")
    
    # 階段 3: 測試 cleanup
    print("\n" + "=" * 80)
    print("【階段 3】執行 cleanup()")
    print("=" * 80)
    
    print("\n呼叫 module.cleanup()...")
    module.cleanup()
    
    print("呼叫 app.processEvents()...")
    app.processEvents()
    
    print("呼叫 gc.collect()...")
    collected = gc.collect()
    print(f"  垃圾回收: 清理了 {collected} 個物件")
    
    # 記錄 cleanup 後狀態
    after_cleanup_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader'),
    }
    
    print("\ncleanup() 後物件數:")
    for obj_type, count in after_cleanup_counts.items():
        before = after_create_counts[obj_type]
        change = count - before
        if change == 0:
            status = "✅"
            msg = "無變化"
        elif count == initial_counts[obj_type]:
            status = "✅"
            msg = "已清理"
        else:
            status = "❌"
            msg = "仍殘留"
        print(f"  {status} {obj_type}: {count} ({change:+d}) - {msg}")
    
    # 階段 4: 刪除引用並再次測試
    print("\n" + "=" * 80)
    print("【階段 4】刪除模組引用")
    print("=" * 80)
    
    print("\n執行 module.deleteLater()...")
    module.deleteLater()
    
    print("執行 del module...")
    del module
    
    print("再次 processEvents()...")
    app.processEvents()
    
    print("再次 gc.collect()...")
    collected = gc.collect()
    print(f"  垃圾回收: 清理了 {collected} 個物件")
    
    # 最終狀態
    final_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader'),
    }
    
    print("\n最終物件數:")
    for obj_type, count in final_counts.items():
        if count == initial_counts[obj_type]:
            status = "✅"
            msg = "完全清理"
        else:
            status = "❌"
            msg = f"洩漏 {count - initial_counts[obj_type]} 個"
        print(f"  {status} {obj_type}: {count} - {msg}")
    
    # 階段 5: 分析殘留物件的引用者
    print("\n" + "=" * 80)
    print("【階段 5】分析殘留物件的引用者")
    print("=" * 80)
    
    for obj_type, count in final_counts.items():
        if count > initial_counts[obj_type]:
            print(f"\n分析 {obj_type} 的引用者:")
            try:
                objects = objgraph.by_type(obj_type)
                if objects:
                    obj = objects[0]
                    print(f"  找到 {len(objects)} 個 {obj_type} 實例")
                    
                    # 顯示引用者
                    refs = gc.get_referrers(obj)
                    print(f"  引用者數量: {len(refs)}")
                    for i, ref in enumerate(refs[:5], 1):  # 只顯示前 5 個
                        ref_type = type(ref).__name__
                        print(f"    {i}. {ref_type}")
            except Exception as e:
                print(f"  ⚠️  分析失敗: {e}")
    
    # 總結
    print("\n" + "=" * 80)
    print("【診斷總結】")
    print("=" * 80)
    
    leak_found = False
    for obj_type, count in final_counts.items():
        if count > initial_counts[obj_type]:
            leak_found = True
            print(f"❌ {obj_type}: 洩漏 {count - initial_counts[obj_type]} 個物件")
    
    if not leak_found:
        print("✅ 無記憶體洩漏！所有物件已正確清理")
    else:
        print("\n⚠️  記憶體洩漏確認！")
        print("可能原因:")
        print("  1. deleteLater() 未被處理（需要事件循環）")
        print("  2. 信號連接創建循環引用")
        print("  3. 全局管理器持有引用")
        print("  4. Qt 父子關係未正確解除")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_speed_module_references()
