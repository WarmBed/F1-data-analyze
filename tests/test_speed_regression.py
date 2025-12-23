#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速度模組回歸測試
測試簡化後的清理流程是否正常工作
"""

import objgraph
import gc

def test_speed_module_regression():
    """測試速度模組回歸後的清理"""
    print("=" * 80)
    print("速度模組回歸測試 - 簡化清理流程")
    print("=" * 80)
    
    # 階段 1: 獲取初始狀態
    print("\n[階段 1] 檢查初始對象數量...")
    before_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader')
    }
    
    print("初始對象數量:")
    for name, count in before_counts.items():
        print(f"  {name}: {count}")
    
    # 階段 2: 指示用戶操作
    print("\n[階段 2] 請執行以下操作:")
    print("  1. 開啟速度分析模組視窗")
    print("  2. 載入任意數據（例如：2025 Japan R, VER vs LEC, 1 vs 1）")
    print("  3. 等待數據載入完成")
    input("\n按 Enter 繼續到階段 3...")
    
    # 階段 3: 記錄開啟後狀態
    print("\n[階段 3] 檢查開啟後的對象數量...")
    after_open_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader')
    }
    
    print("開啟後對象數量:")
    for name, count in after_open_counts.items():
        delta = count - before_counts[name]
        status = "新增" if delta > 0 else "相同"
        print(f"  {name}: {count} ({status} {abs(delta)})")
    
    # 階段 4: 指示關閉視窗
    print("\n[階段 4] 請執行以下操作:")
    print("  1. 關閉速度分析模組視窗")
    print("  2. 確認視窗已完全關閉")
    input("\n按 Enter 繼續到階段 5...")
    
    # 階段 5: 手動 GC
    print("\n[階段 5] 執行手動垃圾回收...")
    collected = gc.collect()
    print(f"GC 回收了 {collected} 個對象")
    
    # 階段 6: 檢查清理後狀態
    print("\n[階段 6] 檢查清理後的對象數量...")
    after_close_counts = {
        'SpeedAnalysisModule': objgraph.count('SpeedAnalysisModule'),
        'SpeedDataManager': objgraph.count('SpeedDataManager'),
        'SpeedAnalysisChartWidget': objgraph.count('SpeedAnalysisChartWidget'),
        'SpeedChartWidget': objgraph.count('SpeedChartWidget'),
        'SpeedAnalysisDataLoader': objgraph.count('SpeedAnalysisDataLoader')
    }
    
    print("清理後對象數量:")
    all_cleaned = True
    for name, count in after_close_counts.items():
        expected = before_counts[name]
        status = "✅ 已清理" if count == expected else "❌ 洩漏"
        if count != expected:
            all_cleaned = False
        print(f"  {name}: {count} (期望 {expected}) {status}")
    
    # 階段 7: 總結
    print("\n" + "=" * 80)
    if all_cleaned:
        print("✅ 測試通過！所有對象已正確清理")
        print("   簡化的清理流程運作正常")
    else:
        print("❌ 測試失敗！仍有對象洩漏")
        print("   需要進一步診斷洩漏來源")
        
        # 生成引用圖
        print("\n[階段 8] 生成洩漏對象的引用圖...")
        for name, count in after_close_counts.items():
            if count > before_counts[name]:
                print(f"\n生成 {name} 的引用圖...")
                try:
                    obj = objgraph.by_type(name)[0]
                    filename = f'speed_regression_leak_{name}.png'
                    objgraph.show_backrefs(
                        obj, 
                        max_depth=3, 
                        filename=filename,
                        too_many=15
                    )
                    print(f"  已生成: {filename}")
                except Exception as e:
                    print(f"  生成失敗: {e}")
    
    print("=" * 80)

if __name__ == "__main__":
    # 檢查 objgraph 是否可用
    try:
        import objgraph
        print("objgraph 已載入")
    except ImportError:
        print("錯誤: 需要安裝 objgraph")
        print("請執行: pip install objgraph")
        exit(1)
    
    test_speed_module_regression()
