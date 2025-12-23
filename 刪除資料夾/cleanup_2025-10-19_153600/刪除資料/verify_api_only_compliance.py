#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API-ONLY 模式合規性驗證腳本
驗證所有 lap_analysis 模組是否符合 API-ONLY 政策
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class APIOnlyComplianceChecker:
    """API-ONLY 模式合規性檢查器"""
    
    def __init__(self, base_path: str = "modules/gui/lap_analysis"):
        self.base_path = Path(base_path)
        self.violations: List[Dict] = []
        self.compliant_markers: List[Dict] = []
        
        # 違規模式（這些不應該出現）
        self.violation_patterns = [
            r"main_window\.create_telemetry_analysis\(\)",
            r"parent_window\.create_telemetry_analysis_tab\(\)",
            r"parent_window\.open_telemetry_analysis\(\)",
            r"self\.parent_window\.create_telemetry_analysis",
            r"hasattr\(main_window,\s*['\"]create_telemetry_analysis['\"]\)",
        ]
        
        # 合規標記（這些應該存在）
        self.compliance_patterns = [
            r"\[API-ONLY\].*未找到現有遙測分析視窗",
            r"請手動開啟遙測分析模組",
            r"或通過 API 獲取數據",
            r"return False.*# .*不自動創建",
        ]
    
    def scan_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """掃描單個檔案"""
        violations = []
        compliances = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, start=1):
                # 檢查違規模式
                for pattern in self.violation_patterns:
                    if re.search(pattern, line):
                        violations.append({
                            'file': str(file_path),
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
                
                # 檢查合規標記
                for pattern in self.compliance_patterns:
                    if re.search(pattern, line):
                        compliances.append({
                            'file': str(file_path),
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
        
        except Exception as e:
            print(f"❌ 無法讀取檔案 {file_path}: {e}")
        
        return violations, compliances
    
    def scan_all_modules(self):
        """掃描所有模組"""
        print("🔍 開始掃描 lap_analysis 模組...")
        print(f"📂 掃描路徑: {self.base_path.absolute()}\n")
        
        # 查找所有 *_mdi.py 檔案
        mdi_files = list(self.base_path.rglob("*_mdi.py"))
        
        if not mdi_files:
            print("⚠️  未找到任何 *_mdi.py 檔案")
            return
        
        print(f"📄 找到 {len(mdi_files)} 個模組檔案\n")
        
        for file_path in mdi_files:
            violations, compliances = self.scan_file(file_path)
            self.violations.extend(violations)
            self.compliant_markers.extend(compliances)
    
    def print_report(self):
        """打印報告"""
        print("=" * 80)
        print("🎯 API-ONLY 模式合規性檢查報告")
        print("=" * 80)
        print()
        
        # 違規報告
        if self.violations:
            print("❌ 發現違規代碼！")
            print(f"總計: {len(self.violations)} 處違規\n")
            
            for i, violation in enumerate(self.violations, start=1):
                print(f"違規 #{i}:")
                print(f"  檔案: {violation['file']}")
                print(f"  行號: {violation['line']}")
                print(f"  內容: {violation['content']}")
                print(f"  模式: {violation['pattern']}")
                print()
        else:
            print("✅ 未發現違規代碼！")
            print("所有模組都符合 API-ONLY 政策\n")
        
        # 合規標記報告
        if self.compliant_markers:
            print(f"✅ 發現合規標記: {len(self.compliant_markers)} 處")
            print()
            
            # 統計每個檔案的合規標記數量
            file_stats = {}
            for marker in self.compliant_markers:
                file_name = Path(marker['file']).parent.name
                file_stats[file_name] = file_stats.get(file_name, 0) + 1
            
            print("📊 各模組合規標記統計:")
            for file_name, count in sorted(file_stats.items()):
                print(f"  {file_name:30s}: {count} 處")
            print()
        else:
            print("⚠️  未發現合規標記")
            print("可能需要添加 [API-ONLY] 標記\n")
        
        # 總結
        print("=" * 80)
        if not self.violations and self.compliant_markers:
            print("🎉 恭喜！所有模組完全符合 API-ONLY 模式政策")
            print("✨ 修復成功，系統已達到合規標準")
        elif self.violations:
            print("⚠️  仍有違規代碼需要修復")
            print("請參考上述違規列表進行修正")
        else:
            print("⚠️  未檢測到明確的合規標記")
            print("建議添加 [API-ONLY] 標記以提高代碼可讀性")
        print("=" * 80)

def main():
    """主函數"""
    checker = APIOnlyComplianceChecker()
    checker.scan_all_modules()
    checker.print_report()

if __name__ == '__main__':
    main()
