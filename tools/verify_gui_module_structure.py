#!/usr/bin/env python3
"""
GUI 模組結構驗證工具

驗證所有 GUI 模組是否遵循統一架構標準：
- UniversalDataLoader 繼承
- UniversalAnalysisMDI 繼承
- ApiWorker 統一性
- i18n 覆蓋率
- Emoji 檢查

Author: F1T Team
Date: 2025-10-11
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ModuleStructureVerifier:
    """GUI 模組結構驗證器"""
    
    def __init__(self):
        self.gui_modules_path = PROJECT_ROOT / "modules" / "gui"
        self.results = {
            "total_modules": 0,
            "universal_loader": [],
            "universal_mdi": [],
            "custom_api_worker": [],
            "telemetry_loader": [],
            "i18n_coverage": {},
            "emoji_found": {},
            "chart_widget_lines": {}
        }
    
    def scan_all_modules(self) -> Dict:
        """掃描所有 GUI 模組"""
        print("🔍 開始掃描 GUI 模組結構...\n")
        
        # 定義要掃描的模組資料夾
        module_folders = [
            "accident_analysis",
            "rain_analysis",
            "tire_analysis",
            "track_analysis",
            "pitstop_analysis",
            "lap_box_plot_analysis",
            "Throttle_analysis/throttle_box_plot_analysis",
            "Throttle_analysis/throttle_line_chart_analysis",
            "ideal_lap_analysis/ideal_lap_ranking_table",
            "ideal_lap_analysis/ideal_lap_sector_comparison",
            "ideal_lap_analysis/ideal_lap_sector_heatmap",
            "driver_race/detailed_lap_analysis",
            "driver_race/lap_box_plot_analysis",
            "lap_analysis/speed_analysis",
            "lap_analysis/brake_analysis",
            "lap_analysis/Throttle_analysis",
            "lap_analysis/gear_analysis",
            "lap_analysis/rpm_analysis",
            "lap_analysis/acceleration_analysis",
            "lap_analysis/speeddiff_analysis",
            "lap_analysis/distancediff_analysis",
        ]
        
        self.results["total_modules"] = len(module_folders)
        
        for module_path in module_folders:
            full_path = self.gui_modules_path / module_path
            if full_path.exists():
                self._verify_module(module_path, full_path)
        
        return self.results
    
    def _verify_module(self, module_name: str, module_path: Path):
        """驗證單一模組"""
        print(f"📦 檢查模組: {module_name}")
        
        # 檢查 DataLoader
        self._check_data_loader(module_name, module_path)
        
        # 檢查 MDI
        self._check_mdi(module_name, module_path)
        
        # 檢查 ApiWorker
        self._check_api_worker(module_name, module_path)
        
        # 檢查 Chart Widget
        self._check_chart_widget(module_name, module_path)
        
        # 檢查 i18n
        self._check_i18n(module_name, module_path)
        
        # 檢查 emoji
        self._check_emoji(module_name, module_path)
        
        print()
    
    def _check_data_loader(self, module_name: str, module_path: Path):
        """檢查 DataLoader 類型"""
        loader_files = list(module_path.glob("*data_loader*.py"))
        if not loader_files:
            return
        
        for loader_file in loader_files:
            content = loader_file.read_text(encoding="utf-8")
            
            if "UniversalDataLoader" in content:
                self.results["universal_loader"].append(module_name)
                print(f"  ✅ UniversalDataLoader")
            elif "TelemetryDataLoader" in content:
                self.results["telemetry_loader"].append(module_name)
                print(f"  ⚠️  TelemetryDataLoader (待遷移)")
    
    def _check_mdi(self, module_name: str, module_path: Path):
        """檢查 MDI 類型"""
        mdi_files = list(module_path.glob("*mdi*.py"))
        if not mdi_files:
            return
        
        for mdi_file in mdi_files:
            content = mdi_file.read_text(encoding="utf-8")
            
            if "UniversalAnalysisMDI" in content:
                self.results["universal_mdi"].append(module_name)
                print(f"  ✅ UniversalAnalysisMDI")
    
    def _check_api_worker(self, module_name: str, module_path: Path):
        """檢查自訂 ApiWorker"""
        py_files = list(module_path.glob("*.py"))
        
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            
            # 搜索自訂 ApiWorker 類別（排除 import）
            pattern = r"class\s+(\w+ApiWorker)\s*\(QThread\)"
            matches = re.findall(pattern, content)
            
            if matches:
                for worker_name in matches:
                    self.results["custom_api_worker"].append({
                        "module": module_name,
                        "worker": worker_name,
                        "file": py_file.name
                    })
                    print(f"  ⚠️  自訂 ApiWorker: {worker_name}")
    
    def _check_chart_widget(self, module_name: str, module_path: Path):
        """檢查 Chart Widget 程式碼行數"""
        chart_files = list(module_path.glob("*chart_widget*.py"))
        
        if chart_files:
            for chart_file in chart_files:
                lines = len(chart_file.read_text(encoding="utf-8").splitlines())
                self.results["chart_widget_lines"][module_name] = lines
                
                if lines > 1000:
                    print(f"  ⚠️  Chart Widget: {lines} 行（重複代碼）")
                else:
                    print(f"  ✅ Chart Widget: {lines} 行")
    
    def _check_i18n(self, module_name: str, module_path: Path):
        """檢查 i18n 覆蓋率"""
        py_files = list(module_path.glob("*.py"))
        
        total_strings = 0
        translated_strings = 0
        
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            
            # 計算所有使用者可見字串（簡化版）
            ui_strings = re.findall(r'["\']([\u4e00-\u9fa5]+.*?)["\']', content)
            total_strings += len(ui_strings)
            
            # 計算 tr() 調用
            tr_calls = re.findall(r'tr\s*\(', content)
            translated_strings += len(tr_calls)
        
        if total_strings > 0:
            coverage = (translated_strings / total_strings) * 100
            self.results["i18n_coverage"][module_name] = coverage
            
            if coverage > 80:
                print(f"  ✅ i18n 覆蓋率: {coverage:.1f}%")
            elif coverage > 30:
                print(f"  🟡 i18n 覆蓋率: {coverage:.1f}%")
            else:
                print(f"  ❌ i18n 覆蓋率: {coverage:.1f}%")
    
    def _check_emoji(self, module_name: str, module_path: Path):
        """檢查 emoji 使用"""
        py_files = list(module_path.glob("*.py"))
        
        emoji_count = 0
        
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            
            # 簡單 emoji 檢測（Unicode 範圍）
            emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
            emojis = re.findall(emoji_pattern, content)
            emoji_count += len(emojis)
        
        if emoji_count > 0:
            self.results["emoji_found"][module_name] = emoji_count
            print(f"  ❌ 發現 {emoji_count} 個 emoji（違反原則 4）")
    
    def generate_report(self):
        """生成驗證報告"""
        print("\n" + "="*80)
        print("📊 GUI 模組結構驗證報告")
        print("="*80 + "\n")
        
        # 總覽
        print(f"📦 總模組數: {self.results['total_modules']}")
        print(f"✅ 使用 UniversalDataLoader: {len(self.results['universal_loader'])} 個")
        print(f"✅ 使用 UniversalAnalysisMDI: {len(self.results['universal_mdi'])} 個")
        print(f"⚠️  使用 TelemetryDataLoader: {len(self.results['telemetry_loader'])} 個")
        print(f"⚠️  自訂 ApiWorker: {len(self.results['custom_api_worker'])} 個")
        print()
        
        # Chart Widget 統計
        total_chart_lines = sum(self.results["chart_widget_lines"].values())
        print(f"📈 Chart Widget 總行數: {total_chart_lines:,} 行")
        if len(self.results["chart_widget_lines"]) > 0:
            avg_lines = total_chart_lines / len(self.results["chart_widget_lines"])
            print(f"📊 平均每模組: {avg_lines:.0f} 行")
        print()
        
        # i18n 統計
        if self.results["i18n_coverage"]:
            avg_i18n = sum(self.results["i18n_coverage"].values()) / len(self.results["i18n_coverage"])
            print(f"🌐 平均 i18n 覆蓋率: {avg_i18n:.1f}%")
        
        # Emoji 統計
        total_emoji = sum(self.results["emoji_found"].values())
        if total_emoji > 0:
            print(f"❌ 總 emoji 數量: {total_emoji} 個（需全部移除）")
        print()
        
        # 詳細列表
        print("🚨 需要統一的模組（使用 TelemetryDataLoader）:")
        for module in self.results["telemetry_loader"]:
            print(f"  - {module}")
        print()
        
        print("⚠️  需要統一的 ApiWorker:")
        for worker_info in self.results["custom_api_worker"]:
            print(f"  - {worker_info['module']}: {worker_info['worker']}")
        print()
        
        print("✅ 已使用通用架構的模組:")
        for module in self.results["universal_loader"]:
            print(f"  - {module}")
        print()
        
        # 結論
        print("="*80)
        print("📝 結論:")
        compliance_rate = (len(self.results["universal_loader"]) / self.results["total_modules"]) * 100
        print(f"架構合規率: {compliance_rate:.1f}%")
        
        if compliance_rate < 50:
            print("❌ 合規率低於 50%，建議立即執行統一化計畫")
        elif compliance_rate < 80:
            print("🟡 合規率介於 50-80%，建議繼續推進統一化")
        else:
            print("✅ 合規率高於 80%，架構已基本統一")
        print("="*80)


def main():
    """主函式"""
    verifier = ModuleStructureVerifier()
    verifier.scan_all_modules()
    verifier.generate_report()


if __name__ == "__main__":
    main()
