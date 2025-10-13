#!/usr/bin/env python3
"""
理想圈分段對比 - 三種視覺化版本 DEMO
Ideal Lap Sector Comparison - 3 Visualization Versions

使用真實 JSON 數據展示三種不同的累積差異視覺化方式

作者: F1T Team
日期: 2025-10-10
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QRect, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

# 添加專案根目錄到 sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from modules.gui.themes import color_palette_provider
except ImportError:
    # 如果無法導入，使用簡單的顏色方案
    class SimpleColorProvider:
        def get_driver_color(self, driver, format="qcolor"):
            # 簡單的車手顏色映射
            colors = {
                "VER": QColor(50, 100, 200), "PER": QColor(50, 100, 200),
                "LEC": QColor(220, 20, 60), "SAI": QColor(220, 20, 60),
                "HAM": QColor(0, 210, 190), "RUS": QColor(0, 210, 190),
                "NOR": QColor(255, 135, 0), "PIA": QColor(255, 135, 0),
            }
            return colors.get(driver, QColor(100, 100, 100))
    color_palette_provider = SimpleColorProvider()


class Version1CumulativeWidget(QWidget):
    """版本 1: 累積差異視覺化 - 詳細版"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.data = []
        
    def load_data(self, ranking_data: List[Dict]):
        """載入排名數據"""
        self.data = ranking_data[:10]  # 只顯示前 10 名
        self.update()
        
    def paintEvent(self, event):
        """繪製累積差異視覺化"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.data:
                self._draw_no_data(painter)
                return
            
            # 繪製標題
            painter.setFont(QFont("Microsoft JhengHei", 14, QFont.Bold))
            painter.setPen(QPen(QColor(50, 50, 50)))
            painter.drawText(20, 30, "理想圈分段對比 - 累積差異視覺化")
            
            # 計算繪製區域
            start_y = 60
            row_height = 50
            margin_left = 80
            chart_width = self.width() - margin_left - 40
            
            # 繪製每個車手
            for idx, driver_data in enumerate(self.data):
                y_pos = start_y + idx * row_height
                self._draw_driver_row_v1(painter, driver_data, idx + 1, 
                                         margin_left, y_pos, chart_width, row_height - 5)
                
        finally:
            painter.end()
    
    def _draw_driver_row_v1(self, painter, driver_data, position, x, y, width, height):
        """繪製單個車手的累積差異行"""
        driver = driver_data.get("driver", "???")
        
        # 提取分段時間
        sector_breakdown = driver_data.get("sector_breakdown", {})
        s1_time = sector_breakdown.get("sector_1", {}).get("time", 0)
        s2_time = sector_breakdown.get("sector_2", {}).get("time", 0)
        s3_time = sector_breakdown.get("sector_3", {}).get("time", 0)
        
        # 計算差異（相對於第一名）
        if position == 1:
            self.leader_s1 = s1_time
            self.leader_s2 = s2_time
            self.leader_s3 = s3_time
        
        delta_s1 = s1_time - self.leader_s1
        delta_s2 = s2_time - self.leader_s2
        delta_s3 = s3_time - self.leader_s3
        cumulative = delta_s1 + delta_s2 + delta_s3
        
        # 繪製位置和車手代碼
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.drawText(10, y + 20, f"{position}")
        painter.drawText(35, y + 20, driver)
        
        # 繪製累積差異棒狀圖
        if cumulative > 0:
            # 比例尺: 每 0.1s = 60px
            bar_width = min((cumulative * 600), width - 200)
            
            # 繪製分段棒
            bar_x = x
            
            # S1
            s1_width = (delta_s1 / cumulative * bar_width) if cumulative > 0 else 0
            color_s1 = self._get_delta_color(delta_s1)
            painter.fillRect(QRectF(bar_x, y, s1_width, height), QBrush(color_s1))
            
            # S2
            s2_width = (delta_s2 / cumulative * bar_width) if cumulative > 0 else 0
            color_s2 = self._get_delta_color(delta_s2)
            painter.fillRect(QRectF(bar_x + s1_width, y, s2_width, height), QBrush(color_s2))
            
            # S3
            s3_width = (delta_s3 / cumulative * bar_width) if cumulative > 0 else 0
            color_s3 = self._get_delta_color(delta_s3)
            painter.fillRect(QRectF(bar_x + s1_width + s2_width, y, s3_width, height), 
                            QBrush(color_s3))
            
            # 繪製累積差異文字
            painter.setFont(QFont("Arial", 9))
            painter.setPen(QPen(QColor(200, 50, 50)))
            text_x = bar_x + bar_width + 10
            painter.drawText(int(text_x), y + 20, f"+{cumulative:.3f}s")
        else:
            # 完美圈
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(QPen(QColor(0, 150, 0)))
            painter.drawText(x, y + 20, "✓ 0.000s (完美)")
    
    def _get_delta_color(self, delta):
        """根據差異獲取顏色"""
        if abs(delta) <= 0.010:
            return QColor(80, 200, 120, 200)  # 綠色
        elif abs(delta) <= 0.050:
            return QColor(255, 200, 80, 200)  # 黃色
        else:
            return QColor(255, 100, 100, 200)  # 紅色
    
    def _draw_no_data(self, painter):
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(self.rect().center().x() - 100, 
                        self.rect().center().y(), 
                        "📊 No Data - Please load JSON")


class Version2CompactWidget(QWidget):
    """版本 2: 累積差異條狀圖 (簡潔版)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.data = []
        
    def load_data(self, ranking_data: List[Dict]):
        """載入排名數據"""
        self.data = ranking_data[:10]
        self.update()
        
    def paintEvent(self, event):
        """繪製簡潔版累積差異"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.data:
                self._draw_no_data(painter)
                return
            
            # 繪製標題
            painter.setFont(QFont("Microsoft JhengHei", 14, QFont.Bold))
            painter.setPen(QPen(QColor(50, 50, 50)))
            painter.drawText(20, 30, "理想圈分段對比 - 累積差異條狀圖 (簡潔版)")
            
            # 繪製表頭
            y_header = 60
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(QPen(QColor(80, 80, 80)))
            painter.drawText(10, y_header, "Pos")
            painter.drawText(50, y_header, "Driver")
            painter.drawText(120, y_header, "S1 差異")
            painter.drawText(200, y_header, "S2 差異")
            painter.drawText(280, y_header, "S3 差異")
            painter.drawText(360, y_header, "累積總差異")
            
            # 繪製分隔線
            painter.drawLine(10, y_header + 5, self.width() - 10, y_header + 5)
            
            # 計算繪製區域
            start_y = y_header + 20
            row_height = 45
            
            # 繪製每個車手
            for idx, driver_data in enumerate(self.data):
                y_pos = start_y + idx * row_height
                self._draw_driver_row_v2(painter, driver_data, idx + 1, y_pos, row_height - 5)
                
        finally:
            painter.end()
    
    def _draw_driver_row_v2(self, painter, driver_data, position, y, height):
        """繪製簡潔版車手行"""
        driver = driver_data.get("driver", "???")
        
        # 提取分段時間
        sector_breakdown = driver_data.get("sector_breakdown", {})
        s1_time = sector_breakdown.get("sector_1", {}).get("time", 0)
        s2_time = sector_breakdown.get("sector_2", {}).get("time", 0)
        s3_time = sector_breakdown.get("sector_3", {}).get("time", 0)
        
        # 計算差異
        if position == 1:
            self.leader_s1 = s1_time
            self.leader_s2 = s2_time
            self.leader_s3 = s3_time
        
        delta_s1 = s1_time - self.leader_s1
        delta_s2 = s2_time - self.leader_s2
        delta_s3 = s3_time - self.leader_s3
        cumulative = delta_s1 + delta_s2 + delta_s3
        
        # 繪製位置和車手
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.drawText(15, y + 15, f"{position}")
        painter.drawText(50, y + 15, driver)
        
        # 繪製分段差異標記
        self._draw_delta_indicator(painter, delta_s1, 120, y, 70, 20)
        self._draw_delta_indicator(painter, delta_s2, 200, y, 70, 20)
        self._draw_delta_indicator(painter, delta_s3, 280, y, 70, 20)
        
        # 繪製累積差異棒狀圖
        bar_x = 370
        bar_max_width = self.width() - bar_x - 100
        
        if cumulative > 0:
            # 比例尺: 每 0.025s = 1 格 (20px)
            bar_width = min(cumulative * 800, bar_max_width)
            
            # 繪製棒狀圖
            color = self._get_cumulative_color(cumulative)
            painter.fillRect(QRectF(bar_x, y, bar_width, 20), QBrush(color))
            
            # 繪製數值
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(QPen(QColor(200, 50, 50)))
            painter.drawText(int(bar_x + bar_width + 5), y + 15, f"+{cumulative:.3f}s")
        else:
            # 完美圈
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.setPen(QPen(QColor(0, 150, 0)))
            painter.drawText(bar_x, y + 15, "0.000s ✓")
    
    def _draw_delta_indicator(self, painter, delta, x, y, width, height):
        """繪製差異指示器"""
        # 背景
        bg_color = self._get_delta_color(delta)
        painter.fillRect(QRectF(x, y, width, height), QBrush(bg_color))
        
        # 文字
        painter.setFont(QFont("Arial", 8))
        if abs(delta) < 0.001:
            text = "✓"
            painter.setPen(QPen(QColor(0, 120, 0)))
        else:
            text = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
            painter.setPen(QPen(QColor(50, 50, 50)))
        
        painter.drawText(int(x + 5), y + 14, text)
    
    def _get_delta_color(self, delta):
        """分段差異顏色"""
        if abs(delta) <= 0.010:
            return QColor(200, 255, 200, 150)  # 淺綠
        elif abs(delta) <= 0.050:
            return QColor(255, 240, 200, 150)  # 淺黃
        else:
            return QColor(255, 200, 200, 150)  # 淺紅
    
    def _get_cumulative_color(self, cumulative):
        """累積差異顏色"""
        if cumulative <= 0.050:
            return QColor(100, 200, 100, 200)  # 綠色
        elif cumulative <= 0.200:
            return QColor(255, 200, 100, 200)  # 黃色
        else:
            return QColor(255, 100, 100, 200)  # 紅色
    
    def _draw_no_data(self, painter):
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(self.rect().center().x() - 100, 
                        self.rect().center().y(), 
                        "📊 No Data - Please load JSON")


class Version3DetailedWidget(QWidget):
    """版本 3: 累積差異棒狀圖 - 超詳細版"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(900, 600)
        self.data = []
        
    def load_data(self, ranking_data: List[Dict]):
        """載入排名數據"""
        self.data = ranking_data[:8]  # 只顯示前 8 名 (版本3較詳細)
        self.update()
        
    def paintEvent(self, event):
        """繪製詳細版累積差異棒狀圖"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            if not self.data:
                self._draw_no_data(painter)
                return
            
            # 繪製標題
            painter.setFont(QFont("Microsoft JhengHei", 14, QFont.Bold))
            painter.setPen(QPen(QColor(50, 50, 50)))
            painter.drawText(20, 30, "理想圈分段對比 - 累積差異棒狀圖 (詳細版)")
            
            # 計算繪製區域
            start_y = 60
            row_height = 65
            
            # 繪製每個車手
            for idx, driver_data in enumerate(self.data):
                y_pos = start_y + idx * row_height
                self._draw_driver_row_v3(painter, driver_data, idx + 1, y_pos, row_height - 5)
                
        finally:
            painter.end()
    
    def _draw_driver_row_v3(self, painter, driver_data, position, y, height):
        """繪製詳細版車手行"""
        driver = driver_data.get("driver", "???")
        team = driver_data.get("team", "Unknown")
        
        # 提取分段時間
        sector_breakdown = driver_data.get("sector_breakdown", {})
        s1_time = sector_breakdown.get("sector_1", {}).get("time", 0)
        s2_time = sector_breakdown.get("sector_2", {}).get("time", 0)
        s3_time = sector_breakdown.get("sector_3", {}).get("time", 0)
        s1_optimal = sector_breakdown.get("sector_1", {}).get("is_optimal_in_fastest", False)
        s2_optimal = sector_breakdown.get("sector_2", {}).get("is_optimal_in_fastest", False)
        s3_optimal = sector_breakdown.get("sector_3", {}).get("is_optimal_in_fastest", False)
        
        # 計算差異
        if position == 1:
            self.leader_s1 = s1_time
            self.leader_s2 = s2_time
            self.leader_s3 = s3_time
        
        delta_s1 = s1_time - self.leader_s1
        delta_s2 = s2_time - self.leader_s2
        delta_s3 = s3_time - self.leader_s3
        cumulative = delta_s1 + delta_s2 + delta_s3
        
        # 獲取車手顏色
        driver_color = color_palette_provider.get_driver_color(driver, format="qcolor")
        if not isinstance(driver_color, QColor):
            driver_color = QColor(100, 100, 100)
        
        # 繪製位置和車手資訊
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.drawText(10, y + 18, f"{position}")
        
        painter.setPen(QPen(driver_color))
        painter.drawText(40, y + 18, driver)
        
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.drawText(80, y + 18, team[:20])
        
        # 繪製分段資訊盒
        box_y = y + 25
        box_height = 30
        box_width = 90
        
        # S1 盒
        self._draw_sector_box(painter, "S1", s1_time, delta_s1, s1_optimal, 
                             40, box_y, box_width, box_height)
        
        # S2 盒
        self._draw_sector_box(painter, "S2", s2_time, delta_s2, s2_optimal, 
                             140, box_y, box_width, box_height)
        
        # S3 盒
        self._draw_sector_box(painter, "S3", s3_time, delta_s3, s3_optimal, 
                             240, box_y, box_width, box_height)
        
        # 繪製累積差異
        cumulative_x = 350
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        if cumulative > 0:
            painter.setPen(QPen(QColor(200, 50, 50)))
            painter.drawText(cumulative_x, y + 18, f"累積: +{cumulative:.3f}s")
            
            # 繪製累積棒狀圖
            bar_width = min(cumulative * 500, self.width() - cumulative_x - 20)
            bar_color = self._get_cumulative_color(cumulative)
            painter.fillRect(QRectF(cumulative_x, box_y, bar_width, box_height), 
                            QBrush(bar_color))
        else:
            painter.setPen(QPen(QColor(0, 150, 0)))
            painter.drawText(cumulative_x, y + 18, "累積: 0.000s ✓ 完美")
    
    def _draw_sector_box(self, painter, label, time, delta, is_optimal, x, y, width, height):
        """繪製分段資訊盒"""
        # 背景顏色
        bg_color = self._get_delta_color(delta)
        painter.fillRect(QRectF(x, y, width, height), QBrush(bg_color))
        
        # 邊框
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawRect(QRectF(x, y, width, height))
        
        # 標籤
        painter.setFont(QFont("Arial", 7, QFont.Bold))
        painter.setPen(QPen(QColor(80, 80, 80)))
        painter.drawText(int(x + 3), y + 10, label)
        
        # 時間
        painter.setFont(QFont("Arial", 8))
        painter.drawText(int(x + 3), y + 20, f"{time:.3f}s")
        
        # 差異
        painter.setFont(QFont("Arial", 7))
        if abs(delta) < 0.001:
            painter.setPen(QPen(QColor(0, 120, 0)))
            delta_text = "✓"
        else:
            painter.setPen(QPen(QColor(150, 50, 50)))
            delta_text = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
        painter.drawText(int(x + 3), y + 28, delta_text)
        
        # 最佳標記
        if is_optimal:
            painter.setPen(QPen(QColor(0, 150, 0)))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(int(x + width - 15), y + 10, "✓")
    
    def _get_delta_color(self, delta):
        """分段差異顏色"""
        if abs(delta) <= 0.010:
            return QColor(220, 255, 220, 180)  # 淺綠
        elif abs(delta) <= 0.050:
            return QColor(255, 245, 220, 180)  # 淺黃
        else:
            return QColor(255, 220, 220, 180)  # 淺紅
    
    def _get_cumulative_color(self, cumulative):
        """累積差異顏色"""
        if cumulative <= 0.050:
            return QColor(100, 200, 100, 200)
        elif cumulative <= 0.200:
            return QColor(255, 200, 100, 200)
        else:
            return QColor(255, 100, 100, 200)
    
    def _draw_no_data(self, painter):
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(self.rect().center().x() - 100, 
                        self.rect().center().y(), 
                        "📊 No Data - Please load JSON")


class ThreeVersionsDemoWindow(QMainWindow):
    """三種版本對比視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("理想圈分段對比 - 三種累積差異視覺化 DEMO")
        self.setGeometry(100, 100, 1000, 700)
        
        # 主 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主佈局
        main_layout = QVBoxLayout(main_widget)
        
        # 控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        
        # 版本 1
        self.version1_widget = Version1CumulativeWidget()
        self.tab_widget.addTab(self.version1_widget, "版本 1: 累積差異視覺化")
        
        # 版本 2
        self.version2_widget = Version2CompactWidget()
        self.tab_widget.addTab(self.version2_widget, "版本 2: 簡潔條狀圖")
        
        # 版本 3
        self.version3_widget = Version3DetailedWidget()
        self.tab_widget.addTab(self.version3_widget, "版本 3: 詳細棒狀圖")
        
        main_layout.addWidget(self.tab_widget)
        
        # 狀態標籤
        self.status_label = QLabel("📊 準備就緒 - 請載入數據")
        main_layout.addWidget(self.status_label)
        
        # 自動載入真實 JSON
        self._auto_load_real_json()
    
    def _create_control_panel(self):
        """創建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # 標題
        title_label = QLabel("🏎️ 理想圈分段對比 - 三種視覺化 DEMO")
        title_label.setFont(QFont("Microsoft JhengHei", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 載入按鈕
        load_btn = QPushButton("🔄 重新載入 JSON")
        load_btn.clicked.connect(self._auto_load_real_json)
        layout.addWidget(load_btn)
        
        return panel
    
    def _auto_load_real_json(self):
        """自動載入真實 JSON 數據"""
        try:
            json_path = Path(__file__).parent / "json" / "ideal_lap_ranking_2025_Japan_R.json"
            
            if not json_path.exists():
                QMessageBox.warning(self, "錯誤", f"找不到 JSON 檔案:\n{json_path}")
                return
            
            print(f"[DEMO] 載入真實 JSON: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取排名數據
            ranking_data = data.get("analysis_result", {}).get("ranking", [])
            
            if not ranking_data:
                QMessageBox.warning(self, "錯誤", "JSON 中沒有 ranking 數據")
                return
            
            # 載入到三個版本
            self.version1_widget.load_data(ranking_data)
            self.version2_widget.load_data(ranking_data)
            self.version3_widget.load_data(ranking_data)
            
            # 更新狀態
            year = data.get("metadata", {}).get("year", "2025")
            race = data.get("metadata", {}).get("race", "Japan")
            session = data.get("metadata", {}).get("session", "R")
            driver_count = len(ranking_data)
            
            self.status_label.setText(
                f"✅ 已載入真實數據: {year} {race} {session} - {driver_count} 位車手"
            )
            
            print(f"[DEMO] ✅ 數據載入成功: {driver_count} 位車手")
            
        except Exception as e:
            error_msg = f"載入 JSON 失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "錯誤", error_msg)


def main():
    app = QApplication(sys.argv)
    window = ThreeVersionsDemoWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
