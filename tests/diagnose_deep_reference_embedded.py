#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1T GUI 內嵌式深度引用鏈追蹤

此腳本必須在 F1T GUI 進程內執行（通過 Python Debug Console 或集成方式）

使用方式：
1. 在 F1T GUI 中打開 Python Debug Console
2. 執行: exec(open('diagnose_deep_reference_embedded.py').read())
3. 或直接在 GUI 中集成此模組

作者：F1T Team
日期：2025-10-15
"""

import gc
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

try:
    import objgraph
except ImportError:
    print("ERROR: objgraph 未安裝")
    print("請執行: pip install objgraph")
    sys.exit(1)


def analyze_speed_analysis_leak():
    """分析 Speed Analysis 模組的記憶體洩漏"""
    
    print("\n" + "=" * 80)
    print("F1T GUI 內嵌式深度引用鏈分析")
    print("=" * 80)
    
    # 目標類型
    target_types = [
        'SpeedAnalysisModule',
        'SpeedDataManager', 
        'SpeedChartWidget',
        'UniversalChartWidget',
        'UniversalDataLoader',
        'QMdiSubWindow',
        'LinkageManager',
        'AnalysisManager',
    ]
    
    print("\n步驟 1: 檢查當前物件計數")
    print("-" * 80)
    
    found_objects = {}
    
    for target_type in target_types:
        try:
            count = objgraph.count(target_type)
            if count > 0:
                print(f"{target_type}: {count} 個")
                found_objects[target_type] = count
            else:
                print(f"{target_type}: 0 個")
        except Exception as e:
            print(f"{target_type}: 無法計數 ({e})")
    
    if not found_objects:
        print("\n⚠️  未找到任何目標類型的物件")
        print("可能原因:")
        print("1. Speed Analysis 模組未開啟")
        print("2. 模組已完全清理")
        print("3. 類型名稱不正確")
        
        print("\n正在搜索類似的類型名稱...")
        all_types = objgraph.most_common_types(limit=50)
        
        print("\n最常見的類型（TOP 20）:")
        for type_name, count in all_types[:20]:
            print(f"  {type_name}: {count} 個")
        
        print("\n搜索包含 'Speed' 的類型:")
        for type_name, count in all_types:
            if 'Speed' in type_name or 'speed' in type_name:
                print(f"  {type_name}: {count} 個")
        
        print("\n搜索包含 'Analysis' 的類型:")
        for type_name, count in all_types:
            if 'Analysis' in type_name or 'analysis' in type_name:
                print(f"  {type_name}: {count} 個")
        
        return
    
    print(f"\n步驟 2: 深度引用鏈分析（找到 {len(found_objects)} 種類型）")
    print("-" * 80)
    
    for target_type, count in found_objects.items():
        print(f"\n正在分析: {target_type} ({count} 個物件)")
        print("=" * 80)
        
        try:
            objects = objgraph.by_type(target_type)
            
            for idx, obj in enumerate(objects[:3]):  # 只分析前 3 個
                print(f"\n物件 #{idx + 1}:")
                print(f"  記憶體位址: {hex(id(obj))}")
                print(f"  類型: {type(obj)}")
                print(f"  引用計數: {sys.getrefcount(obj)}")
                
                # 獲取引用來源
                referrers = gc.get_referrers(obj)
                print(f"\n  引用來源（總計 {len(referrers)} 個）:")
                
                # 統計引用來源類型
                referrer_types = defaultdict(int)
                for ref in referrers:
                    ref_type = type(ref).__name__
                    referrer_types[ref_type] += 1
                
                # 顯示引用來源統計
                print(f"\n  引用來源類型統計:")
                for ref_type, ref_count in sorted(referrer_types.items(), key=lambda x: -x[1]):
                    print(f"    {ref_type}: {ref_count} 個")
                
                # 顯示前 5 個引用來源的詳細資訊
                print(f"\n  前 5 個引用來源詳情:")
                for ref_idx, ref in enumerate(referrers[:5]):
                    ref_type = type(ref).__name__
                    ref_id = hex(id(ref))
                    print(f"    [{ref_idx + 1}] {ref_type} at {ref_id}")
                    
                    # 嘗試獲取更多上下文
                    if isinstance(ref, dict):
                        # 檢查是否是 __dict__
                        try:
                            keys = list(ref.keys())[:5]
                            print(f"        字典鍵: {keys}")
                            
                            # 檢查是否包含關鍵屬性
                            if 'chart_widget' in ref:
                                print(f"        ⚠️  包含 chart_widget 屬性")
                            if 'data_manager' in ref:
                                print(f"        ⚠️  包含 data_manager 屬性")
                            if 'linkage_manager' in ref:
                                print(f"        ⚠️  包含 linkage_manager 屬性")
                        except:
                            pass
                    
                    elif isinstance(ref, list):
                        print(f"        列表長度: {len(ref)}")
                        if len(ref) > 0:
                            print(f"        首元素類型: {type(ref[0]).__name__}")
                    
                    elif isinstance(ref, set):
                        print(f"        集合大小: {len(ref)}")
                    
                    elif hasattr(ref, '__name__'):
                        print(f"        名稱: {ref.__name__}")
                    
                    # 檢查是否是 QObject
                    try:
                        if hasattr(ref, 'objectName'):
                            obj_name = ref.objectName()
                            if obj_name:
                                print(f"        QObject 名稱: {obj_name}")
                    except:
                        pass
                
                print("\n" + "-" * 80)
        
        except Exception as e:
            print(f"分析 {target_type} 時發生錯誤: {e}")
            traceback.print_exc()
    
    print("\n步驟 3: 檢查全局管理器")
    print("-" * 80)
    
    try:
        # 檢查 LinkageManager
        from modules.gui.lap_analysis.linkage.linkage_manager import LinkageManager
        linkage_mgr = LinkageManager()
        
        print(f"\nLinkageManager 狀態:")
        print(f"  註冊模組數: {len(linkage_mgr.registered_modules)}")
        
        if linkage_mgr.registered_modules:
            print(f"  註冊的模組:")
            for idx, module in enumerate(linkage_mgr.registered_modules):
                print(f"    [{idx + 1}] {type(module).__name__} at {hex(id(module))}")
    except Exception as e:
        print(f"無法檢查 LinkageManager: {e}")
    
    try:
        # 檢查 AnalysisManager
        from modules.gui.managers.analysis_manager import AnalysisManager
        analysis_mgr = AnalysisManager()
        
        print(f"\nAnalysisManager 狀態:")
        print(f"  註冊模組數: {len(analysis_mgr.registered_modules)}")
        print(f"  圖表 Widget 數: {len(analysis_mgr.chart_widgets)}")
        
        if analysis_mgr.registered_modules:
            print(f"  註冊的模組:")
            for idx, module in enumerate(analysis_mgr.registered_modules):
                print(f"    [{idx + 1}] {type(module).__name__} at {hex(id(module))}")
    except Exception as e:
        print(f"無法檢查 AnalysisManager: {e}")
    
    print("\n步驟 4: 強制 GC 測試")
    print("-" * 80)
    
    initial_counts = {k: v for k, v in found_objects.items()}
    
    print("\n執行 5 次連續 GC...")
    for i in range(5):
        collected = gc.collect()
        print(f"  GC {i + 1}: 回收 {collected} 個物件")
    
    print("\n檢查 GC 後的物件計數:")
    for target_type, initial_count in initial_counts.items():
        final_count = objgraph.count(target_type)
        delta = final_count - initial_count
        status = "✅ 已清理" if delta < 0 else ("⚠️  持續洩漏" if delta == 0 and final_count > 0 else "🔴 增加")
        print(f"  {target_type}: {initial_count} -> {final_count} ({delta:+d}) {status}")
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)


if __name__ == "__main__":
    analyze_speed_analysis_leak()
