#!/usr/bin/env python3
"""
Demo 4: 完整功能測試（三個獨立視窗）
Complete Feature Test with Three Separate Windows

測試項目：
1. 同時顯示三個獨立視窗（低速/中速/高速彎）
2. 測試數據載入效能
3. 測試圖表切換流暢度
4. 測試匯出功能

執行命令：
python demo_4_test_all_corners.py
"""

import sys
import os
import json

# 設定路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMdiArea, QMdiSubWindow, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from modules.gui.all_drivers_corner_performance_analysis.corner_performance_scatter_widget import CornerPerformanceScatterWidget


class Demo4MainWindow(QMainWindow):
    """Demo 4 主視窗 - 使用 MDI 管理三個獨立視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 4: 完整功能測試 - 三個獨立視窗")
        self.setGeometry(50, 50, 1800, 1000)
        
        # 創建中心元件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 標題
        title_label = QLabel("全車手彎道性能分析 - Japan 2024 R")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 創建 MDI 區域
        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.SubWindowView)
        main_layout.addWidget(self.mdi_area)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.reload_btn = QPushButton("重新載入數據")
        self.reload_btn.clicked.connect(self.load_test_data)
        
        self.refresh_all_btn = QPushButton("刷新所有圖表")
        self.refresh_all_btn.clicked.connect(self.refresh_all_charts)
        
        self.export_all_btn = QPushButton("匯出所有圖表")
        self.export_all_btn.clicked.connect(self.export_all_charts)
        
        self.tile_windows_btn = QPushButton("平鋪視窗")
        self.tile_windows_btn.clicked.connect(self.tile_windows)
        
        self.cascade_windows_btn = QPushButton("層疊視窗")
        self.cascade_windows_btn.clicked.connect(self.cascade_windows)
        
        button_layout.addWidget(self.reload_btn)
        button_layout.addWidget(self.refresh_all_btn)
        button_layout.addWidget(self.export_all_btn)
        button_layout.addWidget(self.tile_windows_btn)
        button_layout.addWidget(self.cascade_windows_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 狀態欄
        self.status_label = QLabel("準備載入數據...")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        main_layout.addWidget(self.status_label)
        
        # 儲存圖表元件引用
        self.low_speed_widget = None
        self.mid_speed_widget = None
        self.high_speed_widget = None
        
        # 自動載入數據
        QTimer.singleShot(500, self.load_test_data)
    
    def create_corner_windows(self, data):
        """創建三個獨立的彎道分析視窗"""
        
        # 1. 低速彎視窗
        self.low_speed_widget = CornerPerformanceScatterWidget()
        self.low_speed_widget.current_corner_type = "low_speed"
        self.low_speed_widget.corner_combo.setCurrentIndex(0)  # 設定為低速彎
        self.low_speed_widget.update_data(data)
        
        low_sub_window = QMdiSubWindow()
        low_sub_window.setWidget(self.low_speed_widget)
        low_sub_window.setWindowTitle("低速彎性能分析 (< 100 km/h)")
        low_sub_window.setAttribute(Qt.WA_DeleteOnClose, False)
        self.mdi_area.addSubWindow(low_sub_window)
        low_sub_window.show()
        
        # 2. 中速彎視窗
        self.mid_speed_widget = CornerPerformanceScatterWidget()
        self.mid_speed_widget.current_corner_type = "mid_speed"
        self.mid_speed_widget.corner_combo.setCurrentIndex(1)  # 設定為中速彎
        self.mid_speed_widget.update_data(data)
        
        mid_sub_window = QMdiSubWindow()
        mid_sub_window.setWidget(self.mid_speed_widget)
        mid_sub_window.setWindowTitle("中速彎性能分析 (100-200 km/h)")
        mid_sub_window.setAttribute(Qt.WA_DeleteOnClose, False)
        self.mdi_area.addSubWindow(mid_sub_window)
        mid_sub_window.show()
        
        # 3. 高速彎視窗
        self.high_speed_widget = CornerPerformanceScatterWidget()
        self.high_speed_widget.current_corner_type = "high_speed"
        self.high_speed_widget.corner_combo.setCurrentIndex(2)  # 設定為高速彎
        self.high_speed_widget.update_data(data)
        
        high_sub_window = QMdiSubWindow()
        high_sub_window.setWidget(self.high_speed_widget)
        high_sub_window.setWindowTitle("高速彎性能分析 (> 200 km/h)")
        high_sub_window.setAttribute(Qt.WA_DeleteOnClose, False)
        self.mdi_area.addSubWindow(high_sub_window)
        high_sub_window.show()
        
        # 自動平鋪視窗
        QTimer.singleShot(100, self.tile_windows)
        
        print("✅ 三個獨立視窗已創建")
    
    def load_test_data(self):
        """載入測試數據"""
        try:
            self.status_label.setText("正在載入數據...")
            
            json_file = "json/all_drivers_cornering_analysis_2024_Japan_R.json"
            
            if not os.path.exists(json_file):
                self.status_label.setText(f"❌ JSON 檔案不存在: {json_file}")
                print(f"❌ JSON 檔案不存在: {json_file}")
                QMessageBox.critical(self, "錯誤", f"找不到數據檔案:\n{json_file}")
                return
            
            print(f"\n載入測試數據: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("✅ 數據載入成功")
            
            # 顯示數據摘要
            selected_corners = data.get('selected_corners', {})
            print("\n選擇的彎道：")
            for corner_type, corner_info in selected_corners.items():
                corner_num = corner_info['corner_number']
                avg_speed = corner_info['avg_apex_speed']
                print(f"  - {corner_type}: T{corner_num} ({avg_speed:.1f} km/h)")
            
            # 清空現有視窗
            for sub_window in self.mdi_area.subWindowList():
                sub_window.close()
            
            # 創建三個獨立視窗
            self.create_corner_windows(data)
            
            # 顯示統計資訊
            fastest_lap = data.get('fastest_lap_analysis', {})
            driver_count = fastest_lap.get('total_drivers', 0)
            
            status_text = f"✅ 數據載入完成 | {driver_count} 位車手 | Japan 2024 R | 三個獨立視窗"
            self.status_label.setText(status_text)
            
            print(f"\n✅ 所有視窗已創建並更新")
            
        except Exception as e:
            error_msg = f"❌ 載入數據失敗: {e}"
            self.status_label.setText(error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "錯誤", f"載入數據失敗:\n{str(e)}")
    
    def refresh_all_charts(self):
        """刷新所有圖表"""
        print("\n刷新所有圖表...")
        
        if self.low_speed_widget:
            self.low_speed_widget.draw_scatter_chart()
        if self.mid_speed_widget:
            self.mid_speed_widget.draw_scatter_chart()
        if self.high_speed_widget:
            self.high_speed_widget.draw_scatter_chart()
        
        self.status_label.setText("✅ 所有圖表已刷新")
        print("✅ 所有圖表已刷新")
    
    def export_all_charts(self):
        """匯出所有圖表"""
        print("\n匯出所有圖表...")
        
        try:
            output_dir = "output/corner_performance"
            os.makedirs(output_dir, exist_ok=True)
            
            exported_files = []
            
            # 匯出低速彎
            if self.low_speed_widget:
                low_file = os.path.join(output_dir, "low_speed_corner.png")
                self.low_speed_widget.figure.savefig(low_file, dpi=300, bbox_inches='tight')
                exported_files.append(low_file)
                print(f"✅ 低速彎圖表已匯出: {low_file}")
            
            # 匯出中速彎
            if self.mid_speed_widget:
                mid_file = os.path.join(output_dir, "mid_speed_corner.png")
                self.mid_speed_widget.figure.savefig(mid_file, dpi=300, bbox_inches='tight')
                exported_files.append(mid_file)
                print(f"✅ 中速彎圖表已匯出: {mid_file}")
            
            # 匯出高速彎
            if self.high_speed_widget:
                high_file = os.path.join(output_dir, "high_speed_corner.png")
                self.high_speed_widget.figure.savefig(high_file, dpi=300, bbox_inches='tight')
                exported_files.append(high_file)
                print(f"✅ 高速彎圖表已匯出: {high_file}")
            
            status_msg = f"✅ 已匯出 {len(exported_files)} 個圖表至: {output_dir}"
            self.status_label.setText(status_msg)
            print(f"\n{status_msg}")
            
            QMessageBox.information(
                self, 
                "匯出成功", 
                f"已成功匯出 {len(exported_files)} 個圖表至:\n{output_dir}"
            )
            
        except Exception as e:
            error_msg = f"❌ 匯出失敗: {e}"
            self.status_label.setText(error_msg)
            print(error_msg)
            QMessageBox.critical(self, "錯誤", f"匯出失敗:\n{str(e)}")
    
    def tile_windows(self):
        """平鋪視窗"""
        self.mdi_area.tileSubWindows()
        self.status_label.setText("✅ 視窗已平鋪")
        print("✅ 視窗已平鋪")
    
    def cascade_windows(self):
        """層疊視窗"""
        self.mdi_area.cascadeSubWindows()
        self.status_label.setText("✅ 視窗已層疊")
        print("✅ 視窗已層疊")


def main():
    print("=" * 60)
    print("Demo 4: 完整功能測試 - 三個獨立視窗")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    window = Demo4MainWindow()
    window.show()
    
    print("\n✅ Demo 4 啟動完成")
    print("功能提示：")
    print("1. 三個獨立視窗顯示不同彎道類型（低速/中速/高速）")
    print("2. 點擊「平鋪視窗」自動排列三個視窗")
    print("3. 點擊「刷新所有圖表」更新所有顯示")
    print("4. 點擊「匯出所有圖表」儲存三個 PNG 檔案")
    print("5. 滑鼠移到散點上查看詳細速度數據")
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
