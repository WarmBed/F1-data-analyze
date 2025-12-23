#!/usr/bin/env python3
"""
排位賽預測 GUI Demo - V5 棒狀圖版
Qualifying Prediction Demo - Bar Chart Version

棒狀圖版本，使用自定義 Delegate 繪製預測時間和信賴度
7 欄：排名、車手、車隊、預測時間（棒狀圖）、FP3 對比（棒狀圖）、信賴度（進度條）、△ FP3

Author: F1T Team
Date: 2025-11-05
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox,
    QPushButton, QGroupBox, QAbstractItemView, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen


class TimeBarDelegate(QStyledItemDelegate):
    """預測時間棒狀圖委託"""
    
    def __init__(self, min_time: float = 64.0, max_time: float = 66.0, parent=None):
        super().__init__(parent)
        self.min_time = min_time
        self.max_time = max_time
        self.time_range = max_time - min_time
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        time_value = index.data(Qt.UserRole)
        
        if time_value is None:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 背景
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QBrush(QColor(35, 35, 35)))
        
        # 計算棒狀圖
        base_x = option.rect.x() + 5
        base_y = option.rect.y() + 8
        max_bar_width = option.rect.width() - 80
        bar_height = 18
        
        # 相對比例
        if self.time_range > 0:
            ratio = (time_value - self.min_time) / self.time_range
        else:
            ratio = 0.5
        
        bar_width = max_bar_width * ratio
        
        # 繪製棒狀圖
        bar_rect = QRectF(base_x, base_y, bar_width, bar_height)
        
        # 漸變顏色（快→慢 = 綠→紅）
        if ratio < 0.33:
            color = QColor(0, 200, 0)
        elif ratio < 0.67:
            color = QColor(255, 200, 0)
        else:
            color = QColor(255, 100, 0)
        
        painter.fillRect(bar_rect, QBrush(color))
        painter.setPen(QPen(color.darker(130), 1))
        painter.drawRect(bar_rect)
        
        # 繪製時間文字
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.setPen(QPen(QColor(255, 255, 255)))
        time_text = self._format_time(time_value)
        text_x = int(base_x + max_bar_width + 5)
        text_y = int(base_y + bar_height / 2 + 5)
        painter.drawText(text_x, text_y, time_text)
        
        painter.restore()
    
    def _format_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"


class ComparisonBarDelegate(QStyledItemDelegate):
    """FP3 對比棒狀圖委託（雙棒並排）"""
    
    def __init__(self, min_time: float = 64.0, max_time: float = 66.0, parent=None):
        super().__init__(parent)
        self.min_time = min_time
        self.max_time = max_time
        self.time_range = max_time - min_time
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        fp3_time = index.data(Qt.UserRole)
        pred_time = index.data(Qt.UserRole + 1)
        
        if fp3_time is None or pred_time is None:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 背景
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QBrush(QColor(35, 35, 35)))
        
        base_x = option.rect.x() + 5
        base_y = option.rect.y() + 4
        max_bar_width = option.rect.width() - 10
        bar_height = 10
        
        # FP3 棒（上方）
        if self.time_range > 0:
            fp3_ratio = (fp3_time - self.min_time) / self.time_range
        else:
            fp3_ratio = 0.5
        fp3_bar_width = max_bar_width * fp3_ratio
        fp3_rect = QRectF(base_x, base_y, fp3_bar_width, bar_height)
        painter.fillRect(fp3_rect, QBrush(QColor(150, 150, 200)))  # 紫色
        
        # 預測棒（下方）
        if self.time_range > 0:
            pred_ratio = (pred_time - self.min_time) / self.time_range
        else:
            pred_ratio = 0.5
        pred_bar_width = max_bar_width * pred_ratio
        pred_rect = QRectF(base_x, base_y + bar_height + 2, pred_bar_width, bar_height)
        painter.fillRect(pred_rect, QBrush(QColor(100, 255, 100)))  # 綠色
        
        # 標籤
        painter.setFont(QFont("Arial", 7))
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(int(base_x), int(base_y + bar_height - 1), "FP3")
        painter.drawText(int(base_x), int(base_y + 2 * bar_height + 1), "預測")
        
        painter.restore()


class QualifyingPredictionBarChartDemo(QMainWindow):
    """排位賽預測棒狀圖 Demo"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("排位賽預測 - 棒狀圖版")
        self.setGeometry(100, 100, 1200, 700)
        
        self.mock_data = self._generate_mock_data()
        self._init_ui()
        self._populate_table()
    
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 表格
        self.table = self._create_table()
        main_layout.addWidget(self.table)
        
        # 狀態欄
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        main_layout.addWidget(self.status_label)
    
    def _create_control_panel(self) -> QGroupBox:
        group_box = QGroupBox("預測參數（視覺化版本）")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems(["Austria", "Monza", "Silverstone"])
        layout.addWidget(self.race_combo)
        
        layout.addStretch()
        
        self.predict_button = QPushButton("🎨 執行視覺化預測")
        self.predict_button.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {background-color: #8e24aa;}
        """)
        layout.addWidget(self.predict_button)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        
        # 7 欄
        columns = ["排名", "車手", "車隊", "預測時間", "FP3 對比", "信賴度", "△ FP3"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # 欄位寬度
        table.setColumnWidth(0, 50)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 140)
        table.setColumnWidth(3, 200)  # 棒狀圖
        table.setColumnWidth(4, 150)  # 對比棒
        table.setColumnWidth(5, 80)
        table.setColumnWidth(6, 80)
        
        # 設置委託
        self.time_delegate = TimeBarDelegate(min_time=64.5, max_time=65.5)
        self.comparison_delegate = ComparisonBarDelegate(min_time=64.5, max_time=65.5)
        table.setItemDelegateForColumn(3, self.time_delegate)
        table.setItemDelegateForColumn(4, self.comparison_delegate)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStretchLastSection(True)
        
        return table
    
    def _populate_table(self):
        predictions = self.mock_data["predictions"]
        self.table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            self.table.setRowHeight(row, 35)
            
            # 排名
            rank_item = QTableWidgetItem(str(pred["rank"]))
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFont(QFont("Arial", 11, QFont.Bold))
            self.table.setItem(row, 0, rank_item)
            
            # 車手
            driver_item = QTableWidgetItem(pred["driver"])
            driver_item.setTextAlignment(Qt.AlignCenter)
            driver_item.setFont(QFont("Consolas", 11, QFont.Bold))
            self.table.setItem(row, 1, driver_item)
            
            # 車隊
            team_item = QTableWidgetItem(pred["team"])
            team_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            team_item.setBackground(self._get_team_color(pred["team"]))
            self.table.setItem(row, 2, team_item)
            
            # 預測時間（使用委託）
            time_item = QTableWidgetItem("")
            time_item.setData(Qt.UserRole, pred["predicted_time"])
            self.table.setItem(row, 3, time_item)
            
            # FP3 對比（使用委託）
            comparison_item = QTableWidgetItem("")
            comparison_item.setData(Qt.UserRole, pred["fp3_time"])
            comparison_item.setData(Qt.UserRole + 1, pred["predicted_time"])
            self.table.setItem(row, 4, comparison_item)
            
            # 信賴度
            conf_item = QTableWidgetItem(f"{int(pred['confidence']*100)}%")
            conf_item.setTextAlignment(Qt.AlignCenter)
            conf_item.setFont(QFont("Arial", 10))
            self.table.setItem(row, 5, conf_item)
            
            # △ FP3
            delta_item = QTableWidgetItem(f"{pred['improvement']:+.3f}s")
            delta_item.setTextAlignment(Qt.AlignCenter)
            delta_item.setFont(QFont("Consolas", 9))
            self.table.setItem(row, 6, delta_item)
        
        # 更新狀態
        self.status_label.setText("📊 模型: v3.8 | 賽道: Austria 2025 | 視覺化模式: 棒狀圖")
    
    def _get_team_color(self, team: str) -> QColor:
        team_colors = {
            "Red Bull Racing": QColor(30, 65, 255),
            "Ferrari": QColor(220, 0, 0),
            "Mercedes": QColor(0, 210, 190),
            "McLaren": QColor(255, 135, 0),
        }
        return team_colors.get(team, QColor(100, 100, 100))
    
    def _generate_mock_data(self) -> dict:
        return {
            "metadata": {"model_version": "v3.8", "track": "Austria"},
            "predictions": [
                {"rank": 1, "driver": "VER", "team": "Red Bull Racing", "predicted_time": 64.523, "fp3_time": 64.643, "improvement": -0.120, "confidence": 0.98},
                {"rank": 2, "driver": "LEC", "team": "Ferrari", "predicted_time": 64.689, "fp3_time": 64.869, "improvement": -0.180, "confidence": 0.95},
                {"rank": 3, "driver": "NOR", "team": "McLaren", "predicted_time": 64.712, "fp3_time": 64.862, "improvement": -0.150, "confidence": 0.92},
                {"rank": 4, "driver": "SAI", "team": "Ferrari", "predicted_time": 64.801, "fp3_time": 65.011, "improvement": -0.210, "confidence": 0.91},
                {"rank": 5, "driver": "HAM", "team": "Mercedes", "predicted_time": 64.923, "fp3_time": 65.063, "improvement": -0.140, "confidence": 0.85},
                {"rank": 6, "driver": "RUS", "team": "Mercedes", "predicted_time": 64.991, "fp3_time": 65.181, "improvement": -0.190, "confidence": 0.84},
            ]
        }


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    app.setPalette(palette)
    
    window = QualifyingPredictionBarChartDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
