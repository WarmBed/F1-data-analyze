#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1T GUI 深度引用鏈追蹤腳本

功能：
1. 自動化 objgraph 深度引用分析
2. 識別強引用持有者
3. 生成引用鏈圖表
4. 持續監控 GC 效果

使用方式：
1. 啟動 F1T GUI
2. 執行此腳本
3. 按照提示操作（開啟模組、關閉視窗、強制 GC）
4. 腳本自動生成分析報告

作者：F1T Team
日期：2025-10-15
"""

import gc
import sys
import os
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Set
import psutil

# 嘗試導入 objgraph
try:
    import objgraph
    OBJGRAPH_AVAILABLE = True
except ImportError:
    print("ERROR: objgraph 未安裝")
    print("請執行: pip install objgraph")
    sys.exit(1)

# 嘗試導入 graphviz（用於生成引用圖）
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    print("WARNING: graphviz 未安裝，無法生成視覺化圖表")
    print("可選安裝: pip install graphviz")
    GRAPHVIZ_AVAILABLE = False


class DeepReferenceChainAnalyzer:
    """深度引用鏈分析器"""
    
    def __init__(self, output_dir: str = "memory_analysis"):
        """
        初始化分析器
        
        Args:
            output_dir: 輸出目錄路徑
        """
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_path = os.path.join(output_dir, f"deep_reference_report_{self.timestamp}.txt")
        self.graph_dir = os.path.join(output_dir, "graphs")
        
        # 創建輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.graph_dir, exist_ok=True)
        
        # 追蹤目標類型（F1T GUI 分析模組相關）
        self.target_types = [
            'SpeedAnalysisModule',
            'SpeedDataManager',
            'SpeedChartWidget',
            'UniversalChartWidget',
            'UniversalDataLoader',
            'QMdiSubWindow',
            'QThread',
            'QTimer',
            'LinkageManager',
            'AnalysisManager',
        ]
        
        # 通用類型（更廣泛的追蹤）
        self.generic_types = [
            'QWidget',
            'QMainWindow',
            'QDialog',
            'QPushButton',
            'QLabel',
            'dict',
            'list',
            'set',
            'function',
            'method',
        ]
        
        # 記憶體快照
        self.snapshots = []
        
        print(f"深度引用鏈分析器已初始化")
        print(f"輸出目錄: {self.output_dir}")
        print(f"報告檔案: {self.report_path}")
        print(f"圖表目錄: {self.graph_dir}")
    
    def take_snapshot(self, label: str = "") -> Dict[str, int]:
        """
        記憶體快照
        
        Args:
            label: 快照標籤
            
        Returns:
            物件計數字典
        """
        print(f"\n正在建立快照: {label}")
        
        # 強制 GC
        collected = gc.collect()
        print(f"GC 回收了 {collected} 個物件")
        
        # 獲取物件計數（目標類型）
        type_counts = {}
        print("\n目標類型計數:")
        for target_type in self.target_types:
            count = objgraph.count(target_type)
            type_counts[target_type] = count
            if count > 0:
                print(f"  {target_type}: {count} 個")
        
        # 檢查通用類型（用於診斷）
        print("\n通用類型計數（前 5 名）:")
        for generic_type in self.generic_types[:5]:
            count = objgraph.count(generic_type)
            if count > 0:
                print(f"  {generic_type}: {count} 個")
        
        # 顯示最常見的類型（TOP 10）
        print("\n最常見的類型（TOP 10）:")
        most_common = objgraph.most_common_types(limit=10)
        for type_name, count in most_common:
            print(f"  {type_name}: {count} 個")
        
        # 記憶體使用量
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        snapshot = {
            'label': label,
            'timestamp': datetime.now(),
            'type_counts': type_counts,
            'memory_mb': memory_mb,
            'gc_collected': collected,
        }
        
        self.snapshots.append(snapshot)
        print(f"記憶體使用量: {memory_mb:.2f} MB")
        
        return type_counts
    
    def analyze_growth(self) -> Dict[str, List[int]]:
        """
        分析物件增長趨勢
        
        Returns:
            類型增長字典
        """
        if len(self.snapshots) < 2:
            print("需要至少 2 個快照才能分析增長")
            return {}
        
        print("\n物件增長分析")
        print("=" * 80)
        
        growth_data = {}
        
        for target_type in self.target_types:
            counts = [snap['type_counts'].get(target_type, 0) for snap in self.snapshots]
            
            if any(c > 0 for c in counts):
                growth_data[target_type] = counts
                
                initial = counts[0]
                final = counts[-1]
                delta = final - initial
                
                print(f"\n{target_type}:")
                print(f"  初始: {initial}")
                print(f"  最終: {final}")
                print(f"  變化: {delta:+d}")
                
                if len(counts) > 2:
                    print(f"  完整序列: {counts}")
        
        return growth_data
    
    def trace_references(self, obj_type: str, max_depth: int = 5) -> None:
        """
        追蹤物件引用鏈
        
        Args:
            obj_type: 物件類型名稱
            max_depth: 最大追蹤深度
        """
        print(f"\n追蹤 {obj_type} 的引用鏈（深度: {max_depth}）")
        print("=" * 80)
        
        # 獲取該類型的所有物件
        objects = objgraph.by_type(obj_type)
        
        if not objects:
            print(f"未找到 {obj_type} 類型的物件")
            return
        
        print(f"找到 {len(objects)} 個 {obj_type} 物件")
        
        # 分析前幾個物件的引用
        for idx, obj in enumerate(objects[:3]):  # 只分析前 3 個
            print(f"\n物件 #{idx + 1}:")
            print(f"  記憶體位址: {hex(id(obj))}")
            print(f"  引用計數: {sys.getrefcount(obj)}")
            
            # 顯示引用來源
            print(f"\n  引用來源（Referrers）:")
            referrers = gc.get_referrers(obj)
            print(f"  總計 {len(referrers)} 個引用來源")
            
            for ref_idx, ref in enumerate(referrers[:5]):  # 只顯示前 5 個
                ref_type = type(ref).__name__
                ref_id = hex(id(ref))
                print(f"    [{ref_idx + 1}] {ref_type} at {ref_id}")
                
                # 如果是容器，顯示內容摘要
                if isinstance(ref, dict):
                    keys = list(ref.keys())[:3]
                    print(f"        字典鍵: {keys}...")
                elif isinstance(ref, list):
                    print(f"        列表長度: {len(ref)}")
                elif isinstance(ref, set):
                    print(f"        集合大小: {len(ref)}")
    
    def generate_reference_graph(self, obj_type: str, max_depth: int = 3) -> None:
        """
        生成引用關係圖
        
        Args:
            obj_type: 物件類型名稱
            max_depth: 圖的最大深度
        """
        if not GRAPHVIZ_AVAILABLE:
            print("graphviz 未安裝，跳過圖表生成")
            return
        
        print(f"\n生成 {obj_type} 的引用關係圖...")
        
        objects = objgraph.by_type(obj_type)
        if not objects:
            print(f"未找到 {obj_type} 類型的物件")
            return
        
        # 為每個物件生成引用圖
        for idx, obj in enumerate(objects[:2]):  # 只生成前 2 個
            graph_path = os.path.join(
                self.graph_dir, 
                f"{obj_type}_{idx + 1}_backrefs_{self.timestamp}.png"
            )
            
            print(f"  物件 #{idx + 1} -> {graph_path}")
            
            try:
                objgraph.show_backrefs(
                    [obj],
                    max_depth=max_depth,
                    filename=graph_path,
                    refcounts=True,
                    highlight=lambda x: type(x).__name__ in self.target_types
                )
                print(f"    成功生成引用圖")
            except Exception as e:
                print(f"    生成引用圖失敗: {e}")
    
    def identify_leak_suspects(self) -> List[str]:
        """
        識別可能的洩漏嫌疑類型
        
        Returns:
            嫌疑類型列表
        """
        if len(self.snapshots) < 2:
            return []
        
        print("\n識別洩漏嫌疑類型")
        print("=" * 80)
        
        suspects = []
        
        for target_type in self.target_types:
            counts = [snap['type_counts'].get(target_type, 0) for snap in self.snapshots]
            
            # 檢查是否持續增長或無法清零
            initial = counts[0]
            final = counts[-1]
            
            # 條件 1: 關閉後仍有殘留
            if initial == 0 and final > 0:
                suspects.append(target_type)
                print(f"嫌疑: {target_type} (創建後未清理，殘留 {final} 個)")
            
            # 條件 2: 多次 GC 後計數不減少
            elif final > 0 and len(counts) >= 3:
                last_three = counts[-3:]
                if all(c == final for c in last_three):
                    suspects.append(target_type)
                    print(f"嫌疑: {target_type} (連續 3 次 GC 後計數不變，固定 {final} 個)")
        
        return suspects
    
    def automated_analysis_workflow(self) -> None:
        """
        自動化分析工作流程
        """
        print("\n" + "=" * 80)
        print("F1T GUI 深度引用鏈自動化分析")
        print("=" * 80)
        
        print("\n工作流程:")
        print("1. 基線快照（初始狀態）")
        print("2. 開啟模組快照（Speed Analysis 開啟後）")
        print("3. 關閉模組快照（視窗關閉後）")
        print("4. 連續 GC 快照（10 次強制 GC）")
        print("5. 引用鏈追蹤")
        print("6. 生成報告")
        
        input("\n請確保 F1T GUI 已啟動，按 Enter 繼續...")
        
        # 步驟 1: 基線快照
        self.take_snapshot("1_Baseline_Initial")
        
        input("\n請在 GUI 中開啟 Speed Analysis 模組，然後按 Enter...")
        time.sleep(2)
        
        # 步驟 2: 開啟模組快照
        self.take_snapshot("2_Module_Opened")
        
        input("\n請關閉 Speed Analysis 視窗（使用 Close All Windows），然後按 Enter...")
        time.sleep(2)
        
        # 步驟 3: 關閉模組快照
        self.take_snapshot("3_Module_Closed")
        
        print("\n開始連續 GC 測試（10 次）...")
        for i in range(10):
            print(f"\nGC 循環 {i + 1}/10")
            time.sleep(1)
            self.take_snapshot(f"4_GC_Cycle_{i + 1:02d}")
        
        # 步驟 4: 分析增長趨勢
        growth_data = self.analyze_growth()
        
        # 步驟 5: 識別嫌疑類型
        suspects = self.identify_leak_suspects()
        
        # 步驟 6: 深度追蹤嫌疑類型
        if suspects:
            print(f"\n發現 {len(suspects)} 個嫌疑類型，開始深度追蹤...")
            
            for suspect in suspects:
                self.trace_references(suspect, max_depth=5)
                self.generate_reference_graph(suspect, max_depth=3)
        else:
            print("\n未發現明顯的洩漏嫌疑類型")
        
        # 步驟 7: 生成最終報告
        self.generate_report(growth_data, suspects)
        
        print(f"\n分析完成！報告已保存至: {self.report_path}")
    
    def generate_report(self, growth_data: Dict[str, List[int]], suspects: List[str]) -> None:
        """
        生成分析報告
        
        Args:
            growth_data: 增長數據
            suspects: 嫌疑類型列表
        """
        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("F1T GUI 深度引用鏈分析報告\n")
            f.write("=" * 80 + "\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python 版本: {sys.version}\n")
            f.write(f"objgraph 版本: {objgraph.__version__ if hasattr(objgraph, '__version__') else 'Unknown'}\n")
            f.write("\n")
            
            # 快照摘要
            f.write("快照摘要\n")
            f.write("-" * 80 + "\n")
            for idx, snap in enumerate(self.snapshots):
                f.write(f"快照 {idx + 1}: {snap['label']}\n")
                f.write(f"  時間: {snap['timestamp'].strftime('%H:%M:%S')}\n")
                f.write(f"  記憶體: {snap['memory_mb']:.2f} MB\n")
                f.write(f"  GC 回收: {snap['gc_collected']} 個物件\n")
                
                # 顯示非零物件計數
                non_zero = {k: v for k, v in snap['type_counts'].items() if v > 0}
                if non_zero:
                    f.write(f"  物件計數:\n")
                    for obj_type, count in non_zero.items():
                        f.write(f"    {obj_type}: {count}\n")
                f.write("\n")
            
            # 增長趨勢
            if growth_data:
                f.write("\n物件增長趨勢\n")
                f.write("-" * 80 + "\n")
                for obj_type, counts in growth_data.items():
                    f.write(f"{obj_type}:\n")
                    f.write(f"  序列: {counts}\n")
                    f.write(f"  初始: {counts[0]}, 最終: {counts[-1]}, 變化: {counts[-1] - counts[0]:+d}\n")
                    f.write("\n")
            
            # 洩漏嫌疑
            if suspects:
                f.write("\n洩漏嫌疑類型\n")
                f.write("-" * 80 + "\n")
                for suspect in suspects:
                    f.write(f"- {suspect}\n")
                    
                    # 顯示引用計數詳情
                    objects = objgraph.by_type(suspect)
                    if objects:
                        f.write(f"  當前物件數: {len(objects)}\n")
                        for idx, obj in enumerate(objects[:3]):
                            f.write(f"  物件 #{idx + 1}:\n")
                            f.write(f"    記憶體位址: {hex(id(obj))}\n")
                            f.write(f"    引用計數: {sys.getrefcount(obj)}\n")
                            
                            referrers = gc.get_referrers(obj)
                            f.write(f"    引用來源: {len(referrers)} 個\n")
                            for ref_idx, ref in enumerate(referrers[:3]):
                                ref_type = type(ref).__name__
                                f.write(f"      [{ref_idx + 1}] {ref_type}\n")
                    f.write("\n")
            else:
                f.write("\n未發現明顯的洩漏嫌疑類型\n")
            
            # 建議
            f.write("\n分析建議\n")
            f.write("-" * 80 + "\n")
            if suspects:
                f.write("1. 檢查嫌疑類型的清理邏輯是否完整\n")
                f.write("2. 確認所有信號連接都已正確斷開\n")
                f.write("3. 檢查是否有循環引用\n")
                f.write("4. 驗證 deleteLater() 和 processEvents() 的調用順序\n")
                f.write("5. 使用 objgraph.show_backrefs() 追蹤引用鏈\n")
            else:
                f.write("1. 當前未發現明顯的記憶體洩漏\n")
                f.write("2. 持續監控長時間運行後的記憶體使用量\n")
                f.write("3. 考慮使用 memory_profiler 進行更詳細的分析\n")
            
            f.write("\n報告結束\n")
            f.write("=" * 80 + "\n")


def main():
    """主函數"""
    print("=" * 80)
    print("F1T GUI 深度引用鏈追蹤腳本")
    print("=" * 80)
    print("\n此腳本將自動化執行以下分析:")
    print("1. 記憶體快照（基線、開啟模組、關閉模組、連續 GC）")
    print("2. 物件增長趨勢分析")
    print("3. 洩漏嫌疑類型識別")
    print("4. 深度引用鏈追蹤")
    print("5. 引用關係圖生成（如果安裝了 graphviz）")
    print("6. 詳細分析報告")
    
    print("\n依賴檢查:")
    print(f"  objgraph: {'已安裝' if OBJGRAPH_AVAILABLE else '未安裝'}")
    print(f"  graphviz: {'已安裝' if GRAPHVIZ_AVAILABLE else '未安裝（可選）'}")
    
    if not OBJGRAPH_AVAILABLE:
        print("\nERROR: 缺少必要依賴，請執行:")
        print("  pip install objgraph")
        sys.exit(1)
    
    # 創建分析器
    analyzer = DeepReferenceChainAnalyzer(output_dir="memory_analysis")
    
    # 執行自動化分析
    try:
        analyzer.automated_analysis_workflow()
    except KeyboardInterrupt:
        print("\n\n分析被用戶中斷")
    except Exception as e:
        print(f"\n\nERROR: 分析過程中發生錯誤: {e}")
        traceback.print_exc()
    
    print("\n分析腳本執行完畢")


if __name__ == "__main__":
    main()
