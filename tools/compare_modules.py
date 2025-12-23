"""
模組完整性對比工具
自動對比兩個模組的所有方法、屬性和調用鏈，確保功能一致性

使用方式：
    python compare_modules.py speed brake time_axis
    
    參數：
        source_module: 源模組名稱（例如：speed）
        target_module: 目標模組名稱（例如：brake）
        feature: 要對比的功能（例如：time_axis）
"""

import os
import re
from typing import List, Dict, Tuple
from pathlib import Path

class ModuleComparator:
    def __init__(self, source_module: str, target_module: str, feature: str):
        self.source_module = source_module
        self.target_module = target_module
        self.feature = feature
        
        # 定義模組路徑
        self.source_mdi_path = f"modules/gui/lap_analysis/{source_module}_analysis/{source_module}_analysis_mdi.py"
        self.source_widget_path = f"modules/gui/lap_analysis/{source_module}_analysis/{source_module}_analysis_chart_widget.py"
        self.target_mdi_path = f"modules/gui/lap_analysis/{target_module}_analysis/{target_module}_analysis_mdi.py"
        self.target_widget_path = f"modules/gui/lap_analysis/{target_module}_analysis/{target_module}_analysis_chart_widget.py"
        
    def search_pattern_in_file(self, file_path: str, pattern: str) -> List[Tuple[int, str]]:
        """在檔案中搜索模式，返回 (行號, 內容) 列表"""
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append((line_num, line.rstrip()))
        except FileNotFoundError:
            print(f"⚠️  檔案不存在: {file_path}")
        return results
    
    def compare_time_axis_feature(self):
        """對比時間軸功能的完整實現"""
        print("=" * 80)
        print(f"🔍 對比功能：時間軸切換")
        print(f"📁 源模組：{self.source_module}")
        print(f"📁 目標模組：{self.target_module}")
        print("=" * 80)
        print()
        
        # 1. 搜索核心方法
        print("階段 1：搜索核心方法")
        print("-" * 80)
        
        patterns = [
            ("set_time_axis_mode", "set_time_axis_mode"),
            ("use_time_axis", "use_time_axis"),
            ("driver1_time", "driver1_time"),
            ("driver2_time", "driver2_time"),
            ("min_time", "min_time"),
            ("max_time", "max_time"),
        ]
        
        for pattern_name, pattern in patterns:
            print(f"\n🔎 搜索: {pattern}")
            
            # 搜索源模組 Widget
            source_widget_results = self.search_pattern_in_file(self.source_widget_path, pattern)
            print(f"  {self.source_module} Widget: {len(source_widget_results)} 個匹配")
            for line_num, line in source_widget_results[:3]:  # 只顯示前3個
                print(f"    Line {line_num}: {line[:80]}")
            
            # 搜索目標模組 Widget
            target_widget_results = self.search_pattern_in_file(self.target_widget_path, pattern)
            print(f"  {self.target_module} Widget: {len(target_widget_results)} 個匹配")
            for line_num, line in target_widget_results[:3]:
                print(f"    Line {line_num}: {line[:80]}")
            
            # 對比數量
            if len(source_widget_results) != len(target_widget_results):
                print(f"  ⚠️  警告：匹配數量不一致！")
                print(f"     {self.source_module}: {len(source_widget_results)} 個")
                print(f"     {self.target_module}: {len(target_widget_results)} 個")
        
        # 2. 搜索調用點
        print("\n\n階段 2：搜索調用點")
        print("-" * 80)
        
        call_patterns = [
            ("set_time_axis_mode 調用", r"\.set_time_axis_mode\("),
            ("update_cross_event_comparison", r"def update_cross_event_comparison"),
            ("_on_cross_event_data_loaded", r"def _on_cross_event_data_loaded"),
            ("update_lap_parameters", r"def update_lap_parameters"),
        ]
        
        for call_name, call_pattern in call_patterns:
            print(f"\n🔎 搜索調用: {call_name}")
            
            # 搜索源模組 MDI
            source_mdi_results = self.search_pattern_in_file(self.source_mdi_path, call_pattern)
            print(f"  {self.source_module} MDI: {len(source_mdi_results)} 個匹配")
            for line_num, line in source_mdi_results:
                print(f"    Line {line_num}: {line[:80]}")
            
            # 搜索目標模組 MDI
            target_mdi_results = self.search_pattern_in_file(self.target_mdi_path, call_pattern)
            print(f"  {self.target_module} MDI: {len(target_mdi_results)} 個匹配")
            for line_num, line in target_mdi_results:
                print(f"    Line {line_num}: {line[:80]}")
            
            # 對比數量
            if len(source_mdi_results) != len(target_mdi_results):
                print(f"  ⚠️  警告：調用點數量不一致！")
                print(f"     {self.source_module}: {len(source_mdi_results)} 個")
                print(f"     {self.target_module}: {len(target_mdi_results)} 個")
        
        # 3. 生成對比報告
        print("\n\n階段 3：生成詳細對比建議")
        print("-" * 80)
        print("\n建議執行的手動對比步驟：")
        print("1. 對比 __init__() 方法中的屬性初始化")
        print(f"   - {self.source_module}: grep_search '__init__' {self.source_widget_path}")
        print(f"   - {self.target_module}: grep_search '__init__' {self.target_widget_path}")
        print()
        print("2. 對比 set_time_axis_mode() 方法的完整實現")
        print(f"   - {self.source_module}: read_file {self.source_widget_path} (搜索 set_time_axis_mode)")
        print(f"   - {self.target_module}: read_file {self.target_widget_path} (搜索 set_time_axis_mode)")
        print()
        print("3. 對比所有調用 set_time_axis_mode() 的位置")
        print(f"   - 確認調用順序一致")
        print(f"   - 確認調用時機一致")
        print()
        print("4. 執行完整測試場景")
        print("   - 場景 1：首次載入（時間軸未勾選）")
        print("   - 場景 2：勾選時間軸")
        print("   - 場景 3：取消勾選時間軸")
        print("   - 場景 4：跨賽事模式 + 時間軸")
        print("   - 場景 5：跨賽事模式 + 取消時間軸")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("使用方式：python compare_modules.py <source_module> <target_module> [feature]")
        print("範例：python compare_modules.py speed brake time_axis")
        sys.exit(1)
    
    source = sys.argv[1]
    target = sys.argv[2]
    feature = sys.argv[3] if len(sys.argv) > 3 else "time_axis"
    
    comparator = ModuleComparator(source, target, feature)
    comparator.compare_time_axis_feature()
