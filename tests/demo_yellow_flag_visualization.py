"""
Yellow Flag 統計數據預覽 - GUI 呈現測試
展示如何在 Track Map 和圖表上視覺化彎道危險度
"""
import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTextEdit, QPushButton, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# 導入我們的 Track Map 和 Elevation Chart
sys.path.insert(0, str(Path(__file__).parent))
from modules.gui.track_map.track_map_widget import TrackMapWidget
from modules.gui.track_elevation.elevation_chart_widget_pyqt5 import ElevationChartWidget

class YellowFlagVisualizationDemo(QMainWindow):
    """Yellow Flag 統計視覺化 Demo"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yellow Flag 統計視覺化 - 鈴鹿賽道")
        self.setGeometry(100, 100, 1600, 900)
        
        # 載入數據
        self.yellow_flag_data = self._load_yellow_flag_data()
        
        # 設置 UI
        self._setup_ui()
        
        # 載入賽道數據並視覺化
        self._load_track_data()
    
    def _load_yellow_flag_data(self):
        """載入 Yellow Flag 統計數據"""
        json_file = Path('json/yellow_flag_statistics_japan_suzuka.json')
        
        if not json_file.exists():
            print(f"❌ 找不到數據檔案: {json_file}")
            return None
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 載入 Yellow Flag 數據:")
        print(f"   - 分析年份: {len(data['yearly_data'])} 年")
        print(f"   - 總事件數: {data['summary']['total_yellow_flags']}")
        print(f"   - 最危險彎道: T{data['summary']['most_dangerous_corner']}")
        
        return data
    
    def _setup_ui(self):
        """設置使用者介面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 標題
        title_label = QLabel("Yellow Flag 統計視覺化 - 鈴鹿賽道 (2018-2024)")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        main_layout.addWidget(title_label)
        
        # 摘要資訊
        if self.yellow_flag_data:
            summary = self.yellow_flag_data['summary']
            info_text = (
                f"總 Yellow Flag 事件: {summary['total_yellow_flags']} | "
                f"平均每場: {summary['average_yellow_flags_per_race']:.1f} | "
                f"最危險彎道: T{summary['most_dangerous_corner']}"
            )
        else:
            info_text = "無數據"
        
        info_label = QLabel(info_text)
        info_label.setFont(QFont("Arial", 10))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("padding: 5px; background-color: #fff3cd;")
        main_layout.addWidget(info_label)
        
        # 分割器（上下兩部分）
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部：Track Map + Elevation Chart
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        
        # Track Map
        track_map_container = QWidget()
        track_map_layout = QVBoxLayout(track_map_container)
        track_map_label = QLabel("賽道平面圖（彎道危險度熱力圖）")
        track_map_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        track_map_label.setAlignment(Qt.AlignCenter)
        track_map_layout.addWidget(track_map_label)
        
        self.track_map = TrackMapWidget()
        self.track_map.show_official_corners = True
        track_map_layout.addWidget(self.track_map)
        
        top_layout.addWidget(track_map_container)
        
        # Elevation Chart
        elevation_container = QWidget()
        elevation_layout = QVBoxLayout(elevation_container)
        elevation_label = QLabel("高程剖面圖（彎道危險度標示）")
        elevation_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        elevation_label.setAlignment(Qt.AlignCenter)
        elevation_layout.addWidget(elevation_label)
        
        self.elevation_chart = ElevationChartWidget()
        elevation_layout.addWidget(self.elevation_chart)
        
        top_layout.addWidget(elevation_container)
        
        splitter.addWidget(top_widget)
        
        # 下半部：統計資訊
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        stats_label = QLabel("彎道危險度排名與事件詳情")
        stats_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        stats_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(stats_label)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Consolas", 9))
        bottom_layout.addWidget(self.stats_text)
        
        # 按鈕區
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("重新載入數據")
        refresh_btn.clicked.connect(self._load_track_data)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("匯出報告")
        export_btn.clicked.connect(self._export_report)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        bottom_layout.addLayout(button_layout)
        
        splitter.addWidget(bottom_widget)
        
        # 設置分割比例
        splitter.setSizes([600, 300])
        
        main_layout.addWidget(splitter)
    
    def _load_track_data(self):
        """載入賽道數據並應用 Yellow Flag 視覺化"""
        if not self.yellow_flag_data:
            self.stats_text.setPlainText("❌ 無 Yellow Flag 數據")
            return
        
        # 從 demo 載入賽道數據
        from demo_fastf1_z_elevation import FastF1ElevationDemo
        
        # 創建臨時 demo 實例來獲取賽道數據
        print("\n載入鈴鹿賽道數據...")
        temp_demo = FastF1ElevationDemo()
        temp_demo._load_fastf1_data_async()
        
        # 等待數據載入
        import time
        time.sleep(3)
        
        if temp_demo.track_data:
            # 載入到 Track Map
            trackmap_data = temp_demo._convert_to_trackmap_format()
            self.track_map.load_track_data(trackmap_data)
            
            # 載入到 Elevation Chart
            track_outline = temp_demo.track_data.get('track_outline', [])
            corners = temp_demo.track_data.get('official_corners', {}).get('corners', [])
            self.elevation_chart.plot_elevation(track_outline, corners)
            
            # 應用 Yellow Flag 顏色標示
            self._apply_yellow_flag_visualization()
            
            # 顯示統計資訊
            self._display_statistics()
            
            print("✅ 數據載入完成")
        else:
            self.stats_text.setPlainText("❌ 無法載入賽道數據")
    
    def _apply_yellow_flag_visualization(self):
        """在圖表上應用 Yellow Flag 視覺化"""
        # TODO: 實現彎道顏色標示
        # 根據 corner_statistics 中的 total_yellow_flags 數量
        # 將彎道標記為不同顏色（綠色=安全，黃色=中等，紅色=危險）
        pass
    
    def _display_statistics(self):
        """顯示統計資訊"""
        if not self.yellow_flag_data:
            return
        
        stats_text = "=" * 80 + "\n"
        stats_text += "彎道危險度排名（依 Yellow Flag 事件數量）\n"
        stats_text += "=" * 80 + "\n\n"
        
        # 排序彎道
        corner_stats = self.yellow_flag_data['corner_statistics']
        sorted_corners = sorted(corner_stats, key=lambda x: x['total_yellow_flags'], reverse=True)
        
        stats_text += f"{'排名':<6} {'彎道':<8} {'事件數':<10} {'發生年份':<30} {'平均/年':<10}\n"
        stats_text += "-" * 80 + "\n"
        
        for i, corner in enumerate(sorted_corners, 1):
            if corner['total_yellow_flags'] > 0:
                corner_num = corner['corner_number']
                count = corner['total_yellow_flags']
                years = ', '.join(str(y) for y in corner.get('years_with_incidents', []))
                rate = corner.get('incident_rate', 0)
                
                stats_text += f"{i:<6} T{corner_num:<7} {count:<10.1f} {years:<30} {rate:<10.2f}\n"
        
        stats_text += "\n" + "=" * 80 + "\n"
        stats_text += "歷年事件總覽\n"
        stats_text += "=" * 80 + "\n\n"
        
        for year_data in self.yellow_flag_data['yearly_data']:
            year = year_data['year']
            count = year_data['yellow_flag_count']
            stats_text += f"\n{year} 年 - 共 {count} 個 Yellow Flag 事件:\n"
            stats_text += "-" * 80 + "\n"
            
            for i, event in enumerate(year_data['events'], 1):
                corner = event.get('corner', '?')
                sector = event.get('sector', '?')
                message = event.get('message', '')[:60]
                stats_text += f"  {i}. 彎道: T{corner} | Sector: {sector} | {message}\n"
        
        self.stats_text.setPlainText(stats_text)
    
    def _export_report(self):
        """匯出報告"""
        print("匯出報告功能（待實現）")


def main():
    """主程式"""
    print("=" * 70)
    print("Yellow Flag 統計視覺化 Demo")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    demo = YellowFlagVisualizationDemo()
    demo.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
