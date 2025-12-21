#!/usr/bin/env python3
"""
測試三項 UI 修正
Test Three UI Fixes

測試項目：
1. Ranking Table - Sectors 欄位：綠色 ✓ 和黑色 ✗
2. Ranking Table - Gap to Session Fastest 欄位：使用統一顏色標準
3. Sector Comparison - Cumulative Delta 欄位：支援點擊排序

Author: F1T Team
Date: 2025-10-10
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QLabel
from PyQt5.QtCore import Qt

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_widget import IdealLapRankingTableWidget
from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_table_widget import IdealLapSectorComparisonTableWidget


class TestWindow(QMainWindow):
    """測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("三項 UI 修正測試 - Three UI Fixes Test")
        self.setGeometry(100, 100, 1400, 800)
        
        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 說明標籤
        info_label = QLabel(
            "測試三項修正：\n"
            "1️⃣ Ranking Table - Sectors 欄位：✓ 應為綠色，✗ 應為黑色\n"
            "2️⃣ Ranking Table - Gap to Session Fastest：顏色應符合統一標準 (0.2s, 0.5s 分界)\n"
            "3️⃣ Sector Comparison - Cumulative Delta：點擊表頭應可遞增/遞減排序"
        )
        info_label.setStyleSheet("font-size: 11pt; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(info_label)
        
        # 分頁容器
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Ranking Table
        self.ranking_widget = IdealLapRankingTableWidget()
        self.tabs.addTab(self.ranking_widget, "📊 Ranking Table (修正 1 & 2)")
        
        # Tab 2: Sector Comparison
        self.sector_widget = IdealLapSectorComparisonTableWidget()
        self.tabs.addTab(self.sector_widget, "📈 Sector Comparison (修正 3)")
        
        # 載入測試數據
        self._load_test_data()
    
    def _load_test_data(self):
        """載入測試數據"""
        # 搜尋最新的理想圈分析 JSON
        json_dir = Path(__file__).parent / "json"
        
        # 尋找理想圈分析檔案 (function 53)
        ideal_lap_files = list(json_dir.glob("ideal_lap_analysis_all_drivers_*_2025_*.json"))
        
        if not ideal_lap_files:
            print("⚠️  找不到理想圈分析 JSON 檔案")
            print("💡 請先執行 CLI 生成數據：")
            print("   python f1_analysis_modular_main.py -f 53 -y 2025 -r Japan -s R")
            return
        
        # 使用最新檔案
        json_file = sorted(ideal_lap_files)[-1]
        print(f"📂 載入測試數據: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取分析結果
            analysis_result = data.get("analysis_result", {})
            ranking_data = analysis_result.get("ranking", [])
            
            if not ranking_data:
                print("❌ JSON 中找不到 ranking 數據")
                return
            
            print(f"✅ 載入 {len(ranking_data)} 位車手數據")
            
            # 填充 Ranking Table
            self.ranking_widget.populate_table(ranking_data)
            
            # 更新統計摘要
            summary = {
                "total_drivers": analysis_result.get("total_drivers"),
                "session_fastest_lap": analysis_result.get("session_fastest_lap"),
                "fastest_ideal_lap": analysis_result.get("fastest_ideal_lap"),
                "ideal_lap_range": analysis_result.get("ideal_lap_range")
            }
            self.ranking_widget.update_summary(summary)
            
            # 填充 Sector Comparison
            self.sector_widget.update_data(data)
            
            print("\n" + "="*60)
            print("🧪 測試指引:")
            print("="*60)
            print("1️⃣  檢查 Ranking Table 的 'Sectors' 欄位：")
            print("    - ✓ 符號應該是綠色")
            print("    - ✗ 符號應該是黑色")
            print("    - 混合時（例如 ✓✗✗）顏色應正確分離")
            print()
            print("2️⃣  檢查 Ranking Table 的 'Gap to Session Fastest' 欄位：")
            print("    - < 0.2s: 淺綠色 (Light Green)")
            print("    - 0.2s ~ 0.5s: 淺黃色 (Light Yellow)")
            print("    - > 0.5s: 淺粉色 (Light Pink)")
            print()
            print("3️⃣  測試 Sector Comparison 的 'Cumulative Delta' 排序：")
            print("    - 點擊表頭應該觸發遞增排序")
            print("    - 再次點擊應該切換為遞減排序")
            print("="*60)
            
        except Exception as e:
            print(f"❌ 載入數據失敗: {e}")
            import traceback
            traceback.print_exc()


def main():
    app = QApplication(sys.argv)
    
    # 設定全域字體
    from PyQt5.QtGui import QFont
    font = QFont()
    font.setPointSize(9)
    app.setFont(font)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
