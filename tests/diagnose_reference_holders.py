"""
診斷記憶體洩漏：追蹤引用持有者
=====================================

目的：找出是誰持有 Speed 模組組件的強引用，導致 GC 無法回收

已知問題：
- cleanup() 執行成功 ✅
- gc.collect() 回收 0 個物件 ❌
- objgraph 顯示物件仍存在 ❌
- 結論：某處持有強引用

檢查重點：
1. MDI parent-child 關係（QMdiArea → QMdiSubWindow → SpeedAnalysisModule）
2. PopoutSubWindow 持有的引用
3. analysis_manager 全域字典
4. linkage_manager 全域字典
5. 信號連接殘留
"""

import gc
import sys
import objgraph
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_speed_module_references():
    """分析 Speed 模組的引用情況"""
    
    print("\n" + "="*70)
    print("速度模組引用分析")
    print("="*70)
    
    # 1. 檢查當前記憶體中的 Speed 相關物件
    print("\n【步驟 1】檢查記憶體中的 Speed 組件：")
    speed_types = [
        'SpeedAnalysisModule',
        'SpeedDataManager', 
        'SpeedChartWidget',
        'SpeedChart',
        'TelemetryDataLoader'
    ]
    
    found_objects = {}
    for obj_type in speed_types:
        objects = objgraph.by_type(obj_type)
        found_objects[obj_type] = objects
        print(f"  - {obj_type}: {len(objects)} 個實例")
        
        if len(objects) > 0:
            print(f"    ℹ️  應該為 0（已關閉），實際有 {len(objects)} 個 → ⚠️ 洩漏！")
    
    # 2. 對每個洩漏的物件分析引用來源
    print("\n【步驟 2】分析引用持有者：")
    for obj_type, objects in found_objects.items():
        if len(objects) == 0:
            continue
            
        print(f"\n  🔍 分析 {obj_type}:")
        for i, obj in enumerate(objects[:3]):  # 只分析前 3 個
            print(f"\n    實例 #{i+1}:")
            print(f"      引用數: {sys.getrefcount(obj)}")
            
            # 獲取引用來源
            referrers = gc.get_referrers(obj)
            print(f"      引用來源數量: {len(referrers)}")
            
            # 分類引用來源
            ref_types = {}
            for ref in referrers:
                ref_type = type(ref).__name__
                ref_types[ref_type] = ref_types.get(ref_type, 0) + 1
            
            print(f"      引用來源分類:")
            for ref_type, count in sorted(ref_types.items(), key=lambda x: x[1], reverse=True):
                print(f"        - {ref_type}: {count} 個")
                
                # 特別關注這些類型
                if ref_type in ['dict', 'QMdiSubWindow', 'PopoutSubWindow', 'QWidget']:
                    matching_refs = [r for r in referrers if type(r).__name__ == ref_type]
                    for ref in matching_refs[:2]:  # 只看前 2 個
                        if ref_type == 'dict':
                            # 檢查是否是全域管理器的字典
                            if hasattr(ref, '__name__'):
                                print(f"          ⚠️  可能是全域字典: {ref.__name__}")
                            # 檢查字典內容
                            keys = list(ref.keys())[:3]
                            print(f"          字典前 3 個 key: {keys}")
                        else:
                            print(f"          物件類型: {type(ref)}")
    
    # 3. 生成引用鏈圖（保存為圖片）
    print("\n【步驟 3】生成引用鏈可視化：")
    for obj_type, objects in found_objects.items():
        if len(objects) > 0:
            output_file = f"reference_chain_{obj_type}.png"
            print(f"  正在生成 {obj_type} 的引用鏈圖 → {output_file}")
            try:
                objgraph.show_refs(
                    objects[0], 
                    max_depth=3,
                    too_many=10,
                    filename=output_file,
                    refcounts=True
                )
                print(f"    ✅ 已生成: {output_file}")
            except Exception as e:
                print(f"    ❌ 生成失敗: {e}")
    
    # 4. 檢查全域管理器
    print("\n【步驟 4】檢查全域管理器：")
    try:
        from modules.gui.managers.analysis_manager import analysis_manager
        registered = analysis_manager.registered_modules
        print(f"  analysis_manager 已註冊模組數: {len(registered)}")
        for module_id in list(registered.keys())[:5]:
            print(f"    - {module_id}")
        
        if len(registered) > 0:
            print(f"    ⚠️  應該為 0（已清理），實際有 {len(registered)} 個！")
    except Exception as e:
        print(f"  ❌ 無法檢查 analysis_manager: {e}")
    
    try:
        from modules.gui.managers.linkage_manager import linkage_manager
        linkages = linkage_manager.linkages
        print(f"  linkage_manager 連動數: {len(linkages)}")
        
        if len(linkages) > 0:
            print(f"    ⚠️  應該為 0（已清理），實際有 {len(linkages)} 個！")
            for link_id in list(linkages.keys())[:5]:
                print(f"    - {link_id}")
    except Exception as e:
        print(f"  ❌ 無法檢查 linkage_manager: {e}")
    
    # 5. 建議修復方案
    print("\n" + "="*70)
    print("【診斷結論與修復建議】")
    print("="*70)
    
    total_leaks = sum(len(objs) for objs in found_objects.values())
    if total_leaks == 0:
        print("\n✅ 沒有記憶體洩漏！所有物件已正確清理。")
    else:
        print(f"\n❌ 發現 {total_leaks} 個洩漏物件")
        print("\n根據上述引用分析，可能的修復方向：")
        print("  1. 如果主要是 'dict' 引用 → 檢查 analysis_manager/linkage_manager 解除註冊")
        print("  2. 如果主要是 'QMdiSubWindow' → 檢查 MDI parent-child 清理")
        print("  3. 如果主要是 'PopoutSubWindow' → 檢查彈出視窗引用釋放")
        print("  4. 如果主要是 'function' → 檢查 signal/slot 連接是否完全斷開")
        print("  5. 如果主要是 'frame' → 檢查是否有循環引用")
        
        print(f"\n請查看生成的 reference_chain_*.png 圖片以了解詳細引用鏈。")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    print("⚠️  注意：此腳本需要在關閉 Speed 模組後立即執行！")
    print("請按以下步驟操作：")
    print("  1. 啟動 F1T GUI")
    print("  2. 打開速度分析模組")
    print("  3. 關閉速度分析模組")
    print("  4. 不要退出 GUI，立即執行此腳本")
    print()
    
    input("準備好後按 Enter 繼續...")
    
    analyze_speed_module_references()
