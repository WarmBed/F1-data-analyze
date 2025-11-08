#!/usr/bin/env python3
"""
測試 Ideal Lap Analysis 隱藏 Position 欄位功能
Test Hide Position Column in Ideal Lap Analysis Modules

驗證以下功能：
1. Ideal Lap Ranking Table - Position 欄位已隱藏
2. Sector Comparison - Position 欄位已隱藏

作者: F1T Team
日期: 2025-10-21
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

# 導入測試模組
from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_widget import IdealLapRankingTableWidget
from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_table_widget import IdealLapSectorComparisonTableWidget


class TestHidePositionColumn(QMainWindow):
    """測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("測試隱藏 Position 欄位 - Ideal Lap Analysis")
        self.setGeometry(100, 100, 1400, 800)
        
        # 創建主要 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 創建 Tab Widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Tab 1: Ranking Table
        self.ranking_widget = IdealLapRankingTableWidget()
        tab_widget.addTab(self.ranking_widget, "Ranking Table (Position 已隱藏)")
        
        # Tab 2: Sector Comparison
        self.sector_widget = IdealLapSectorComparisonTableWidget()
        tab_widget.addTab(self.sector_widget, "Sector Comparison (Position 已隱藏)")
        
        # 填充測試數據
        self._populate_test_data()
    
    def _populate_test_data(self):
        """填充測試數據"""
        # 測試數據 - Ranking Table
        ranking_data = [
            {
                "position": 1,
                "driver": "VER",
                "team": "Red Bull Racing",
                "fastest_lap_time": 94.500,
                "ideal_lap_time": 94.183,
                "time_gap": 0.000,
                "gap_to_session_fastest": 0.000,
                "sector_breakdown": {
                    "sector_1": {"fastest_time": 25.5, "ideal_time": 25.4, "is_optimal_in_fastest": False},
                    "sector_2": {"fastest_time": 38.2, "ideal_time": 38.1, "is_optimal_in_fastest": True},
                    "sector_3": {"fastest_time": 30.8, "ideal_time": 30.683, "is_optimal_in_fastest": False}
                }
            },
            {
                "position": 2,
                "driver": "LEC",
                "team": "Ferrari",
                "fastest_lap_time": 95.200,
                "ideal_lap_time": 94.850,
                "time_gap": 0.667,
                "gap_to_session_fastest": 0.700,
                "sector_breakdown": {
                    "sector_1": {"fastest_time": 25.8, "ideal_time": 25.6, "is_optimal_in_fastest": True},
                    "sector_2": {"fastest_time": 38.5, "ideal_time": 38.3, "is_optimal_in_fastest": False},
                    "sector_3": {"fastest_time": 30.9, "ideal_time": 30.950, "is_optimal_in_fastest": True}
                }
            },
            {
                "position": 3,
                "driver": "HAM",
                "team": "Mercedes",
                "fastest_lap_time": 95.500,
                "ideal_lap_time": 95.100,
                "time_gap": 0.917,
                "gap_to_session_fastest": 1.000,
                "sector_breakdown": {
                    "sector_1": {"fastest_time": 26.0, "ideal_time": 25.8, "is_optimal_in_fastest": False},
                    "sector_2": {"fastest_time": 38.7, "ideal_time": 38.5, "is_optimal_in_fastest": True},
                    "sector_3": {"fastest_time": 30.8, "ideal_time": 30.800, "is_optimal_in_fastest": True}
                }
            }
        ]
        
        # 測試數據 - Sector Comparison
        sector_data = {
            "analysis_result": {
                "ranking": [
                    {
                        "position": 1,
                        "driver": "VER",
                        "team": "Red Bull Racing",
                        "sector_breakdown": {
                            "sector_1": {"delta": 0.100},
                            "sector_2": {"delta": 0.050},
                            "sector_3": {"delta": 0.117}
                        }
                    },
                    {
                        "position": 2,
                        "driver": "LEC",
                        "team": "Ferrari",
                        "sector_breakdown": {
                            "sector_1": {"delta": 0.200},
                            "sector_2": {"delta": 0.150},
                            "sector_3": {"delta": 0.000}
                        }
                    },
                    {
                        "position": 3,
                        "driver": "HAM",
                        "team": "Mercedes",
                        "sector_breakdown": {
                            "sector_1": {"delta": 0.200},
                            "sector_2": {"delta": 0.200},
                            "sector_3": {"delta": 0.000}
                        }
                    }
                ]
            }
        }
        
        # 填充 Ranking Table
        self.ranking_widget.populate_table(ranking_data)
        
        # 填充 Sector Comparison
        self.sector_widget.update_data(sector_data)
        
        print("✅ 測試數據已載入")
        print("📊 請檢查兩個 Tab：")
        print("   1. Ranking Table - Position 欄位應該已隱藏")
        print("   2. Sector Comparison - Position 欄位應該已隱藏")
        print("")
        print("✅ 驗證重點：")
        print("   - 第一個可見欄位應該是「車手」欄位")
        print("   - Position 欄位完全不顯示")
        print("   - 排序功能仍然正常")


def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle("Fusion")
    
    # 創建測試視窗
    window = TestHidePositionColumn()
    window.show()
    
    print("="*60)
    print("🧪 測試：隱藏 Position 欄位")
    print("="*60)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
