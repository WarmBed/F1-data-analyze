#!/usr/bin/env python3
"""
理想圈分段對比 Widget - 獨立測試視窗
Ideal Lap Sector Comparison Widget - Standalone Test

使用 JSON 檔案或 API 測試新重寫的 Widget

作者: F1T Team
日期: 2025-10-10
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt

# 添加專案根目錄到 sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_widget import (
    IdealLapSectorComparisonWidget
)


class SectorComparisonTestWindow(QMainWindow):
    """獨立測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("理想圈分段對比 Widget - 獨立測試")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建主 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主佈局
        main_layout = QVBoxLayout(main_widget)
        
        # ========== 控制面板 ==========
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # ========== 圖表 Widget ==========
        self.chart_widget = IdealLapSectorComparisonWidget(self)
        main_layout.addWidget(self.chart_widget, stretch=1)
        
        # ========== 狀態標籤 ==========
        self.status_label = QLabel("狀態: 等待載入數據...")
        main_layout.addWidget(self.status_label)
        
        print("[TEST] ✅ 測試視窗初始化完成")
    
    def _create_control_panel(self) -> QWidget:
        """創建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # 標題
        title = QLabel("📊 測試控制面板")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 載入 JSON 按鈕
        btn_load_json = QPushButton("📁 載入 JSON 檔案")
        btn_load_json.clicked.connect(self._load_json_file)
        layout.addWidget(btn_load_json)
        
        # 載入測試數據按鈕
        btn_load_test = QPushButton("🧪 載入測試數據")
        btn_load_test.clicked.connect(self._load_test_data)
        layout.addWidget(btn_load_test)
        
        # 排序選擇
        layout.addWidget(QLabel("排序:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "position (排名)",
            "ideal_lap (理想圈)",
            "fastest_lap (最快圈)",
            "delta (時間差)"
        ])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)
        
        # 清空圖表按鈕
        btn_clear = QPushButton("🗑️ 清空圖表")
        btn_clear.clicked.connect(self._clear_chart)
        layout.addWidget(btn_clear)
        
        # 匯出圖表按鈕
        btn_export = QPushButton("💾 匯出圖表")
        btn_export.clicked.connect(self._export_chart)
        layout.addWidget(btn_export)
        
        return panel
    
    def _load_json_file(self):
        """載入 JSON 檔案"""
        try:
            # 開啟檔案對話框
            json_dir = project_root / "json"
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "選擇 JSON 檔案",
                str(json_dir),
                "JSON Files (*.json);;All Files (*.*)"
            )
            
            if not file_path:
                print("[TEST] 使用者取消選擇檔案")
                return
            
            # 讀取 JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[TEST] ✅ 讀取 JSON 成功: {Path(file_path).name}")
            print(f"[TEST] 數據鍵: {list(data.keys())}")
            
            # 更新圖表
            self.chart_widget.update_data(data)
            
            # 更新狀態
            driver_count = len(data.get("comparison_data", []))
            self.status_label.setText(f"✅ 已載入 {driver_count} 位車手的數據")
            
        except Exception as e:
            error_msg = f"載入 JSON 失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "錯誤", error_msg)
    
    def _load_test_data(self):
        """載入測試數據（模擬 API 回應）"""
        try:
            print("[TEST] 🧪 生成測試數據...")
            
            # ✅ 參考實際 JSON 結構 (ideal_lap_ranking_2025_Japan_R.json)
            # 結構: analysis_result.ranking[].sector_breakdown.sector_X.time
            test_data = {
                "analysis_result": {
                    "ranking": [
                        {
                            "driver": "VER",
                            "driver_name": "Max Verstappen",
                            "team": "Red Bull Racing",
                            "position": 1,
                            "ideal_lap_time": 75.123,
                            "fastest_lap_time": 75.156,
                            "time_gap": 0.033,
                            "gap_to_leader": 0.0,
                            "sector_breakdown": {
                                "sector_1": {"time": 25.012, "is_optimal_in_fastest": False},
                                "sector_2": {"time": 25.034, "is_optimal_in_fastest": False},
                                "sector_3": {"time": 25.077, "is_optimal_in_fastest": True}
                            }
                        },
                        {
                            "driver": "PER",
                            "driver_name": "Sergio Perez",
                            "team": "Red Bull Racing",
                            "position": 2,
                            "ideal_lap_time": 75.456,
                            "fastest_lap_time": 75.512,
                            "time_gap": 0.056,
                            "gap_to_leader": 0.333,
                            "sector_breakdown": {
                                "sector_1": {"time": 25.123, "is_optimal_in_fastest": False},
                                "sector_2": {"time": 25.145, "is_optimal_in_fastest": True},
                                "sector_3": {"time": 25.188, "is_optimal_in_fastest": False}
                            }
                        },
                        {
                            "driver": "LEC",
                            "driver_name": "Charles Leclerc",
                            "team": "Ferrari",
                            "position": 3,
                            "ideal_lap_time": 75.678,
                            "fastest_lap_time": 75.734,
                            "time_gap": 0.056,
                            "gap_to_leader": 0.555,
                            "sector_breakdown": {
                                "sector_1": {"time": 25.234, "is_optimal_in_fastest": False},
                                "sector_2": {"time": 25.256, "is_optimal_in_fastest": False},
                                "sector_3": {"time": 25.188, "is_optimal_in_fastest": False}
                            }
                        },
                        {
                            "driver": "SAI",
                            "driver_name": "Carlos Sainz",
                            "team": "Ferrari",
                            "position": 4,
                            "ideal_lap_time": 75.789,
                            "fastest_lap_time": 75.856,
                            "time_gap": 0.067,
                            "gap_to_leader": 0.666,
                            "sector_breakdown": {
                                "sector_1": {"time": 25.345, "is_optimal_in_fastest": False},
                                "sector_2": {"time": 25.367, "is_optimal_in_fastest": False},
                                "sector_3": {"time": 25.077, "is_optimal_in_fastest": True}
                            }
                        },
                        {
                            "driver": "HAM",
                            "driver_name": "Lewis Hamilton",
                            "team": "Mercedes",
                            "position": 5,
                            "ideal_lap_time": 75.890,
                            "fastest_lap_time": 75.967,
                            "time_gap": 0.077,
                            "gap_to_leader": 0.767,
                            "sector_breakdown": {
                                "sector_1": {"time": 25.456, "is_optimal_in_fastest": False},
                                "sector_2": {"time": 25.478, "is_optimal_in_fastest": False},
                                "sector_3": {"time": 25.956, "is_optimal_in_fastest": False}
                            }
                        }
                    ],
                    "summary": {
                        "total_drivers": 5,
                        "perfect_lap_count": 0,
                        "fastest_ideal_lap": {
                            "driver": "VER",
                            "time": 75.123
                        }
                    }
                },
                "metadata": {
                    "year": 2025,
                    "race": "Japan",
                    "session": "R",
                    "function_id": 53,
                    "analysis_timestamp": "2025-10-10T00:00:00"
                }
            }
            
            # 更新圖表
            self.chart_widget.update_data(test_data)
            
            # 更新狀態
            self.status_label.setText("✅ 已載入測試數據 (5 位車手)")
            
            print("[TEST] ✅ 測試數據載入成功")
            
        except Exception as e:
            error_msg = f"載入測試數據失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "錯誤", error_msg)
    
    def _on_sort_changed(self, index):
        """排序方式變更"""
        sort_mapping = {
            0: "position",
            1: "ideal_lap",
            2: "fastest_lap",
            3: "delta"
        }
        
        sort_key = sort_mapping.get(index, "position")
        print(f"[TEST] 排序方式變更: {sort_key}")
        
        try:
            self.chart_widget.sort_data(sort_key)
            self.status_label.setText(f"✅ 已按 {sort_key} 排序")
        except Exception as e:
            error_msg = f"排序失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.warning(self, "警告", error_msg)
    
    def _clear_chart(self):
        """清空圖表"""
        try:
            self.chart_widget.clear_chart()
            self.status_label.setText("✅ 圖表已清空")
            print("[TEST] ✅ 圖表已清空")
        except Exception as e:
            error_msg = f"清空圖表失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.warning(self, "警告", error_msg)
    
    def _export_chart(self):
        """匯出圖表"""
        try:
            # 開啟儲存對話框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "匯出圖表",
                "sector_comparison.png",
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*.*)"
            )
            
            if not file_path:
                print("[TEST] 使用者取消匯出")
                return
            
            # 匯出圖表
            success = self.chart_widget.export_chart(file_path)
            
            if success:
                self.status_label.setText(f"✅ 圖表已匯出至: {Path(file_path).name}")
                print(f"[TEST] ✅ 圖表已匯出: {file_path}")
            else:
                raise Exception("匯出失敗")
            
        except Exception as e:
            error_msg = f"匯出圖表失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, "錯誤", error_msg)


def main():
    """主程式入口"""
    print("=" * 60)
    print("理想圈分段對比 Widget - 獨立測試")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle("Fusion")
    
    # 創建測試視窗
    window = SectorComparisonTestWindow()
    window.show()
    
    print("[TEST] 🚀 測試視窗已啟動")
    print("[TEST] 💡 請點擊「載入測試數據」或「載入 JSON 檔案」來測試圖表")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
